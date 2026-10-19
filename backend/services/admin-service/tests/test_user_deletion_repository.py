"""Deletion regressions confined to the authorized Local tenant and rolled back.

Firebase callbacks are controlled substitutes; these are PostgreSQL repository
tests, not an assertion that Firebase or the HTTP acceptance suite was exercised.
"""
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from app.repositories import AdminRepository, IdempotencyConflictError
from erclave_common.errors import ErclaveError
from test_organization_commands import TransactionEngine
from test_organization_migration import TENANT, cli


@pytest.fixture
def deletion_store():
    value = os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Local PostgreSQL integration URL not configured")
    engine = create_engine(cli.local_database_url(value, "local", TENANT), poolclass=NullPool)
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                assert connection.execute(
                    text("select id from admin.tenants where id=:tenant"), {"tenant": TENANT}
                ).scalar_one() == TENANT
                yield SimpleNamespace(connection=connection, repository=AdminRepository(TransactionEngine(connection)))
            finally:
                transaction.rollback()
    finally:
        engine.dispose()


def key():
    return f"user-deletion-test-{uuid4().hex}"


def invite(store, email=None, ensure_identity=None):
    return store.repository.invite_user(
        tenant_id=TENANT, email=email or f"deletion-{uuid4().hex}@example.invalid",
        display_name="Synthetic deletion regression", role_ids=[],
        idempotency_key=key(), correlation_id="user-deletion-test", ensure_identity=ensure_identity,
    )


def remove(store, user, command_key=None, actor_email=None):
    return store.repository.delete_user(
        tenant_id=TENANT, user_id=user.id, idempotency_key=command_key or key(),
        correlation_id="user-deletion-test", actor_email=actor_email or user.email,
    )


def membership_count(store, user):
    return store.connection.execute(
        text("select count(*) from admin.memberships where tenant_id=:tenant and user_id=:user"),
        {"tenant": TENANT, "user": user.id},
    ).scalar_one()


def audit_count(store, command_key):
    return store.connection.execute(
        text("select count(*) from admin.audit_events where tenant_id=:tenant and idempotency_key=:key"),
        {"tenant": TENANT, "key": command_key},
    ).scalar_one()


def test_delete_audited_user_retains_global_identity_and_actor_foreign_key(deletion_store):
    store = deletion_store
    user = invite(store)
    prior_key = key()
    store.repository._record_audit_event(
        store.connection, tenant_id=TENANT, action="admin.user.update", resource_type="user",
        resource_id=user.id, before_state=None, after_state={"id": user.id},
        idempotency_key=prior_key, correlation_id="user-deletion-test", metadata={}, actor_user_id=user.id,
    )
    command_key = key()
    assert remove(store, user, command_key).status == "deleted"
    assert membership_count(store, user) == 0
    assert store.connection.execute(text("select status from admin.users where id=:id"), {"id": user.id}).scalar_one() == "disabled"
    assert audit_count(store, prior_key) == 1
    deletion = store.connection.execute(
        text("select actor_user_id,metadata from admin.audit_events where tenant_id=:tenant and idempotency_key=:key"),
        {"tenant": TENANT, "key": command_key},
    ).mappings().one()
    assert deletion["actor_user_id"] == user.id
    assert deletion["metadata"]["retained_for_audit"] is True
    assert deletion["metadata"]["removed_global_user"] is False


def test_delete_replay_is_stable_and_changed_user_or_actor_conflicts(deletion_store):
    store = deletion_store
    user, other = invite(store), invite(store)
    command_key = key()
    first = remove(store, user, command_key)
    assert remove(store, user, command_key) == first
    assert audit_count(store, command_key) == 1
    with pytest.raises(IdempotencyConflictError):
        remove(store, other, command_key, actor_email=user.email)
    with pytest.raises(IdempotencyConflictError):
        remove(store, user, command_key, actor_email=other.email)
    assert membership_count(store, other) == 1
    assert audit_count(store, command_key) == 1


def test_pending_firebase_cleanup_retries_once_without_duplicate_audit(deletion_store):
    store = deletion_store
    user, command_key = invite(store), key()
    remove(store, user, command_key)
    calls = []

    def unavailable(email):
        calls.append(email)
        raise ErclaveError("firebase_identity_unavailable", "Synthetic unavailable provider", status_code=502)

    pending = store.repository.cleanup_user_identity(TENANT, user.id, command_key, unavailable)
    assert pending == {"status": "pending", "error_codes": ["firebase_identity_unavailable"]}
    assert membership_count(store, user) == 0
    assert remove(store, user, command_key).status == "deleted"
    completed = store.repository.cleanup_user_identity(TENANT, user.id, command_key, calls.append)
    assert completed == {"status": "completed", "error_codes": []}
    assert store.repository.cleanup_user_identity(TENANT, user.id, command_key, calls.append) == completed
    assert calls == [user.email, user.email]
    assert audit_count(store, command_key) == 1


@pytest.mark.parametrize("initial_cleanup", [False, True])
def test_reinvitation_and_old_delete_replay_preserve_new_identity(deletion_store, initial_cleanup):
    store = deletion_store
    user, command_key = invite(store), key()
    remove(store, user, command_key)
    removed = []
    if initial_cleanup:
        store.repository.cleanup_user_identity(TENANT, user.id, command_key, removed.append)
    ensured = []

    def ensure_identity():
        # Provisioning runs after the membership exists inside the transaction.
        assert membership_count(store, user) == 1
        ensured.append(user.email)

    reinvited = invite(store, user.email, ensure_identity)
    assert reinvited.id == user.id
    before_replay = list(removed)
    assert remove(store, user, command_key).status == "deleted"
    result = store.repository.cleanup_user_identity(TENANT, user.id, command_key, removed.append)
    assert result == {"status": "not_required", "error_codes": []}
    assert removed == before_replay
    assert ensured == [user.email]
    assert membership_count(store, user) == 1
    assert store.repository.get_user_for_tenant(TENANT, user.id).status == "invited"
    assert audit_count(store, command_key) == 1


def test_failed_identity_provisioning_rolls_back_reinvitation_and_its_audit(deletion_store):
    store = deletion_store
    user = invite(store)
    remove(store, user)
    invitation_key = key()

    def unavailable():
        assert membership_count(store, user) == 1
        assert audit_count(store, invitation_key) == 1
        raise ErclaveError("firebase_identity_unavailable", "Synthetic unavailable provider", status_code=502)

    with pytest.raises(ErclaveError) as raised:
        store.repository.invite_user(
            tenant_id=TENANT, email=user.email, display_name="Rejected reinvitation", role_ids=[],
            idempotency_key=invitation_key, correlation_id="user-deletion-test", ensure_identity=unavailable,
        )
    assert raised.value.code == "firebase_identity_unavailable"
    assert membership_count(store, user) == 0
    assert audit_count(store, invitation_key) == 0
    assert store.connection.execute(text("select status from admin.users where id=:id"), {"id": user.id}).scalar_one() == "disabled"
