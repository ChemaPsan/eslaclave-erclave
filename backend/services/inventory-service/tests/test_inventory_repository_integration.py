import importlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool


DATABASE_URL = os.getenv("ERCLAVE_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="ERCLAVE_TEST_DATABASE_URL is required for PostgreSQL integration",
)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        del sys.modules[module_name]
repositories = importlib.import_module("app.repositories")
schemas = importlib.import_module("app.schemas")


@pytest.fixture
def stocked_resource():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
    repository = repositories.InventoryRepository(engine)
    tenant = os.getenv("ERCLAVE_TEST_TENANT_ID", "ten_739ee59d765d5e14818674800d")
    suffix = uuid4().hex[:12]
    actor = f"usr_it_{suffix}"
    key_prefix = f"it-{suffix}"
    warehouse = repository.create_warehouse(
        tenant,
        schemas.WarehouseCreate(
            code=f"IT-WH-{suffix}",
            name="Almacen integracion concurrente",
            type="rawMaterials",
            business_center="Local",
            location="Local",
            owner="Integration test",
        ),
        f"{key_prefix}-warehouse",
        "warehouse",
        actor,
    )
    item = repository.create_item(
        tenant,
        schemas.ItemCreate(
            code=f"IT-ITEM-{suffix}",
            name="Articulo integracion concurrente",
            type="rawMaterial",
            category="integration-test",
            base_unit="PZA",
            suggested_warehouse_id=warehouse.id,
            minimum_stock=0,
            default_unit_cost=10,
            use_in_recipe=True,
        ),
        f"{key_prefix}-item",
        "item",
        actor,
    )
    repository.create_movement(
        tenant,
        schemas.MovementCreate(
            movement_type="entry",
            inventory_item_id=item.id,
            warehouse_id=warehouse.id,
            quantity=10,
            unit="PZA",
            unit_cost=10,
            reason="Existencia de prueba concurrente",
            source=schemas.SourceRef(type="integration_test", id=suffix),
            occurred_at=datetime.now(timezone.utc),
        ),
        f"{key_prefix}-entry",
        "entry",
        actor,
    )
    try:
        yield repository, tenant, item, warehouse, suffix, actor, key_prefix
    finally:
        with engine.begin() as connection:
            connection.execute(
                text("delete from inventory.reservations where tenant_id=:tenant and inventory_item_id=:item"),
                {"tenant": tenant, "item": item.id},
            )
            connection.execute(
                text("delete from inventory.movements where tenant_id=:tenant and inventory_item_id=:item"),
                {"tenant": tenant, "item": item.id},
            )
            connection.execute(
                text("delete from inventory.audit_events where tenant_id=:tenant and actor_id=:actor"),
                {"tenant": tenant, "actor": actor},
            )
            connection.execute(
                text("delete from inventory.idempotency_records where tenant_id=:tenant and idempotency_key like :pattern"),
                {"tenant": tenant, "pattern": f"{key_prefix}%"},
            )
            connection.execute(
                text("delete from inventory.items where tenant_id=:tenant and id=:item"),
                {"tenant": tenant, "item": item.id},
            )
            connection.execute(
                text("delete from inventory.warehouses where tenant_id=:tenant and id=:warehouse"),
                {"tenant": tenant, "warehouse": warehouse.id},
            )
        engine.dispose()


def test_concurrent_reservations_never_oversell_stock(stocked_resource):
    _, tenant, item, warehouse, suffix, actor, key_prefix = stocked_resource
    barrier = Barrier(2)

    def reserve(index):
        competing = repositories.InventoryRepository(create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool))
        payload = schemas.ReservationCreateRequest(
            inventory_item_id=item.id,
            warehouse_id=warehouse.id,
            quantity=6,
            unit="PZA",
            source=schemas.SourceRef(
                type="sales_order",
                id=f"ord_it_{suffix}_{index}",
                line_id=f"line_it_{suffix}_{index}",
            ),
        )
        barrier.wait()
        try:
            return competing.create_reservation(
                tenant,
                payload,
                f"{key_prefix}-reserve-{index}",
                f"reserve-{index}",
                actor,
            )
        except ValueError as error:
            return str(error)
        finally:
            competing.engine.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, (1, 2)))

    assert sum(hasattr(result, "id") for result in results) == 1
    assert results.count("insufficient_available_stock") == 1
    with stocked_resource[0].engine.connect() as connection:
        reserved = connection.execute(
            text("select coalesce(sum(quantity),0) from inventory.reservations where tenant_id=:tenant and inventory_item_id=:item and status='active'"),
            {"tenant": tenant, "item": item.id},
        ).scalar_one()
    assert float(reserved) == 6


def test_concurrent_recovery_consumes_a_reservation_only_once(stocked_resource):
    repository, tenant, item, warehouse, suffix, actor, key_prefix = stocked_resource
    reservation = repository.create_reservation(
        tenant,
        schemas.ReservationCreateRequest(
            inventory_item_id=item.id,
            warehouse_id=warehouse.id,
            quantity=4,
            unit="PZA",
            source=schemas.SourceRef(
                type="sales_order",
                id=f"ord_recovery_{suffix}",
                line_id=f"line_recovery_{suffix}",
            ),
        ),
        f"{key_prefix}-reserve-recovery",
        "reserve-recovery",
        actor,
    )
    barrier = Barrier(2)

    def consume(index):
        competing = repositories.InventoryRepository(create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool))
        barrier.wait()
        try:
            return competing.consume_reservation(
                tenant,
                reservation.id,
                "Confirmacion concurrente de entrega",
                f"{key_prefix}-consume-{index}",
                f"consume-{index}",
                actor,
            )
        finally:
            competing.engine.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        movements = list(pool.map(consume, (1, 2)))

    assert movements[0].id == movements[1].id
    with repository.engine.connect() as connection:
        movement_count = connection.execute(
            text("select count(*) from inventory.movements where tenant_id=:tenant and source_type='reservation' and source_id=:reservation"),
            {"tenant": tenant, "reservation": reservation.id},
        ).scalar_one()
        current_status = connection.execute(
            text("select status from inventory.reservations where tenant_id=:tenant and id=:reservation"),
            {"tenant": tenant, "reservation": reservation.id},
        ).scalar_one()
    assert movement_count == 1
    assert current_status == "consumed"
