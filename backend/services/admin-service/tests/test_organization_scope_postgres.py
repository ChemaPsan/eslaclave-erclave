"""Rollback-only tests confined to the authorized Local tenant."""
import json
from uuid import uuid4
import pytest
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from app.organization_scope import ScopeStore, resolve_scope, scope_migration_plan, migrate_scopes
from app.repositories import IdempotencyConflictError
from test_organization_commands import store, hierarchy, command
from test_organization_migration import TENANT, load, BACKEND


def member(store):
    return store.test_connection.execute(text("select user_id from admin.memberships where tenant_id=:tenant order by id limit 1"), {"tenant": TENANT}).scalar_one()


def legacy(store, user, branch_ids):
    store.test_connection.execute(text("update admin.memberships set metadata=cast(:value as jsonb) where tenant_id=:tenant and user_id=:user"),
        {"value": json.dumps({"preserve": "extension", "scope": {"branch_ids": branch_ids}}), "tenant": TENANT, "user": user})


def test_scope_revision_replay_audit_and_metadata_preservation(store):
    _, society, division = hierarchy(store)
    user = member(store); legacy(store, user, ["*"])
    scopes = ScopeStore(store.repository)
    assert scopes.read(TENANT, user)["division_ids"] == ["*"]
    payload = {"version": 2, "society_ids": [society["id"]], "division_ids": [division["id"]], "expected_revision": 0}
    key = f"scope-{uuid4().hex}"
    saved = scopes.update(TENANT, user, payload, key, "scope-test", None)
    assert saved["revision"] == 1
    assert scopes.update(TENANT, user, payload, key, "scope-test", None) == saved
    with pytest.raises(IdempotencyConflictError):
        scopes.update(TENANT, user, {**payload, "division_ids": []}, key, "scope-test", None)
    with pytest.raises(ErclaveError) as error:
        scopes.update(TENANT, user, payload, f"scope-{uuid4().hex}", "scope-test", None)
    assert error.value.code == "organization_scope_conflict"
    metadata = store.test_connection.execute(text("select metadata from admin.memberships where tenant_id=:tenant and user_id=:user"), {"tenant": TENANT, "user": user}).scalar_one()
    assert metadata["preserve"] == "extension"
    assert resolve_scope(store.test_connection, TENANT, metadata)["division_ids"] == [division["id"]]
    other = command(store, "divisions", {"name": "Future division", "society_id": society["id"]})
    assert other["id"] not in resolve_scope(store.test_connection, TENANT, metadata)["division_ids"]
    assert store.test_connection.execute(text("select count(*) from admin.audit_events where tenant_id=:tenant and idempotency_key=:key"), {"tenant": TENANT, "key": key}).scalar_one() == 1


@pytest.mark.parametrize("case", ["foreign-division", "foreign-society", "inactive", "wrong-parent", "missing-user"])
def test_invalid_scope_never_writes(store, case):
    _, society, division = hierarchy(store)
    user = member(store); legacy(store, user, ["*"])
    scopes = ScopeStore(store.repository)
    payload = {"version": 2, "society_ids": [society["id"]], "division_ids": [division["id"]], "expected_revision": 0}
    if case == "foreign-division": payload["division_ids"] = ["foreign-division"]
    if case == "foreign-society": payload["society_ids"] = ["foreign-society"]
    if case == "inactive": command(store, "divisions", {"status": "inactive"}, division["id"], "deactivate")
    if case == "wrong-parent": payload["society_ids"] = []
    target = "foreign-user" if case == "missing-user" else user
    with pytest.raises(ErclaveError):
        scopes.update(TENANT, target, payload, f"scope-{uuid4().hex}", "scope-test", None)
    assert scopes.read(TENANT, user)["revision"] == 0


def test_reviewed_migration_is_atomic_preserves_and_does_not_repeat(store):
    _, society, division = hierarchy(store)
    user = member(store); legacy(store, user, [division["id"]])
    plan = scope_migration_plan(store.test_connection, TENANT)
    with pytest.raises(ErclaveError):
        migrate_scopes(store.test_connection, store.repository, TENANT, "outdated", "test")
    count = migrate_scopes(store.test_connection, store.repository, TENANT, plan["hash"], "test")
    assert count >= 1
    result = ScopeStore(store.repository).read(TENANT, user)
    assert result["society_ids"] == [society["id"]] and result["division_ids"] == [division["id"]]
    again = scope_migration_plan(store.test_connection, TENANT)
    assert again["changes"] == []
    assert migrate_scopes(store.test_connection, store.repository, TENANT, again["hash"], "test") == 0


def test_new_invitation_starts_with_empty_versioned_scope_and_reinvite_preserves_it(store):
    hierarchy(store)
    email = f"scope-{uuid4().hex}@example.invalid"
    user = store.repository.invite_user(TENANT, email, "Synthetic scope test", [], f"invite-{uuid4().hex}", "scope-test")
    assert ScopeStore(store.repository).read(TENANT, user.id)["division_ids"] == []
    store.repository.invite_user(TENANT, email, "Synthetic scope test", [], f"invite-{uuid4().hex}", "scope-test")
    assert ScopeStore(store.repository).read(TENANT, user.id)["society_ids"] == []


def test_seed_and_onboarding_cannot_reset_existing_scope(store, monkeypatch):
    hierarchy(store)
    seed = load("scope_seed_test", BACKEND / "scripts/seed_admin_qa_demo.py")
    ids = seed.demo_ids(seed.DEFAULT_TENANT_SLUG, seed.DEFAULT_ADMIN_EMAIL)
    assert ids["tenant_id"] == TENANT
    user = ids["user_id"]
    legacy(store, user, ["*"])
    scopes = ScopeStore(store.repository)
    scopes.update(TENANT, user, {"version": 2, "society_ids": [], "division_ids": [], "expected_revision": 0}, f"scope-{uuid4().hex}", "scope-test", None)
    monkeypatch.setattr(seed, "create_engine", lambda *args, **kwargs: store.repository.engine)
    seed.apply_demo_seed("unused", seed.DEFAULT_TENANT_SLUG, seed.DEFAULT_TENANT_NAME, seed.DEFAULT_ADMIN_EMAIL, seed.DEFAULT_ADMIN_NAME)
    assert scopes.read(TENANT, user)["division_ids"] == []
    store.repository.onboard_tenant(slug=seed.DEFAULT_TENANT_SLUG, commercial_name=seed.DEFAULT_TENANT_NAME,
        legal_name=seed.DEFAULT_TENANT_NAME, plan_id=None, timezone="America/Mexico_City", locale="es-MX", source={"type": "test", "id": "scope-test"},
        owner={"email": seed.DEFAULT_ADMIN_EMAIL, "display_name": seed.DEFAULT_ADMIN_NAME, "status": "active", "branch_ids": ["*"]},
        organization_profile=None, modules=[], idempotency_key=f"onboard-{uuid4().hex}", correlation_id="scope-test")
    assert scopes.read(TENANT, user)["division_ids"] == []
