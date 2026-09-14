"""Real Local PostgreSQL migration/value round trips; all writes rolled back."""
import importlib.util
import os
from pathlib import Path
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError


def test_expected_margin_postgres_roundtrip_and_safe_rollback():
    url = os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not url: pytest.skip("ERCLAVE_TEST_DATABASE_URL required")
    parsed = make_url(url)
    assert parsed.host in ("127.0.0.1", "localhost") and parsed.port == 5434 and parsed.database == "erclave_local"
    tenant = "ten_739ee59d765d5e14818674800d"
    migration_path = Path(__file__).resolve().parents[3] / "alembic/versions/20260913_0035_product_expected_margin.py"
    spec = importlib.util.spec_from_file_location("margin_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine(url)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            assert connection.scalar(text("select count(*) from admin.tenants where id=:t"), {"t":tenant}) == 1
            migration.op = Operations(MigrationContext.configure(connection))
            before = connection.execute(text("select id, expected_margin from production.product_services order by id")).all()
            def check_original_rollback():
                fits = all(value is None or (value <= 100 and value == value.quantize(Decimal("0.0001"))) for _, value in before)
                if fits:
                    migration.downgrade()
                    migration.upgrade()
                else:
                    with pytest.raises(DBAPIError, match="cannot fit"), connection.begin_nested():
                        migration.downgrade()
            check_original_rollback()
            assert connection.execute(text("select id, expected_margin from production.product_services order by id")).all() == before
            ids = []
            for kind in ("product", "service"):
                ident = "prs_" + uuid4().hex[:26]
                ids.append(ident)
                connection.execute(text("insert into production.product_services (id,tenant_id,code,name,type,base_unit,status,expected_margin) values (:i,:t,:i,'Margin regression',:kind,'H87','active',400)"), {"i":ident,"t":tenant,"kind":kind})
                for value in (400, 22122.22, 1000000):
                    connection.execute(text("update production.product_services set expected_margin=:v where tenant_id=:t and id=:i"), {"v":value,"t":tenant,"i":ident})
                    actual = connection.scalar(text("select expected_margin from production.product_services where tenant_id=:t and id=:i"), {"t":tenant,"i":ident})
                    assert float(actual) == value
                for value in ("-1", "NaN", "Infinity"):
                    with pytest.raises(DBAPIError), connection.begin_nested():
                        connection.execute(text("update production.product_services set expected_margin=cast(:v as numeric) where tenant_id=:t and id=:i"), {"v":value,"t":tenant,"i":ident})
            with pytest.raises(DBAPIError, match="cannot fit"), connection.begin_nested():
                migration.downgrade()
            for ident in ids:
                connection.execute(text("delete from production.product_services where tenant_id=:t and id=:i"), {"t":tenant,"i":ident})
            check_original_rollback()
            assert connection.execute(text("select id, expected_margin from production.product_services order by id")).all() == before
        finally:
            transaction.rollback()
    engine.dispose()
