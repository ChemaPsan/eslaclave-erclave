from copy import deepcopy
import importlib.util
import os
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.pool import NullPool

from app.models import AuditEvent, Division, FiscalIssuer, OrganizationImport, OrganizationLegacyMapping, Society
from app.organization_migration import (
    OrganizationMigrationError, TABLES, apply_import, build_plan, digest, read_profile,
)

BACKEND = Path(__file__).resolve().parents[3]
TENANT = "ten_739ee59d765d5e14818674800d"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = load("organization_revision", BACKEND / "alembic/versions/20260922_0037_organization_structure.py")
cli = load("organization_backfill_cli", BACKEND / "scripts/organization_backfill_local.py")


def profile():
    return {"corporate": {"commercial_name": "Synthetic corporate", "extension": {"keep": True}},
            "legal_entities": [{"id": "rso_test", "legal_name": "Synthetic issuer", "tax_id": "TEST-ONLY",
                                "status": "active", "contact_email": "synthetic@example.invalid", "custom": "preserve"}],
            "branches": [{"id": "suc_test", "name": "Synthetic division", "code": "DIV-OLD",
                          "status": "inactive", "legal_entity_id": "rso_test", "address": "Synthetic address"}]}


def test_plan_preserves_legacy_codes_inactive_status_contacts_extensions_and_source():
    original = profile()
    before = deepcopy(original)
    plan = build_plan(TENANT, original)
    assert original == before == plan["source_profile"]
    assert plan == build_plan(TENANT, original)
    division = plan["rows"]["divisions"][0]
    assert (division["code"], division["status"]) == ("DIV-OLD", "inactive")
    assert plan["rows"]["societies"][0]["base_currency"] == "MXN"
    assert plan["rows"]["fiscal_issuers"][0]["contact"]["contact_email"] == "synthetic@example.invalid"
    assert plan["rows"]["organization_legacy_mappings"][0]["source_item"]["custom"] == "preserve"
    assert plan["source_hash"] == digest(before)


def test_one_issuer_can_have_multiple_societies_only_through_explicit_resolution():
    source = profile()
    source["legal_entities"].append({**source["legal_entities"][0], "id": "rso_second"})
    with pytest.raises(OrganizationMigrationError, match="shared_tax_identity_requires_resolution"):
        build_plan(TENANT, source)
    plan = build_plan(TENANT, source, {"issuer_aliases": {"rso_second": "rso_test"}})
    assert len(plan["rows"]["fiscal_issuers"]) == 1
    assert len(plan["rows"]["societies"]) == 2
    assert len({item["issuer_id"] for item in plan["rows"]["societies"]}) == 1


def test_orphan_branch_requires_explicit_existing_society_and_changes_plan_hash():
    source = profile()
    source["branches"][0]["legal_entity_id"] = None
    with pytest.raises(OrganizationMigrationError, match="branch_society_requires_resolution"):
        build_plan(TENANT, source)
    resolved = build_plan(TENANT, source, {"branch_societies": {"suc_test": "rso_test"}})
    assert resolved["rows"]["divisions"][0]["society_id"] == resolved["rows"]["societies"][0]["id"]
    assert source["branches"][0]["legal_entity_id"] is None
    good = profile()
    assert build_plan(TENANT, good)["plan_hash"] != build_plan(TENANT, good, {"branch_societies": {"suc_test": "rso_test"}})["plan_hash"]


@pytest.mark.parametrize("field,value", [("id", None), ("id", " bad "), ("status", "deleted"),
                                         ("legal_name", ""), ("tax_id", []), ("tenant_id", "another_tenant")])
def test_invalid_source_is_rejected_before_any_writes(field, value):
    source = profile()
    source["legal_entities"][0][field] = value
    with pytest.raises(OrganizationMigrationError, match="invalid_source"):
        build_plan(TENANT, source)


def test_ids_are_tenant_scoped_and_duplicate_input_is_not_collapsed():
    source = profile()
    assert build_plan(TENANT, source)["rows"]["societies"][0]["id"] != build_plan("other_in_memory", source)["rows"]["societies"][0]["id"]
    source["legal_entities"].append(deepcopy(source["legal_entities"][0]))
    with pytest.raises(OrganizationMigrationError, match="invalid_source"):
        build_plan(TENANT, source)


@pytest.mark.parametrize("change", ["tax", "fiscal", "chain"])
def test_aliases_cannot_hide_incompatible_fiscal_identity_or_cycles(change):
    source = profile()
    source["legal_entities"].append({**source["legal_entities"][0], "id": "second"})
    resolutions = {"issuer_aliases": {"second": "rso_test"}}
    if change == "tax":
        source["legal_entities"][1]["tax_id"] = "DIFFERENT"
    elif change == "fiscal":
        source["legal_entities"][1]["fiscal_regime"] = "different"
    else:
        resolutions["issuer_aliases"]["rso_test"] = "second"
    with pytest.raises(OrganizationMigrationError, match="issuer_alias"):
        build_plan(TENANT, source, resolutions)


def test_missing_fiscal_data_is_preserved_without_inventing_rfc():
    source = profile()
    del source["legal_entities"][0]["tax_id"]
    assert build_plan(TENANT, source)["rows"]["fiscal_issuers"][0]["tax_id"] is None


@pytest.mark.parametrize("url,env,tenant", [
    ("postgresql+psycopg://x@remote:5434/erclave_local", "local", TENANT),
    ("postgresql+psycopg://x@127.0.0.1:5432/erclave_qa", "local", TENANT),
    ("postgresql+psycopg://x@127.0.0.1:5434/erclave_local?host=remote", "local", TENANT),
    ("postgresql+psycopg://x@127.0.0.1:5434/erclave_local", "qa", TENANT),
    ("postgresql+psycopg://x@127.0.0.1:5434/erclave_local", "local", "other"),
])
def test_cli_rejects_wrong_environment_database_or_tenant_without_connecting(url, env, tenant):
    with pytest.raises(OrganizationMigrationError, match="local_database_required"):
        cli.local_database_url(url, env, tenant)


def test_cli_does_not_print_url_or_secret_on_failure(monkeypatch, capsys):
    monkeypatch.setenv("ERCLAVE_DATABASE_URL", "postgresql://user:private-password@remote/db")
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "local")
    assert cli.main(["--tenant-id", TENANT]) == 2
    output = capsys.readouterr().out
    assert "local_database_required" in output and "private-password" not in output and "remote" not in output


def test_preview_exposes_codes_status_currency_and_equivalences_without_personal_data():
    import json
    preview = cli.preview_report(build_plan(TENANT, profile()))
    assert preview["targets"]["divisions"][0]["code"] == "DIV-OLD"
    assert preview["targets"]["divisions"][0]["status"] == "inactive"
    assert preview["targets"]["societies"][0]["base_currency"] == "MXN"
    assert preview["equivalences"][0]["legacy_id"] == "rso_test"
    for private in ("synthetic@example.invalid", "Synthetic address", "TEST-ONLY", "Synthetic issuer"):
        assert private not in json.dumps(preview)


@pytest.fixture
def db():
    value = os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Local PostgreSQL integration URL not configured")
    url = cli.local_database_url(value, "local", TENANT)
    engine = create_engine(url, poolclass=NullPool)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            assert connection.execute(text("select id from admin.tenants where id=:tenant"), {"tenant": TENANT}).scalar() == TENANT
            if not inspect(connection).has_table("societies", schema="admin"):
                with Operations.context(MigrationContext.configure(connection)):
                    revision.upgrade()
            for table in (*TABLES.values(), OrganizationImport.__table__):
                if connection.execute(select(table.c.tenant_id).where(table.c.tenant_id == TENANT).limit(1)).first():
                    pytest.skip("Authorized tenant already has organization data; do not erase it for tests")
            yield connection, engine
        finally:
            transaction.rollback()
    engine.dispose()


def set_source(connection, source):
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy import bindparam
    connection.execute(text("update admin.tenant_settings set value=:value where tenant_id=:tenant and key='organization.profile'")
                       .bindparams(bindparam("value", type_=JSONB)), {"value": source, "tenant": TENANT})


def apply(connection, source, resolutions=None):
    plan = build_plan(TENANT, source, resolutions)
    return apply_import(connection, TENANT, expected_source_hash=plan["source_hash"], expected_plan_hash=plan["plan_hash"],
                        operator="cont01-local-test", correlation_id="cont01-test", resolutions=resolutions)


def test_postgres_import_is_atomic_repeatable_and_preserves_original(db):
    connection, _ = db
    source = profile()
    set_source(connection, source)
    assert apply(connection, source)["status"] == "applied"
    assert apply(connection, source)["status"] == "already_applied"
    assert read_profile(connection, TENANT) == source
    assert connection.execute(select(OrganizationImport.source_profile).where(OrganizationImport.tenant_id == TENANT)).scalar() == source
    assert connection.execute(text("select count(*) from admin.audit_events where tenant_id=:tenant and correlation_id='cont01-test'"), {"tenant": TENANT}).scalar() == 1
    with connection.begin_nested() as savepoint:
        connection.execute(OrganizationImport.__table__.update().where(OrganizationImport.tenant_id == TENANT).values(source_profile={}))
        with pytest.raises(OrganizationMigrationError, match="target_changed"):
            apply(connection, source)
        savepoint.rollback()
    connection.execute(text("update admin.societies set name='Changed' where tenant_id=:tenant"), {"tenant": TENANT})
    with pytest.raises(OrganizationMigrationError, match="target_changed"):
        apply(connection, source)


def test_postgres_refuses_changed_source_and_changed_reviewed_plan(db):
    connection, _ = db
    source = profile()
    set_source(connection, source)
    plan = build_plan(TENANT, source)
    with pytest.raises(OrganizationMigrationError, match="plan_changed"):
        apply_import(connection, TENANT, expected_source_hash=plan["source_hash"], expected_plan_hash="0" * 64,
                     operator="test", correlation_id="test")
    changed = deepcopy(source)
    changed["corporate"]["commercial_name"] = "Changed after review"
    set_source(connection, changed)
    with pytest.raises(OrganizationMigrationError, match="source_changed"):
        apply(connection, source)
    assert not connection.execute(select(Society.id).where(Society.tenant_id == TENANT)).all()
    set_source(connection, source)
    apply(connection, source)
    set_source(connection, changed)
    with pytest.raises(OrganizationMigrationError, match="existing_import_changed"):
        apply(connection, changed)


def test_postgres_single_issuer_multiple_societies_and_internal_scope_constraints(db):
    connection, _ = db
    source = profile()
    source["legal_entities"].append({**source["legal_entities"][0], "id": "second"})
    set_source(connection, source)
    apply(connection, source, {"issuer_aliases": {"second": "rso_test"}})
    societies = connection.execute(select(Society.__table__).where(Society.tenant_id == TENANT)).mappings().all()
    assert len(societies) == 2 and len({row["issuer_id"] for row in societies}) == 1
    for statement in (
        Society.__table__.update().where(Society.tenant_id == TENANT).values(issuer_id=None),
        Society.__table__.update().where(Society.tenant_id == TENANT).values(issuer_id="foreign_or_absent"),
        Society.__table__.update().where(Society.tenant_id == TENANT).values(code="DUPLICATE"),
    ):
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(statement)
    # Actual PostgreSQL constraints must carry tenant on every organizational FK.
    for model in (Society, Division, OrganizationLegacyMapping):
        for fk in inspect(connection).get_foreign_keys(model.__tablename__, schema="admin"):
            assert "tenant_id" in fk["constrained_columns"]
            assert fk["referred_schema"] == "admin"
    mapping = connection.execute(select(OrganizationLegacyMapping.__table__).where(
        OrganizationLegacyMapping.tenant_id == TENANT, OrganizationLegacyMapping.collection == "branches"
    )).mappings().one()
    wrong_society = next(row["id"] for row in societies if row["id"] != mapping["society_id"])
    with pytest.raises(IntegrityError), connection.begin_nested():
        connection.execute(OrganizationLegacyMapping.__table__.update().where(
            OrganizationLegacyMapping.tenant_id == TENANT, OrganizationLegacyMapping.collection == "branches"
        ).values(society_id=wrong_society))


def test_postgres_audit_failure_rolls_back_every_imported_row(db):
    connection, _ = db
    source = profile()
    set_source(connection, source)

    class FailingAudit:
        def execute(self, statement, *args, **kwargs):
            if getattr(statement, "table", None) is AuditEvent.__table__:
                raise RuntimeError("synthetic audit failure")
            return connection.execute(statement, *args, **kwargs)

    with pytest.raises(RuntimeError, match="synthetic audit failure"), connection.begin_nested():
        apply(FailingAudit(), source)
    for table in (*TABLES.values(), OrganizationImport.__table__):
        assert not connection.execute(select(table.c.tenant_id).where(table.c.tenant_id == TENANT)).all()


def test_postgres_concurrent_attempts_serialize_on_tenant_lock(db):
    connection, engine = db
    source = profile()
    set_source(connection, source)
    apply(connection, source)
    with engine.connect() as contender:
        assert contender.execute(text("select pg_try_advisory_xact_lock(hashtextextended(:key, 0))"),
                                 {"key": f"admin.organization.import:{TENANT}"}).scalar() is False


def test_postgres_model_migration_alignment_and_empty_downgrade_reupgrade(db):
    connection, _ = db
    models = (FiscalIssuer, Society, Division, OrganizationImport, OrganizationLegacyMapping)
    # Do not remove any other tenant's rows, even inside this rollback-only test.
    for model in models:
        if connection.execute(select(model.__table__.c.tenant_id).limit(1)).first():
            pytest.skip("Organization tables contain data; guarded downgrade must preserve it")
    with Operations.context(MigrationContext.configure(connection)):
        revision.downgrade()
        assert not inspect(connection).has_table("societies", schema="admin")
        revision.upgrade()
    for model in models:
        actual = {col["name"]: col for col in inspect(connection).get_columns(model.__tablename__, schema="admin")}
        assert inspect(connection).get_pk_constraint(model.__tablename__, schema="admin")["constrained_columns"] == list(model.__table__.primary_key.columns.keys())
        # This historical revision predates CONT-02's optional fiscal fields.
        future_columns = {"postal_code", "country_code"} if model is FiscalIssuer else set()
        assert set(actual) == set(model.__table__.c.keys()) - future_columns
        for col in model.__table__.c:
            if col.name in future_columns:
                continue
            assert actual[col.name]["nullable"] == col.nullable
            assert actual[col.name]["type"].compile(dialect=connection.dialect) == col.type.compile(dialect=connection.dialect)


def test_postgres_downgrade_refuses_populated_tables(db):
    connection, _ = db
    source = profile()
    set_source(connection, source)
    apply(connection, source)
    with pytest.raises(DBAPIError, match="Organization data exists"), connection.begin_nested():
        with Operations.context(MigrationContext.configure(connection)):
            revision.downgrade()
    assert connection.execute(select(Society.id).where(Society.tenant_id == TENANT)).first()


def test_postgres_empty_profile_creates_no_import_marker(db):
    connection, _ = db
    source = {"corporate": {}, "legal_entities": [], "branches": []}
    set_source(connection, source)
    assert apply(connection, source)["status"] == "empty"
    assert not connection.execute(select(OrganizationImport.id).where(OrganizationImport.tenant_id == TENANT)).all()


def test_postgres_base_currency_comes_from_active_admin_catalog(db):
    connection, _ = db
    source = profile()
    set_source(connection, source)
    connection.execute(text("update admin.catalog_items set status='inactive' where tenant_id=:tenant and catalog_code='currencies' and code='MXN'"), {"tenant": TENANT})
    with pytest.raises(OrganizationMigrationError, match="base_currency_not_active"):
        apply(connection, source)
    assert not connection.execute(select(OrganizationImport.id).where(OrganizationImport.tenant_id == TENANT)).all()
