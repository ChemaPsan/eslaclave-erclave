"""PostgreSQL evidence for warehouse-before-start; only own Local fixtures are removed."""
import importlib
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

DATABASE_URL=os.getenv("ERCLAVE_TEST_DATABASE_URL", "")
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason="ERCLAVE_TEST_DATABASE_URL is required")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."):del sys.modules[name]
repos=importlib.import_module("app.repositories")
schemas=importlib.import_module("app.schemas")
api=importlib.import_module("app.api")
from erclave_common.errors import ErclaveError


@pytest.fixture
def material_order():
    engine=create_engine(DATABASE_URL,poolclass=NullPool)
    repo=repos.ProductionRepository(engine)
    tenant=os.getenv("ERCLAVE_TEST_TENANT_ID","ten_739ee59d765d5e14818674800d")
    assert tenant=="ten_739ee59d765d5e14818674800d"
    suffix=uuid4().hex[:12];oid=f"ord_issue_{suffix}";actor=f"usr_issue_{suffix}"
    try:
        with engine.begin() as c:
            recipe=c.execute(text("select v.id version_id,r.id recipe_id,r.product_service_id from production.recipe_versions v join production.recipes r on r.tenant_id=v.tenant_id and r.id=v.recipe_id where r.tenant_id=:t limit 1"),{"t":tenant}).mappings().first()
            assert recipe,"Local demo requires a recipe for read-only fixture references"
            c.execute(text("""insert into production.production_orders(id,tenant_id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,responsible_name_snapshot,planned_cost,recipe_snapshot,resource_validation_snapshot,validated_at,created_by)
                values(:i,:t,:i,:p,:r,:v,1,'H87','released','Responsable sintético',12,'{}','{}',now(),:a)"""),{"i":oid,"t":tenant,"p":recipe["product_service_id"],"r":recipe["recipe_id"],"v":recipe["version_id"],"a":actor})
            for n in range(2):
                c.execute(text("""insert into production.production_order_resources(id,tenant_id,production_order_id,resource_type,resource_ref_id,resource_code,resource_name_snapshot,unit,planned_quantity,unit_cost_snapshot,planned_cost)
                    values(:i,:t,:o,'material',:i,:i,'Material sintético','H87',2,3,6)"""),{"i":f"resource{n}_{suffix}","t":tenant,"o":oid})
                c.execute(text("insert into production.production_order_resource_reservations(id,tenant_id,production_order_resource_id,reservation_ref_id) values(:i,:t,:r,:ref)"),{"i":f"link{n}_{suffix}","t":tenant,"r":f"resource{n}_{suffix}","ref":f"reserve{n}_{suffix}"})
        yield repo,tenant,oid,actor,suffix
    finally:
        with engine.begin() as c:
            c.execute(text("delete from production.material_return_adjustments where tenant_id=:t and order_id=:i"),{"t":tenant,"i":oid})
            c.execute(text("delete from production.failed_order_creations where tenant_id=:t and actor_id=:a"),{"t":tenant,"a":actor})
            c.execute(text("delete from production.material_issues where tenant_id=:t and production_order_id=:i"),{"t":tenant,"i":oid})
            c.execute(text("delete from production.production_orders where tenant_id=:t and id=:i"),{"t":tenant,"i":oid})
            for table in ('audit_events','idempotency_records'):
                c.execute(text(f"delete from production.{table} where tenant_id=:t and actor_id=:a"),{"t":tenant,"a":actor})
        engine.dispose()


def test_material_return_preserves_issue_history_and_adjusts_cost_once(material_order):
    repo,t,o,a,s=material_order
    movements={f'reserve{n}_{s}':{'id':f'mov{n}_{s}','quantity':2,'unit_cost':3} for n in range(2)}
    repo.prepare_warehouse_issue(t,o,a,s)
    repo.complete_warehouse_issue(t,o,movements,None,a,s)
    payload={'id':'return_'+s,'source_id':o,'source_type':'production_order','reservation_id':f'reserve0_{s}','original_movement_id':f'mov0_{s}','movement_id':'retmov_'+s,'quantity':'1','unit_cost':'3','status':'received_pending_reconciliation'}
    with pytest.raises(ValueError,match='material_return_terminal_order_required'):repo.validate_material_return(t,payload)
    repo.update_order_status(t,o,schemas.ProductionOrderStatusRequest(status='cancelled',reason='Orden cancelada de prueba'),s+'-cancel','cancel',a,{})
    assert repo.validate_material_return(t,payload)['source_code']==o
    assert any(row['id']==f'mov0_{s}' for row in repo.returnable_materials(t,100))
    assert repo.reconcile_material_return(t,payload,a)['status']=='completed'
    repo.reconcile_material_return(t,payload,a)
    order=repo.get_order(t,o)
    assert order.status=='cancelled' and order.actual_cost==9
    assert len(order.material_returns)==1
    assert order.resources[0].actual_quantity==2
    assert len(repo.returnable_materials('other-tenant'))==0


def test_maintenance_hold_blocks_start_resume_and_manual_machine_release(material_order):
    repo,t,o,a,s=material_order;machine='machine_'+s
    with repo.engine.begin() as c:
        c.execute(text("delete from production.production_order_resources where tenant_id=:t and production_order_id=:o"),{'t':t,'o':o})
        c.execute(text("insert into production.machines(id,tenant_id,code,name,machine_type,available_minutes_per_day,status,maintenance_order_ref_id) values(:id,:t,:id,'Máquina sintética','Test',60,'maintenance',:maintenance)"),{'id':machine,'t':t,'maintenance':'maintenance_'+s})
        c.execute(text("insert into production.production_order_resources(id,tenant_id,production_order_id,resource_type,resource_ref_id,resource_code,resource_name_snapshot,unit,planned_quantity,unit_cost_snapshot,planned_cost) values(:id,:t,:o,'machine',:machine,:machine,'Máquina sintética','MIN',10,1,10)"),{'id':'resource_'+s,'t':t,'o':o,'machine':machine})
    try:
        for status in ('released','paused'):
            with repo.engine.begin() as c:c.execute(text('update production.production_orders set status=:status where tenant_id=:t and id=:o'),{'status':status,'t':t,'o':o})
            with pytest.raises(ValueError,match='production_machine_maintenance_required'):repo.preflight_order_status(t,o,'in_progress')
            with pytest.raises(ValueError,match='production_machine_maintenance_required'):repo.update_order_status(t,o,schemas.ProductionOrderStatusRequest(status='in_progress',reason='Intento bloqueado'),s+status,'blocked',a,{})
        with pytest.raises(ValueError,match='machine_maintenance_release_required'):repo.update_machine(t,machine,schemas.MachineUpdateRequest(status='active'),s+'-machine','machine',a)
    finally:
        with repo.engine.begin() as c:c.execute(text('delete from production.machines where tenant_id=:t and id=:id'),{'t':t,'id':machine})


def test_failed_creation_proof_does_not_authorize_existing_orders(material_order):
    repo,t,o,a,s=material_order;failed='failed_'+s
    assert not repo.record_failed_creation(t,o,'Existing order',a,'conflict')
    assert repo.record_failed_creation(t,failed,'Failed test',a,'resources_unavailable')
    assert repo.failed_creation(t,failed,'other-actor') is None
    assert repo.failed_creation('other-tenant',failed,a) is None
    with pytest.raises(ValueError,match='production_creation_attempt_failed'):repo.require_new_creation_attempt(t,failed)
    repo.recover_failed_creation(t,failed,a)
    assert repo.failed_creation(t,failed,a)['status']=='recovered'


def test_warehouse_issue_blocks_start_recovers_partial_failure_and_never_reissues(material_order):
    repo,t,o,a,s=material_order
    with pytest.raises(ValueError,match="material_consumption_required"):repo.preflight_order_status(t,o,"in_progress")
    with pytest.raises(ValueError,match="material_consumption_required"):
        repo.update_order_status(t,o,schemas.ProductionOrderStatusRequest(status="in_progress",reason="Inicio de prueba"),s+"-blocked","blocked",a,{})
    assert any(r["id"]==o for r in repo.list_warehouse_material_requests(t,100,0)["data"])
    assert repo.warehouse_material_request("other-tenant",o) is None
    with pytest.raises(ErclaveError,match="Order not found"):
        repo.prepare_warehouse_issue("other-tenant",o,a,s)
    class Inventory:
        calls=[]
        fail=True
        def reservation_action(self,tenant,reservation,action,authorization,key,reason):
            assert tenant==t and action=="consume" and key==f"production-order-{o}-material-start"
            self.calls.append(reservation)
            if reservation==f"reserve1_{s}" and self.fail:raise ErclaveError("inventory_unavailable","Retry",503)
            return {"id":"mov_"+reservation,"quantity":2,"unit_cost":3}
    inventory=Inventory();access=api.AuthorizedContext(t,a,"inventory.movement.create",frozenset({"inventory.movement.create"}))
    def issue():return api.issue_order_materials(o,None,t,None,s,repo,inventory,access)["data"]
    assert issue()["status"]=="needs_reconciliation"
    with pytest.raises(ValueError,match="production_material_issue_pending"):repo.preflight_order_status(t,o,"cancelled")
    with pytest.raises(ValueError,match="material_consumption_required"):repo.preflight_order_status(t,o,"in_progress")
    inventory.fail=False
    assert issue()["status"]=="issued"
    count=len(inventory.calls);assert issue()["status"]=="issued";assert len(inventory.calls)==count
    assert inventory.calls.count(f"reserve0_{s}")==1
    assert repo.get_order(t,o).status=="released"
    assert repo.get_order(t,o).actual_cost==12
    assert not any(r["id"]==o for r in repo.list_warehouse_material_requests(t,100,0)["data"])
    repo.preflight_order_status(t,o,"in_progress")
    result=repo.update_order_status(t,o,schemas.ProductionOrderStatusRequest(status="in_progress",reason="Inicio de prueba"),s+"-start","start",a,{})
    assert result.status=="in_progress" and result.actual_cost==12
    assert all(r.actual_quantity==2 for r in result.resources)
    with repo.engine.connect() as c:
        assert c.execute(text("select authorized_by from production.material_issues where tenant_id=:t and production_order_id=:o"),{"t":t,"o":o}).scalar_one()==a


def test_lock_and_crash_after_preparation_are_recoverable(material_order):
    repo,t,o,a,s=material_order
    with repo.material_command_lock(t,o):
        with pytest.raises(ErclaveError,match="in progress"):
            with repo.material_command_lock(t,o):pass
        repo.prepare_warehouse_issue(t,o,a,s)
    assert repo.warehouse_material_request(t,o)["status"]=="processing"
    with pytest.raises(ValueError,match="production_material_issue_pending"):repo.preflight_order_status(t,o,"cancelled")
    with repo.material_command_lock(t,o):
        order,movements=repo.prepare_warehouse_issue(t,o,a,s)
        assert order.status=="released" and movements=={}


def test_order_without_materials_does_not_need_a_warehouse_issue(material_order):
    repo,t,o,a,s=material_order
    with repo.engine.begin() as c:c.execute(text("delete from production.production_order_resources where tenant_id=:t and production_order_id=:o"),{"t":t,"o":o})
    assert repo.preflight_order_status(t,o,"in_progress").id==o
    assert not any(r["id"]==o for r in repo.list_warehouse_material_requests(t,100,0)["data"])
