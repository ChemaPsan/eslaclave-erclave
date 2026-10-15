"""CONT-02 behavior. PostgreSQL writes only the authorized Local tenant and rolls back."""
from contextlib import contextmanager
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4
import os

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError
from app.auth import AuthenticatedActor, get_authenticated_actor
from app.main import app
from app.models import Division, FiscalIssuer, OrganizationAuthority, OrganizationImport, OrganizationLegacyMapping, Society
from app.organization_store import OrganizationStore, activate_organization, authority, structure_hash
from app.organization_schemas import FiscalIssuerCreate, FiscalIssuerUpdate, SocietyCreate, SocietyUpdate, DivisionCreate, DivisionUpdate
from app.repositories import AdminRepository, IdempotencyConflictError, get_admin_repository
from test_organization_migration import TENANT, cli, profile, set_source, apply, build_plan, read_profile, load, BACKEND


class TransactionEngine:
    def __init__(self, connection):
        self.connection = connection

    @contextmanager
    def begin(self):
        with self.connection.begin_nested():
            yield self.connection

    @contextmanager
    def connect(self):
        yield self.connection


@pytest.fixture
def store():
    value = os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Local PostgreSQL integration URL not configured")
    engine = create_engine(cli.local_database_url(value, "local", TENANT), poolclass=NullPool)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            assert connection.execute(text("select id from admin.tenants where id=:tenant"), {"tenant": TENANT}).scalar() == TENANT
            # Isolation is rollback-only. Never delete or seed another tenant, including in tests.
            for model in (OrganizationAuthority, OrganizationLegacyMapping, Division, Society, FiscalIssuer, OrganizationImport):
                connection.execute(model.__table__.delete().where(model.__table__.c.tenant_id == TENANT))
            connection.execute(text("delete from admin.code_sequences where tenant_id=:tenant and document_type in ('admin.fiscal_issuer','admin.society','admin.division')"), {"tenant": TENANT})
            set_source(connection, {"corporate": {"commercial_name": "Synthetic"}, "legal_entities": [], "branches": [], "extension": {"keep": True}})
            result = OrganizationStore(AdminRepository(TransactionEngine(connection)))
            result.test_connection = connection
            result.test_engine = engine
            yield result
        finally:
            transaction.rollback()
    engine.dispose()


def command(store, kind, payload, record_id=None, action=None, key=None):
    return store.command(TENANT, kind, payload, record_id, action or ("update" if record_id else "create"),
                         key or f"test-{uuid4().hex}", "cont02-test", None)


def hierarchy(store):
    issuer = command(store, "fiscal-issuers", {"legal_name": "Synthetic issuer", "tax_id": "SYNTHETIC"})
    society = command(store, "societies", {"name": "Synthetic society", "issuer_id": issuer["id"], "base_currency": "MXN"})
    division = command(store, "divisions", {"name": "Synthetic division", "society_id": society["id"]})
    return issuer, society, division


def test_postgres_hierarchy_projection_search_currency_idempotency_and_audit(store):
    issuer, society, division = hierarchy(store)
    other = command(store, "societies", {"name": "Second society", "issuer_id": issuer["id"], "base_currency": "MXN"})
    assert society["issuer_id"] == other["issuer_id"]
    key = f"test-{uuid4().hex}"
    payload = {"name": "Updated division"}
    first = command(store, "divisions", payload, division["id"], key=key)
    assert first == command(store, "divisions", payload, division["id"], key=key)
    with pytest.raises(IdempotencyConflictError):
        command(store, "divisions", {"name": "Different"}, division["id"], key=key)
    listed = store.list(TENANT, "societies", q="Second", parent_id=issuer["id"], status="active", limit=1)
    assert listed["meta"]["total"] == 1 and listed["data"][0]["id"] == other["id"]
    source = read_profile(store.test_connection, TENANT)
    assert source["extension"] == {"keep": True}
    assert source["branches"][0]["name"] == "Updated division"
    assert source["branches"][0]["legal_entity_id"] == society["id"]
    assert authority(store.test_connection, TENANT)["projection_hash"] == structure_hash(source)
    assert store.test_connection.execute(text("select count(*) from admin.audit_events where tenant_id=:tenant and idempotency_key=:key"), {"tenant": TENANT, "key": key}).scalar() == 1


@pytest.mark.parametrize("case,code,field", [
    ("duplicate-tax", "organization_tax_id_duplicate", "tax_id"),
    ("unknown-parent", "organization_parent_invalid", "issuer_id"),
    ("unknown-currency", "organization_currency_invalid", "base_currency"),
    ("issuer-dependents", "organization_active_dependents", None),
    ("society-dependents", "organization_active_dependents", None),
    ("managed-code", "organization_code_managed", "code"),
    ("long-legacy", "organization_value_invalid", "name"),
])
def test_postgres_rejected_commands_are_atomic_and_have_stable_paths(store, case, code, field):
    issuer, society, division = hierarchy(store)
    before = read_profile(store.test_connection, TENANT)
    with pytest.raises(ErclaveError) as raised:
        if case == "duplicate-tax": command(store, "fiscal-issuers", {"legal_name": "Other", "tax_id": " synthetic "})
        elif case == "unknown-parent": command(store, "societies", {"name": "Other", "issuer_id": "foreign-or-missing", "base_currency": "MXN"})
        elif case == "unknown-currency": command(store, "societies", {"name": "Other", "issuer_id": issuer["id"], "base_currency": "NOT-A-CURRENCY"})
        elif case == "issuer-dependents": command(store, "fiscal-issuers", {"status": "inactive"}, issuer["id"], "deactivate")
        elif case == "society-dependents": command(store, "societies", {"status": "inactive"}, society["id"], "deactivate")
        elif case == "managed-code": command(store, "divisions", {"name": "Other", "society_id": society["id"], "code": "MANUAL"})
        else: command(store, "divisions", {"name": "X" * 241}, division["id"])
    assert raised.value.code == code
    if field: assert raised.value.details["field"] == field
    assert read_profile(store.test_connection, TENANT) == before


def test_postgres_inactive_parents_block_reactivation_and_manual_codes_are_unique(store):
    issuer, society, division = hierarchy(store)
    command(store, "divisions", {"status": "inactive"}, division["id"], "deactivate")
    command(store, "societies", {"status": "inactive"}, society["id"], "deactivate")
    with pytest.raises(ErclaveError) as raised:
        command(store, "divisions", {"status": "active"}, division["id"], "activate")
    assert raised.value.code == "organization_parent_inactive"
    command(store, "societies", {"status": "active"}, society["id"], "activate")
    store.test_connection.execute(text("update admin.code_sequences set mode='manual' where tenant_id=:tenant and document_type='admin.division'"), {"tenant": TENANT})
    assert store.list(TENANT, "divisions")["meta"]["code_mode"] == "manual"
    with pytest.raises(ErclaveError, match="Organization") as raised:
        command(store, "divisions", {"name": "No code", "society_id": society["id"]})
    assert raised.value.code == "manual_business_code_required"
    created = command(store, "divisions", {"name": "Manual", "society_id": society["id"], "code": "man-1"})
    assert created["code"] == "MAN-1"
    with pytest.raises(ErclaveError) as raised:
        command(store, "divisions", {"name": "Duplicate", "society_id": society["id"], "code": "Man-1"})
    assert raised.value.code == "organization_code_duplicate"


def activate(store, source):
    plan = build_plan(TENANT, source)
    result = activate_organization(store.test_connection, TENANT, plan["source_hash"], plan["plan_hash"], "cont02-test", "cont02-test")
    store.project(store.test_connection, TENANT)
    return result, plan


def test_postgres_reconciles_reviewed_shadow_archives_original_and_protects_drift(store):
    source = profile(); set_source(store.test_connection, source); apply(store.test_connection, source)
    changed = deepcopy(source); changed["legal_entities"][0]["legal_name"] = "Corrected name"
    set_source(store.test_connection, changed)
    result, plan = activate(store, changed)
    assert result["reconciled_shadow"] is True
    saved = authority(store.test_connection, TENANT)
    assert saved["prior_shadow"]["batch"]["source_profile"] == source
    assert saved["source_profile"] == changed
    assert activate_organization(store.test_connection, TENANT, plan["source_hash"], plan["plan_hash"], "test", "test")["status"] == "already_active"
    set_source(store.test_connection, source)
    with pytest.raises(ErclaveError) as raised:
        command(store, "fiscal-issuers", {"legal_name": "Should not write"})
    assert raised.value.code == "organization_projection_changed"
    with pytest.raises(ErclaveError) as raised:
        activate_organization(store.test_connection, TENANT, plan["source_hash"], plan["plan_hash"], "test", "test")
    assert raised.value.code == "organization_projection_changed"


def test_postgres_optional_fiscal_extensions_are_promoted_without_changing_old_plan(store):
    source = profile()
    source["legal_entities"][0].update(postal_code="01234", country_code="mx")
    set_source(store.test_connection, source)
    apply(store.test_connection, source)
    activate(store, source)
    issuer = store.list(TENANT, "fiscal-issuers")["data"][0]
    assert issuer["postal_code"] == "01234" and issuer["country_code"] == "MX"
    assert read_profile(store.test_connection, TENANT)["legal_entities"][0]["postal_code"] == "01234"


def test_postgres_corporate_partial_update_preserves_unactivated_source(store):
    source = profile(); set_source(store.test_connection, source)
    store.repository.upsert_setting(TENANT, "organization.profile", "admin", {"corporate": {"commercial_name": "New"}}, "test", "test")
    current = read_profile(store.test_connection, TENANT)
    assert current["legal_entities"] == source["legal_entities"] and current["branches"] == source["branches"]


def test_postgres_legacy_aliases_survive_reparenting_and_shared_fiscal_edits_are_rejected(store):
    source = profile(); set_source(store.test_connection, source); activate(store, source)
    issuer = command(store, "fiscal-issuers", {"legal_name": "New issuer"})
    original = store.list(TENANT, "societies")["data"][0]
    command(store, "societies", {"issuer_id": issuer["id"]}, original["id"])
    other = command(store, "societies", {"issuer_id": issuer["id"], "name": "Another", "base_currency": "MXN"})
    division = store.list(TENANT, "divisions")["data"][0]
    command(store, "divisions", {"society_id": other["id"]}, division["id"])
    projection = read_profile(store.test_connection, TENANT)
    assert next(row for row in projection["legal_entities"] if row["id"] == "rso_test")["issuer_id"] == issuer["id"]
    assert projection["branches"][0]["id"] == "suc_test"
    assert projection["branches"][0]["legal_entity_id"] == other["id"]
    with store.test_connection.begin_nested(), pytest.raises(ErclaveError) as raised:
        store.legacy_command(store.test_connection, TENANT, "legal_entities", {"tax_id": "CHANGED"}, "rso_test", "test-legacy", "test")
    assert raised.value.code == "organization_shared_issuer"
    key = f"test-{uuid4().hex}"
    legacy = store.repository._update_organization_item(TENANT, "branches", "suc_test", {"name": "Legacy edited"}, "update", key, "test")
    assert legacy["name"] == store.get(TENANT, "divisions", division["id"])["name"] == "Legacy edited"
    assert store.repository._update_organization_item(TENANT, "branches", "suc_test", {"name": "Legacy edited"}, "update", key, "test") == legacy
    with pytest.raises(ErclaveError) as raised:
        store.repository._update_organization_item(TENANT, "branches", "suc_test", {"name": "Changed"}, "update", key, "test")
    assert raised.value.code == "idempotency_key_reused"
    with pytest.raises(ErclaveError) as raised:
        store.repository.update_branch(TENANT, "suc_test", {"code": "CHANGED"}, f"test-{uuid4().hex}", "test")
    assert raised.value.code == "organization_code_immutable"


def test_postgres_setting_cannot_bypass_authority_but_corporate_edit_preserves_extensions(store):
    hierarchy(store)
    with pytest.raises(ErclaveError) as raised:
        store.repository.upsert_setting(TENANT, "organization.profile", "admin", {"branches": []}, "test", "test")
    assert raised.value.code == "organization_structure_read_only"
    store.repository.upsert_setting(TENANT, "organization.profile", "admin", {"corporate": {"commercial_name": "Renamed"}}, "test", "test")
    assert read_profile(store.test_connection, TENANT)["extension"] == {"keep": True}
    assert store.list(TENANT, "divisions")["meta"]["total"] == 1
    with pytest.raises(ErclaveError) as raised:
        store.repository.delete_backoffice_tenant(TENANT, "test", "test")
    assert raised.value.code == "organization_tenant_in_use"


def test_postgres_tenant_predicates_and_writer_lock(store):
    issuer, _, _ = hierarchy(store)
    with pytest.raises(ErclaveError) as raised:
        store.get_row(store.test_connection, "other-read-only", "fiscal-issuers", issuer["id"])
    assert raised.value.code == "organization_record_not_found"
    with store.test_engine.connect() as contender:
        assert contender.execute(text("select pg_try_advisory_xact_lock(hashtextextended(:key,0))"), {"key": f"admin.organization.import:{TENANT}"}).scalar() is False


@pytest.mark.parametrize("schema,payload", [
    (FiscalIssuerCreate, {"legal_name": " "}), (FiscalIssuerUpdate, {"code": "CHANGED"}),
    (SocietyCreate, {"name": "Name", "issuer_id": "id", "issuer_ids": ["other"]}),
    (SocietyUpdate, {"issuer_id": None}), (DivisionCreate, {"name": "Name"}),
    (DivisionUpdate, {"society_id": None}),
])
def test_schema_rejects_invalid_identity_or_unrecognized_fields(schema, payload):
    with pytest.raises(ValueError): schema.model_validate(payload)


@pytest.fixture
def api(monkeypatch):
    context = SimpleNamespace(tenant=SimpleNamespace(status="active"), active_modules=["admin"], permissions=[])
    repository = SimpleNamespace(get_session_context_by_email=lambda tenant, email: context if tenant == TENANT else None)
    actor = AuthenticatedActor(uid="synthetic", email="synthetic@example.invalid")
    app.dependency_overrides[get_settings] = lambda: Settings(environment="local", auth_mode="firebase")
    app.dependency_overrides[get_admin_repository] = lambda: repository
    app.dependency_overrides[get_authenticated_actor] = lambda: actor
    client = TestClient(app)
    try: yield client, context
    finally: app.dependency_overrides.clear()


@pytest.mark.parametrize("kind,stem", [("fiscal-issuers", "fiscal_issuer"), ("societies", "society"), ("divisions", "division")])
@pytest.mark.parametrize("method,suffix,action", [("GET", "", "read"), ("GET", "/id", "read"), ("POST", "", "create"), ("PATCH", "/id", "update"), ("POST", "/id/activate", "status"), ("POST", "/id/deactivate", "status")])
def test_every_endpoint_enforces_specific_permission(api, kind, stem, method, suffix, action):
    client, context = api
    context.permissions = ["admin.setting.update", f"admin.{stem}.unrelated"]
    response = client.request(method, f"/v1/organization/{kind}{suffix}", headers={"X-Tenant-Id": TENANT}, json={})
    assert response.status_code == 403
    assert response.json()["error"]["details"]["permissions_any"] == [f"admin.{stem}.{action}"]


def test_api_authentication_missing_tenant_and_schema_validation(api):
    client, context = api
    assert client.get("/v1/organization/societies").status_code == 400
    assert client.get("/v1/organization/societies", headers={"X-Tenant-Id": "other-read-only"}).status_code == 404
    context.permissions = ["admin.society.create"]
    response = client.post("/v1/organization/societies", headers={"X-Tenant-Id": TENANT}, json={"name": "Test"})
    assert response.status_code == 422
    app.dependency_overrides[get_authenticated_actor] = lambda: None
    assert client.get("/v1/organization/societies", headers={"X-Tenant-Id": TENANT}).status_code == 401


def test_postgres_api_real_commands_responses_and_key_requirement(store, api):
    client, context = api
    app.dependency_overrides[get_admin_repository] = lambda: store.repository
    store.repository.get_session_context_by_email = lambda tenant, email: context if tenant == TENANT else None
    context.permissions = [f"admin.{stem}.{action}" for stem in ("fiscal_issuer", "society", "division") for action in ("create", "read", "update", "status")]
    headers = {"X-Tenant-Id": TENANT}
    assert client.post("/v1/organization/fiscal-issuers", headers=headers, json={"legal_name": "API issuer"}).status_code == 400
    headers["Idempotency-Key"] = f"test-{uuid4().hex}"
    created = client.post("/v1/organization/fiscal-issuers", headers=headers, json={"legal_name": "API issuer"})
    assert created.status_code == 201, created.text
    issuer = created.json()["data"]
    society = client.post("/v1/organization/societies", headers=headers, json={"name": "API society", "issuer_id": issuer["id"]})
    assert society.status_code == 201, society.text
    division = client.post("/v1/organization/divisions", headers=headers, json={"name": "API division", "society_id": society.json()["data"]["id"]})
    assert division.status_code == 201, division.text
    assert client.get("/v1/organization/divisions?limit=101", headers=headers).status_code == 422
    assert client.get("/v1/organization/divisions", headers=headers).json()["data"][0] == division.json()["data"]
    assert client.post("/v1/organization/fiscal-issuers", headers=headers, json={"legal_name": "Different"}).status_code == 409


def test_postgres_authority_migration_alignment_and_guarded_downgrade(store):
    from alembic.operations import Operations
    from alembic.migration import MigrationContext
    from sqlalchemy import inspect
    from sqlalchemy.exc import DBAPIError
    revision = load("authority_revision", BACKEND / "alembic/versions/20260925_0038_organization_authority.py")
    connection = store.test_connection
    # Whole-table DDL only when no tenant has active authority or new fiscal data.
    if connection.execute(select(OrganizationAuthority.tenant_id).limit(1)).first():
        pytest.skip("An active organization prevents downgrade")
    if connection.execute(text("select 1 from admin.fiscal_issuers where postal_code is not null or country_code is not null limit 1")).first():
        pytest.skip("Existing fiscal details prevent downgrade")
    with Operations.context(MigrationContext.configure(connection)):
        revision.downgrade()
        assert not inspect(connection).has_table("organization_authorities", schema="admin")
        revision.upgrade()
    for model in (OrganizationAuthority, FiscalIssuer):
        columns = {col["name"]: col for col in inspect(connection).get_columns(model.__tablename__, schema="admin")}
        assert set(columns) == set(model.__table__.c.keys())
        for col in model.__table__.c:
            assert columns[col.name]["nullable"] == col.nullable
            assert columns[col.name]["type"].compile(dialect=connection.dialect) == col.type.compile(dialect=connection.dialect)
    hierarchy(store)
    with pytest.raises(DBAPIError, match="Organization authority"), connection.begin_nested():
        with Operations.context(MigrationContext.configure(connection)):
            revision.downgrade()


def test_postgres_nonempty_source_requires_review_and_edited_shadow_is_never_overwritten(store):
    source = profile(); set_source(store.test_connection, source)
    with pytest.raises(ErclaveError) as raised:
        store.list(TENANT, "societies")
    assert raised.value.code == "organization_review_required"
    with pytest.raises(ErclaveError) as raised:
        command(store, "fiscal-issuers", {"legal_name": "Cannot bypass"})
    assert raised.value.code == "organization_review_required"
    apply(store.test_connection, source)
    store.test_connection.execute(Society.__table__.update().where(Society.tenant_id == TENANT).values(name="Out of band"))
    with pytest.raises(ErclaveError) as raised:
        activate(store, source)
    assert raised.value.code == "organization_shadow_changed"
    assert read_profile(store.test_connection, TENANT) == source
