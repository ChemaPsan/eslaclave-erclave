from pathlib import Path
import importlib.util

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "configure_qa_tenant.py"


def load_module():
    spec = importlib.util.spec_from_file_location("configure_qa_tenant", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_configuration_refuses_non_qa_environment(monkeypatch):
    module = load_module()
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "local")

    with pytest.raises(RuntimeError, match="ERCLAVE_ENVIRONMENT=qa"):
        module.main()


def test_configuration_requires_explicit_confirmation(monkeypatch):
    module = load_module()
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "qa")
    monkeypatch.delenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION", raising=False)

    with pytest.raises(RuntimeError, match="explicit QA tenant configuration confirmation"):
        module.main()


def test_configuration_reconciles_only_explicit_existing_tenant(monkeypatch, tmp_path):
    module = load_module()
    contracts = tmp_path / "contracts" / "api"
    contracts.mkdir(parents=True)
    calls = []

    monkeypatch.setattr(module, "CONTRACTS_DIR", contracts)
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "qa")
    monkeypatch.setenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION", "CONFIGURE_ERCLAVE_QA")
    monkeypatch.setenv("ERCLAVE_DATABASE_URL", "postgresql://configured-by-secret-manager")
    monkeypatch.setenv("ERCLAVE_QA_CONFIGURATION_TENANT_ID", "ten_authorized")
    monkeypatch.setattr(module, "extract_permission_seeds", lambda path: ("catalog",))
    monkeypatch.setattr(module, "reconcile_existing_tenant", lambda *args: calls.append(args) or 2)

    assert module.main() == 0
    assert calls == [("postgresql://configured-by-secret-manager", "ten_authorized", ("catalog",))]


def test_configuration_requires_explicit_tenant(monkeypatch):
    module = load_module()
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "qa")
    monkeypatch.setenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION", "CONFIGURE_ERCLAVE_QA")
    monkeypatch.setenv("ERCLAVE_DATABASE_URL", "postgresql://configured-by-secret-manager")
    monkeypatch.delenv("ERCLAVE_QA_CONFIGURATION_TENANT_ID", raising=False)
    with pytest.raises(RuntimeError, match="explicitly select"):
        module.main()


def test_reconciliation_preserves_existing_tenant_data_in_postgres(monkeypatch):
    """Rollback all effects inside the authorized Local tenant; never connect QA."""
    import os
    from types import SimpleNamespace
    from sqlalchemy import create_engine, text
    from test_organization_commands import TransactionEngine
    from test_organization_migration import TENANT, cli

    value = os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not value:
        pytest.skip("Local PostgreSQL integration URL not configured")
    engine = create_engine(cli.local_database_url(value, "local", TENANT))
    module = load_module()
    contracts = SCRIPT_PATH.parents[2] / "contracts" / "api"
    permissions = module.extract_permission_seeds(contracts)
    assert permissions
    tables = ("tenants", "users", "memberships", "roles", "tenant_settings", "tenant_modules", "membership_roles")
    def snapshot(connection):
        return {table: connection.execute(text(
            f"select coalesce(jsonb_agg(to_jsonb(r) order by r.id), '[]'::jsonb) from admin.{table} r"
        )).scalar_one() for table in tables}
    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                wrapper = TransactionEngine(connection)
                monkeypatch.setattr(module, "create_engine", lambda _: SimpleNamespace(begin=wrapper.begin, dispose=lambda: None))
                before = snapshot(connection)
                # A missing target must fail before catalog/role changes.
                with pytest.raises(RuntimeError, match="already exist"):
                    module.reconcile_existing_tenant(value, "ten_missing_configuration", permissions)
                assert snapshot(connection) == before
                first = module.reconcile_existing_tenant(value, TENANT, permissions)
                second = module.reconcile_existing_tenant(value, TENANT, permissions)
                assert first >= 0 and second == 0
                assert snapshot(connection) == before
                assert connection.execute(text("""
                    select count(*) from admin.permissions p where p.code like 'costing.cost_center.%'
                    and p.module_code='admin' and p.status='active'
                """)).scalar_one() == 4
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
