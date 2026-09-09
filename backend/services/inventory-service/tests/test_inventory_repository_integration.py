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
inventory_api = importlib.import_module("app.api")


@pytest.fixture
def stocked_resource():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
    repository = repositories.InventoryRepository(engine)
    tenant = os.getenv("ERCLAVE_TEST_TENANT_ID", "ten_739ee59d765d5e14818674800d")
    assert tenant == "ten_739ee59d765d5e14818674800d"
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
            connection.execute(text('delete from inventory.reservation_source_rollbacks where tenant_id=:t and actor_id=:a'),{'t':tenant,'a':actor})
            connection.execute(text("delete from inventory.material_returns where tenant_id=:tenant and original_movement_id in (select id from inventory.movements where tenant_id=:tenant and inventory_item_id=:item)"),{"tenant":tenant,"item":item.id})
            connection.execute(text("delete from inventory.transfers where tenant_id=:tenant and outgoing_movement_id in (select id from inventory.movements where tenant_id=:tenant and inventory_item_id=:item)"),{"tenant":tenant,"item":item.id})
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


def test_material_return_records_one_entry_and_retries_owner_reconciliation(stocked_resource):
    repo,t,item,wh,s,actor,key=stocked_resource
    reservation=repo.create_reservation(t,schemas.ReservationCreateRequest(inventory_item_id=item.id,warehouse_id=wh.id,quantity=4,unit='PZA',source=schemas.SourceRef(type='production_order',id='order_'+s,line_id='line_'+s)),key+'-reserve','reserve',actor)
    movement=repo.consume_reservation(t,reservation.id,'Entrega física',key+'-issue','issue',actor,allowed_sources={'production_order'})
    from erclave_common.errors import ErclaveError
    class Owner:
        fail=True
        calls=0
        def validate(self,tenant,source,authorization):
            assert tenant==t and source['source_id']=='order_'+s
            return {'source_code':'OP-'+s}
        def reconcile(self,tenant,source,authorization):
            self.calls+=1
            if self.fail:raise ErclaveError('resource_authority_unavailable','Retry',503)
            return {'id':source['id'],'status':'completed'}
    owner=Owner();access=inventory_api.AuthorizedContext(t,actor,'inventory.movement.create',frozenset({'inventory.movement.create'}))
    payload=schemas.MaterialReturnRequest(original_movement_id=movement.id,quantity=2,reason='Sobrante no utilizado')
    request=inventory_api.request_material_return(payload,t,None,key+'-request',repo,owner,access).data
    assert request.status=='pending'
    with repo.engine.connect() as c:assert repo._balance(c,t,item.id,wh.id,'PZA')==6
    with pytest.raises(ValueError,match='linked_movement_requires_return'):repo.reverse_movement(t,movement.id,'No revertir orden',key+'-reverse','reverse',actor)
    first=inventory_api.receive_material_return(request.id,t,None,key+'-receive',repo,owner,access).data
    assert first.status=='received_pending_reconciliation'
    assert repo.get_material_return('other-tenant',request.id) is None
    owner.fail=False
    second=inventory_api.receive_material_return(request.id,t,None,key+'-retry',repo,owner,access).data
    assert second.status=='completed' and second.movement_id==first.movement_id
    inventory_api.receive_material_return(request.id,t,None,key+'-again',repo,owner,access)
    assert owner.calls==2
    assert inventory_api.request_material_return(payload,t,None,key+'-request',repo,owner,access).data.status=='completed'
    denied=inventory_api.AuthorizedContext(t,actor,'maintenance.material_request.create',frozenset({'maintenance.material_request.create'}))
    with pytest.raises(ErclaveError) as forbidden:inventory_api.request_material_return(payload,t,None,key+'-forbidden',repo,owner,denied)
    assert forbidden.value.code=='permission_denied'
    pending=inventory_api.request_material_return(payload,t,None,key+'-cancel-request',repo,owner,access).data
    assert inventory_api.cancel_material_return(pending.id,schemas.ReverseRequest(reason='Sobrante utilizado'),t,key+'-cancel',repo,access).data.status=='cancelled'
    assert inventory_api.cancel_material_return(pending.id,schemas.ReverseRequest(reason='Sobrante utilizado'),t,key+'-cancel',repo,access).data.status=='cancelled'
    with pytest.raises(ErclaveError) as cancelled:inventory_api.receive_material_return(pending.id,t,None,key+'-cancel-receive',repo,owner,access)
    assert cancelled.value.code=='material_return_not_receivable'
    with repo.engine.connect() as c:assert repo._balance(c,t,item.id,wh.id,'PZA')==8
    with pytest.raises(ValueError,match='material_return_quantity_exceeded'):
        repo.request_material_return(t,payload.model_copy(update={'quantity':3}),repo.return_source(t,movement.id),'OP-'+s,key+'-over','over',actor)


def test_creation_rollback_only_releases_unissued_reservations_owned_by_actor(stocked_resource):
    repo,t,item,wh,s,actor,key=stocked_resource
    reservation=repo.create_reservation(t,schemas.ReservationCreateRequest(inventory_item_id=item.id,warehouse_id=wh.id,quantity=3,unit='PZA',source=schemas.SourceRef(type='production_order',id='order_'+s,line_id='line_'+s)),key+'-reserve','reserve',actor)
    with pytest.raises(ValueError,match='permission_denied'):repo.rollback_production_reservations(t,'order_'+s,'other-actor')
    assert repo.rollback_production_reservations(t,'order_'+s,actor)['status']=='released'
    assert repo.rollback_production_reservations(t,'order_'+s,actor)['status']=='released'
    with pytest.raises(ValueError,match='production_creation_attempt_failed'):
        repo.create_reservation(t,schemas.ReservationCreateRequest(inventory_item_id=item.id,warehouse_id=wh.id,quantity=3,unit='PZA',source=schemas.SourceRef(type='production_order',id='order_'+s,line_id='line_'+s)),key+'-late-reserve','late-reserve',actor)
    with repo.engine.connect() as c:
        assert repo._reserved(c,t,item.id,wh.id,'PZA')==0
        assert repo._balance(c,t,item.id,wh.id,'PZA')==10


def test_reversal_cancels_quantity_and_value_once(stocked_resource):
    repo,t,item,wh,s,actor,key=stocked_resource
    original=repo.list_movements(t,item.id)[0]
    reversal=repo.reverse_movement(t,original.id,"Corrección física validada",key+"-reverse","reverse",actor)
    assert repo.reverse_movement(t,original.id,"Corrección física validada",key+"-reverse","reverse",actor).id==reversal.id
    with repo.engine.connect() as c:
        assert repo._balance(c,t,item.id,wh.id,"PZA")==0
        assert c.execute(text("select sum(case when direction='in' then quantity*unit_cost else -quantity*unit_cost end) from inventory.movements where tenant_id=:t and inventory_item_id=:i"),{"t":t,"i":item.id}).scalar_one()==0
    with pytest.raises(ValueError,match="movement_already_reversed"):
        repo.reverse_movement(t,original.id,"No duplicar la corrección",key+"-duplicate","duplicate",actor)
    with pytest.raises(ValueError,match="reversal_cannot_be_reversed"):
        repo.reverse_movement(t,reversal.id,"No revertir la corrección",key+"-chain","chain",actor)


def test_transfer_requires_destination_receipt_and_origin_confirms_returns(stocked_resource):
    repo,t,item,origin,s,actor,key=stocked_resource
    destination=repo.create_warehouse(t,schemas.WarehouseCreate(code="DEST-"+s,name="Destino sintético",type="rawMaterials",business_center="Local",location="Local",owner="Prueba"),key+"-dest","dest",actor)
    try:
        movement=repo.create_movement(t,schemas.MovementCreate(movement_type="transfer",inventory_item_id=item.id,warehouse_id=origin.id,destination_warehouse_id=destination.id,quantity=6,unit="PZA",reason="Traslado de prueba",source=schemas.SourceRef(type="manual",id=s),occurred_at=datetime.now(timezone.utc)),key+"-transfer","transfer",actor)
        transfer_id=movement.transfer_group_id
        def balances():
            with repo.engine.connect() as c:return repo._balance(c,t,item.id,origin.id,"PZA"),repo._balance(c,t,item.id,destination.id,"PZA")
        assert balances()==(4,0)
        with pytest.raises(ValueError,match="transfer_requires_receipt_or_return"):
            repo.reverse_movement(t,movement.id,"No regresar virtualmente",key+"-reverse","reverse",actor)
        wrong=schemas.TransferActionRequest(warehouse_id=origin.id,quantity=3,reason="Recepción parcial")
        with pytest.raises(ValueError,match="transfer_receiving_warehouse_required"):
            repo.transition_transfer(t,transfer_id,"receive",wrong,key+"-wrong","wrong",actor)
        receipt=wrong.model_copy(update={"warehouse_id":destination.id})
        assert repo.transition_transfer("other-tenant",transfer_id,"receive",receipt,key+"-other","other",actor) is None
        result=repo.transition_transfer(t,transfer_id,"receive",receipt,key+"-receive","receive",actor)
        assert result.status=="partially_received" and balances()==(4,3)
        assert repo.transition_transfer(t,transfer_id,"receive",receipt,key+"-receive","receive",actor).received_quantity==3
        assert balances()==(4,3)
        request=schemas.TransferActionRequest(warehouse_id=destination.id,reason="Saldo rechazado por daño")
        assert repo.transition_transfer(t,transfer_id,"request-return",request,key+"-return","return",actor).status=="return_requested"
        assert balances()==(4,3)
        with pytest.raises(ValueError,match="transfer_return_in_progress"):
            repo.transition_transfer(t,transfer_id,"receive",receipt,key+"-late","late",actor)
        assert repo.transition_transfer(t,transfer_id,"receive-return",wrong,key+"-back","back",actor).status=="returned"
        assert balances()==(7,3)
    finally:
        with repo.engine.begin() as c:
            c.execute(text("delete from inventory.transfers where tenant_id=:t and destination_warehouse_id=:w"),{"t":t,"w":destination.id})
            c.execute(text("delete from inventory.movements where tenant_id=:t and warehouse_id=:w"),{"t":t,"w":destination.id})
            c.execute(text("delete from inventory.warehouses where tenant_id=:t and id=:w"),{"t":t,"w":destination.id})


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


@pytest.mark.parametrize("source_type",["maintenance_order","production_order"])
def test_internal_issue_requires_source_authority_and_full_quantity(stocked_resource,source_type):
    repo,tenant,item,warehouse,suffix,actor,key=stocked_resource
    payload=schemas.ReservationCreateRequest(inventory_item_id=item.id,warehouse_id=warehouse.id,quantity=3,unit="PZA",source=schemas.SourceRef(type=source_type,id="order_"+suffix,line_id="line_"+suffix))
    reservation=repo.create_reservation(tenant,payload,key+"-reserve","reserve",actor)
    with pytest.raises(ValueError,match="permission_denied"):
        repo.consume_reservation(tenant,reservation.id,"Forbidden",key+"-deny","deny",actor,3,allowed_sources={"sales_order"})
    with pytest.raises(ValueError,match="reservation_quantity_exceeded"):
        repo.consume_reservation(tenant,reservation.id,"Partial",key+"-partial","partial",actor,1,allowed_sources={source_type})
    assert reservation.expires_at is None
    first=repo.consume_reservation(tenant,reservation.id,"Warehouse issue",key+"-consume","consume",actor,3,allowed_sources={source_type})
    replay=repo.consume_reservation(tenant,reservation.id,"Warehouse issue",key+"-retry","retry",actor,3,allowed_sources={source_type})
    assert replay.id==first.id
    assert repo.consume_reservation("ten_other",reservation.id,"Foreign",key+"-foreign","foreign",actor,3,allowed_sources={"maintenance_order"}) is None
    with repo.engine.connect() as c:
        exits=c.execute(text("select count(*),sum(quantity) from inventory.movements where tenant_id=:t and source_type='reservation' and source_id=:r"),{"t":tenant,"r":reservation.id}).one()
        assert exits[0]==1 and float(exits[1])==3


def test_maintenance_source_scope_cannot_release_or_consume_production_reservations(stocked_resource):
    repo,tenant,item,warehouse,suffix,actor,key=stocked_resource
    payload=schemas.ReservationCreateRequest(inventory_item_id=item.id,warehouse_id=warehouse.id,quantity=2,unit="PZA",source=schemas.SourceRef(type="production_order",id="pro_"+suffix,line_id="line_"+suffix))
    reservation=repo.create_reservation(tenant,payload,key+"-reserve","reserve",actor)
    with pytest.raises(ValueError,match="permission_denied"):
        repo.release_reservation(tenant,reservation.id,"Forbidden",key+"-release","release",actor,allowed_sources={"maintenance_order"})
    with pytest.raises(ValueError,match="permission_denied"):
        repo.consume_reservation(tenant,reservation.id,"Forbidden",key+"-consume","consume",actor,2,allowed_sources={"maintenance_order"})
