"""CC-14 consumer proofs: transport identity, malformed data, tampering and scope."""
import importlib
import sys
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from erclave_common.config import Settings
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import OrganizationAccess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
proofs=importlib.import_module('app.producer_context')
schemas=importlib.import_module('app.schemas')
main=importlib.import_module('app.main')
auth=importlib.import_module('app.authorization')
repos=importlib.import_module('app.repositories')
contexts=importlib.import_module('app.reservation_context')
api=importlib.import_module('app.api')

CTX={'division_ref_id':'division','society_ref_id':'society','division_code':'D','division_name':'Division','cost_currency':'MXN'}
STAMP='2026-10-12T12:00:00+00:00'
KEY='purchase-receipt-line-key'

def purchase_payload():
    return schemas.MovementCreate(movement_type='entry',inventory_item_id='item',warehouse_id='warehouse',quantity='2.123456',unit='H87',unit_cost='82.469120',reason='Purchase receipt',source={'type':'purchase_receipt','id':'receipt','line_id':'line'},occurred_at=STAMP)

def purchase_proof():
    return {'organization_context':deepcopy(CTX),'quantity':'2.123456','unit_cost':'82.469120','original_unit_cost':'4.123456','cost_exchange_rate':'20','original_currency':'USD','occurred_at':STAMP,'receipt_id':'receipt','receipt_line_id':'line','inventory_item_id':'item','warehouse_id':'warehouse','unit':'H87','inventory_idempotency_key':KEY}

def maintenance_payload():
    return schemas.ReservationCreateRequest(inventory_item_id='item',warehouse_id='warehouse',quantity=2.123456,unit='H87',source={'type':'maintenance_order','id':'order','line_id':'line'})

def maintenance_proof():
    return {'organization_context':deepcopy(CTX),'quantity':'2.123456','order_id':'order','line_id':'line','inventory_item_id':'item','warehouse_id':'warehouse','unit':'H87','line_status':'pending','order_status':'assigned','request_status':'processing'}

def test_purchase_proof_preserves_decimal_original_rate_and_base():
    context,monetary=proofs.validate_purchase_proof(purchase_proof(),purchase_payload(),KEY)
    assert context.model_dump()==CTX
    assert monetary=={'original_currency':'USD','original_unit_cost':'4.123456','cost_exchange_rate':'20','unit_cost':'82.469120'}

@pytest.mark.parametrize('field,value',[('receipt_id','other'),('receipt_line_id','other'),('inventory_item_id','other'),('warehouse_id','other'),('unit','KGM'),('quantity','2'),('unit_cost','82.47'),('occurred_at','2026-10-13T12:00:00+00:00'),('inventory_idempotency_key','other-key')])
def test_purchase_proof_rejects_altered_effect(field,value):
    proof=purchase_proof();proof[field]=value
    with pytest.raises(ErclaveError) as error:proofs.validate_purchase_proof(proof,purchase_payload(),KEY)
    assert error.value.code==('assignment_authority_unavailable' if field=='unit_cost' else 'operational_context_mismatch')

@pytest.mark.parametrize('proof',[None,[],{}, {'organization_context':None}])
def test_purchase_proof_malformed_is_dependency_failure(proof):
    with pytest.raises(ErclaveError) as error:proofs.validate_purchase_proof(proof,purchase_payload(),KEY)
    assert error.value.status_code==503

@pytest.mark.parametrize('field,value',[('quantity','NaN'),('quantity','Infinity'),('quantity','0'),('unit_cost','-1'),('original_unit_cost','NaN'),('cost_exchange_rate','0')])
def test_purchase_proof_rejects_invalid_money(field,value):
    proof=purchase_proof();proof[field]=value
    with pytest.raises(ErclaveError) as error:proofs.validate_purchase_proof(proof,purchase_payload(),KEY)
    assert error.value.status_code==503

@pytest.mark.parametrize('currency',[None,[],{},'usd','XXX-invalid'])
def test_purchase_proof_rejects_malformed_original_currency(currency):
    proof=purchase_proof();proof['original_currency']=currency
    with pytest.raises(ErclaveError) as error:proofs.validate_purchase_proof(proof,purchase_payload(),KEY)
    assert error.value.status_code==503

def test_purchase_proof_missing_currency_is_controlled_dependency_error():
    proof=purchase_proof();del proof['original_currency']
    with pytest.raises(ErclaveError) as error:proofs.validate_purchase_proof(proof,purchase_payload(),KEY)
    assert error.value.status_code==503

@pytest.mark.parametrize('field,value',[('order_id','other'),('line_id','other'),('inventory_item_id','other'),('warehouse_id','other'),('unit','KGM'),('quantity','2'),('quantity','Infinity')])
def test_maintenance_proof_rejects_altered_allocation(field,value):
    proof=maintenance_proof();proof[field]=value
    with pytest.raises(ErclaveError) as error:proofs.validate_maintenance_proof(proof,maintenance_payload())
    assert error.value.code=='operational_context_mismatch'

@pytest.mark.parametrize('field,value',[('line_status','issued'),('line_status','released'),('order_status','resolved'),('order_status','cancelled'),('request_status','cancelled')])
def test_maintenance_reservation_requires_live_intent(field,value):
    proof=maintenance_proof();proof[field]=value
    with pytest.raises(ErclaveError) as error:proofs.validate_maintenance_proof(proof,maintenance_payload())
    assert error.value.status_code==409

def test_maintenance_null_context_is_explicit_legacy_only():
    proof=maintenance_proof();proof['organization_context']=None
    assert proofs.validate_maintenance_proof(proof,maintenance_payload()) is None
    del proof['organization_context']
    with pytest.raises(ErclaveError):proofs.validate_maintenance_proof(proof,maintenance_payload())

@pytest.mark.parametrize('change',['missing-context','missing-cost','wrong-division','wrong-cost','nan-cost'])
def test_return_proof_rejects_conflict_before_physical_receipt(change):
    source={'source_type':'maintenance_order','organization_context':deepcopy(CTX),'unit_cost':'4.123456'}
    proof={'organization_context':deepcopy(CTX),'unit_cost_snapshot':'4.123456'}
    if change=='missing-context':del proof['organization_context']
    elif change=='missing-cost':del proof['unit_cost_snapshot']
    elif change=='wrong-division':proof['organization_context']['division_ref_id']='other'
    elif change=='wrong-cost':proof['unit_cost_snapshot']='4.12'
    else:proof['unit_cost_snapshot']='NaN'
    with pytest.raises(ErclaveError) as error:api.validate_return_snapshot(source,proof)
    assert error.value.status_code in (409,503)

def test_return_proof_conserves_six_decimal_cost():
    source={'source_type':'maintenance_order','organization_context':CTX,'unit_cost':Decimal('4.123456')}
    api.validate_return_snapshot(source,{'organization_context':CTX,'unit_cost_snapshot':'4.123456'})

@pytest.mark.parametrize('base',['http://service.example','https://localhost','https://user:pass@service.example','https://service.example?token=x'])
def test_remote_proof_rejects_invalid_service_origin_before_transport(base):
    client=SimpleNamespace(environment='qa',client=SimpleNamespace(get=lambda *args:pytest.fail('must not call dependency')))
    with pytest.raises(ErclaveError) as error:proofs.read_proof(client,base,'/proof','tenant','Bearer test','actor')
    assert error.value.status_code==503


@pytest.fixture
def api_client():
    calls=[]
    state={'permissions':['inventory.movement.create','maintenance.material_request.create'],'scope':True,'proof':purchase_proof()}
    class Admin:
        def get_context(self,tenant,authorization):
            return {'tenant':{'id':'tenant','status':'active'},'user':{'id':'real-actor','status':'active'},'active_modules':['admin','inventory','maintenance','purchasing'],'permissions':state['permissions']}
    class Repository:
        def create_reservation(self,t,p,k,h,a,**kwargs):
            calls.append(('reserve',t,a,k,kwargs))
            return schemas.ReservationRead(id='reservation',inventory_item_id=p.inventory_item_id,warehouse_id=p.warehouse_id,quantity=p.quantity,unit=p.unit,unit_cost_snapshot=4.123456,source_type=p.source.type,source_id=p.source.id,source_line_id=p.source.line_id,status='active',created_at=datetime.now(timezone.utc),organization_context=kwargs.get('organization_context'))
        def create_movement(self,t,p,k,h,a,**kwargs):
            calls.append(('write',t,a,k,kwargs))
            return schemas.MovementRead(id='movement',movement_code='MOV',movement_type='entry',inventory_item_id=p.inventory_item_id,warehouse_id=p.warehouse_id,direction='in',quantity=p.quantity,unit=p.unit,unit_cost=p.unit_cost,reason=p.reason,source_type=p.source.type,source_id=p.source.id,status='recorded',occurred_at=p.occurred_at,organization_context=kwargs['organization_context'])
    class Client:
        environment='local';purchasing='http://127.0.0.1:8010';maintenance='http://127.0.0.1:8012'
        @property
        def client(self):return self
        def get(self,base,path,tenant,authorization,actor):
            calls.append(('proof',tenant,actor,path,authorization))
            return state['proof']
        def access(self,tenant,permission,authorization,actor):
            return OrganizationAccess(tenant,actor,tuple(state['permissions']),({'id':'division','society_id':'society','code':'D','name':'Division'},) if state['scope'] else (),False,False)
    main.app.dependency_overrides[auth.get_settings]=lambda:Settings(auth_mode='firebase')
    main.app.dependency_overrides[auth.get_admin_session_client]=lambda:Admin()
    main.app.dependency_overrides[repos.get_inventory_repository]=lambda:Repository()
    main.app.dependency_overrides[contexts.get_reservation_context_client]=lambda:Client()
    main.app.dependency_overrides[auth.get_unit_catalog_client]=lambda:SimpleNamespace(require_active=lambda *args:'H87')
    yield TestClient(main.app),state,calls
    main.app.dependency_overrides.clear()

def headers():return {'X-Tenant-Id':'tenant','Authorization':'Bearer test','X-Actor-Id':'forged-actor','Idempotency-Key':KEY}

def test_authenticated_purchase_uses_session_actor_not_claimed_actor(api_client):
    client,state,calls=api_client
    response=client.post('/v1/inventory/purchase-receipts',headers=headers(),json=purchase_payload().model_dump(mode='json'))
    assert response.status_code==201,response.text
    assert calls[0][2]=='real-actor' and calls[-1][2]=='real-actor'
    assert calls[-1][4]['purchase_proof']['original_unit_cost']=='4.123456'

@pytest.mark.parametrize('kind',['missing-token','wrong-tenant','permission','revoked-scope','tampered-cost','wrong-key'])
def test_purchase_api_rejects_before_any_inventory_write(api_client,kind):
    client,state,calls=api_client;head=headers();body=purchase_payload().model_dump(mode='json')
    if kind=='missing-token':head.pop('Authorization')
    elif kind=='wrong-tenant':head['X-Tenant-Id']='other'
    elif kind=='permission':state['permissions']=[]
    elif kind=='revoked-scope':state['scope']=False
    elif kind=='tampered-cost':body['unit_cost']='1'
    else:head['Idempotency-Key']='different-key'
    response=client.post('/v1/inventory/purchase-receipts',headers=head,json=body)
    assert response.status_code in (401,403,422),response.text
    assert not any(row[0]=='write' for row in calls)

def test_maintenance_api_uses_producer_context_and_authenticated_actor(api_client):
    client,state,calls=api_client;state['proof']=maintenance_proof()
    body=maintenance_payload().model_dump(mode='json')
    body['organization_context']={**CTX,'division_ref_id':'forged-division'}
    response=client.post('/v1/inventory/reservation-requests',headers=headers(),json=body)
    assert response.status_code==201,response.text
    assert response.json()['data']['organization_context']==CTX
    assert calls[0][2]=='real-actor' and calls[-1][2]=='real-actor'
    assert '/v1/maintenance/orders/order/inventory-context?line_id=line' in calls[0][3]

@pytest.mark.parametrize('kind',['scope','permission','quantity','source-owner','line','terminal','missing-context'])
def test_maintenance_api_rejects_before_reservation(api_client,kind):
    client,state,calls=api_client;state['proof']=maintenance_proof()
    body=maintenance_payload().model_dump(mode='json')
    if kind=='scope':state['scope']=False
    elif kind=='permission':state['permissions']=['inventory.movement.create']
    elif kind=='quantity':body['quantity']=50
    elif kind=='source-owner':body['source']['type']='production_order'
    elif kind=='line':body['source']['line_id']='other'
    elif kind=='terminal':state['proof']['order_status']='resolved'
    else:del state['proof']['organization_context']
    response=client.post('/v1/inventory/reservation-requests',headers=headers(),json=body)
    assert response.status_code in (403,409,422,503),response.text
    assert not any(row[0]=='reserve' for row in calls)


@pytest.fixture
def pg_inventory():
    import os
    from contextlib import contextmanager
    from uuid import uuid4
    from sqlalchemy import create_engine,text
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool
    from erclave_common.operational_context import OperationalContext
    configured=os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not configured:pytest.skip('Local PostgreSQL required')
    parsed=make_url(configured)
    assert parsed.host in ('127.0.0.1','localhost','::1') and parsed.port==5434 and parsed.database=='erclave_local' and not parsed.query
    tenant='ten_739ee59d765d5e14818674800d'
    engine=create_engine(parsed,poolclass=NullPool)
    with engine.connect() as connection:
        transaction=connection.begin()
        class TransactionEngine:
            @contextmanager
            def begin(self):
                with connection.begin_nested():yield connection
            @contextmanager
            def connect(self):yield connection
        try:
            assert connection.execute(text('select id from admin.tenants where id=:t'),{'t':tenant}).scalar()==tenant
            suffix=uuid4().hex[:18];item='cc14p_i_'+suffix;warehouse='cc14p_w_'+suffix
            context=OperationalContext(**{**CTX,'division_ref_id':'cc14p_d_'+suffix})
            connection.execute(text("insert into inventory.items(id,tenant_id,code,name,type,base_unit) values(:id,:t,:id,'CC14 proof fixture','material','H87')"),{'id':item,'t':tenant})
            connection.execute(text("insert into inventory.warehouses(id,tenant_id,code,name,type,business_center,location,owner,division_ref_id,division_revision) values(:id,:t,:id,'CC14 proof warehouse','general','Synthetic','Synthetic','Synthetic',:d,1)"),{'id':warehouse,'t':tenant,'d':context.division_ref_id})
            connection.execute(text("insert into inventory.item_division_assignments(tenant_id,item_id,division_ref_id,status,revision) values(:t,:i,:d,'active',1)"),{'t':tenant,'i':item,'d':context.division_ref_id})
            repository=repos.InventoryRepository(TransactionEngine())
            entry=schemas.MovementCreate(movement_type='entry',inventory_item_id=item,warehouse_id=warehouse,quantity=10,unit='H87',unit_cost='4.123456',reason='CC14 fixture',source={'type':'manual','id':suffix},occurred_at=STAMP)
            movement=repository.create_movement(tenant,entry,'entry-'+suffix,'entry','actor',organization_context=context)
            yield repository,connection,tenant,item,warehouse,context,suffix,movement
        finally:transaction.rollback()
    engine.dispose()


@pytest.mark.parametrize('state',['released','expired'])
@pytest.mark.parametrize('same_key',[True,False])
def test_pg_maintenance_terminal_reservation_never_reactivates_or_recosts(pg_inventory,state,same_key):
    from sqlalchemy import text
    repository,connection,tenant,item,warehouse,context,suffix,movement=pg_inventory
    payload=schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=warehouse,quantity=2,unit='H87',source={'type':'maintenance_order','id':'order-'+suffix,'line_id':'line-'+suffix})
    initial_key='reserve-'+suffix
    reservation=repository.create_reservation(tenant,payload,initial_key,'reserve','actor',organization_context=context)
    if state=='released':repository.release_reservation(tenant,reservation.id,'Synthetic release','release-'+suffix,'release','actor',allowed_sources={'maintenance_order'})
    else:connection.execute(text("update inventory.reservations set expires_at=now()-interval '1 minute' where tenant_id=:t and id=:id"),{'t':tenant,'id':reservation.id})
    before=connection.execute(text('select status,quantity,unit_cost_snapshot,expires_at,organization_context from inventory.reservations where tenant_id=:t and id=:id'),{'t':tenant,'id':reservation.id}).mappings().one()
    # Another entry changes average stock cost, making accidental recosting observable.
    entry=schemas.MovementCreate(movement_type='entry',inventory_item_id=item,warehouse_id=warehouse,quantity=10,unit='H87',unit_cost='100',reason='Changed current valuation',source={'type':'manual','id':suffix},occurred_at=STAMP)
    repository.create_movement(tenant,entry,'new-cost-'+suffix,'new-cost','actor',organization_context=context)
    with pytest.raises(ValueError,match='reservation_source_conflict'):
        repository.create_reservation(tenant,payload,initial_key if same_key else 'new-reserve-'+suffix,'reserve','actor',organization_context=context)
    after=connection.execute(text('select status,quantity,unit_cost_snapshot,expires_at,organization_context from inventory.reservations where tenant_id=:t and id=:id'),{'t':tenant,'id':reservation.id}).mappings().one()
    assert dict(after)==dict(before)
    assert after['unit_cost_snapshot']==Decimal('4.123456')


def test_pg_cc14_downgrade_rejects_history_before_any_schema_drop(pg_inventory,monkeypatch):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    repository,connection,tenant,item,warehouse,context,suffix,movement=pg_inventory
    connection.execute(text("update inventory.movements set monetary_snapshot=cast(:snapshot as jsonb) where tenant_id=:t and id=:id"),{'snapshot':'{"original_currency":"MXN","original_unit_cost":"4.123456","cost_exchange_rate":"1","unit_cost":"4.123456"}','t':tenant,'id':movement.id})
    path=Path(__file__).resolve().parents[3]/'alembic/versions/20261012_0057_inventory_producers.py'
    spec=importlib.util.spec_from_file_location('cc14_migration_proof',path)
    migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    operations=Operations(MigrationContext.configure(connection))
    monkeypatch.setattr(migration,'op',operations)
    for method in ('drop_index','drop_column','drop_constraint'):
        monkeypatch.setattr(operations,method,lambda *args,**kwargs:pytest.fail('history must block before schema mutation'))
    with pytest.raises(DBAPIError,match='CC14 history exists'):
        with connection.begin_nested():
            connection.execute(text("set local lock_timeout='2s'"))
            migration.downgrade()
    assert connection.execute(text("select organization_context from inventory.movements where tenant_id=:t and id=:id"),{'t':tenant,'id':movement.id}).scalar()==context.model_dump()
    assert connection.execute(text("select 1 from information_schema.columns where table_schema='inventory' and table_name='movements' and column_name='monetary_snapshot'")).scalar()==1
