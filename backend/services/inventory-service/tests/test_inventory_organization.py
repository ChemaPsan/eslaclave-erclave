import importlib,sys,os
from pathlib import Path
from contextlib import contextmanager
from dataclasses import replace
from uuid import uuid4
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.pool import NullPool
from fastapi.testclient import TestClient
from erclave_common.config import Settings,get_settings
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import OrganizationAccess,OrganizationClient,resolve_organization_access,get_organization_client
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
main=importlib.import_module('app.main');repos=importlib.import_module('app.repositories')
Store=importlib.import_module('app.organization_store').OrganizationStore
schemas=importlib.import_module('app.organization_schemas')
api=importlib.import_module('app.organization_api')
TENANT='ten_739ee59d765d5e14818674800d'
DIVISIONS=({'id':'division-a','code':'DIV-A','name':'Division A','society_id':'society-a'},{'id':'division-b','code':'DIV-B','name':'Division B','society_id':'society-b'})
PERMISSIONS=('inventory.warehouse.read','inventory.warehouse.update','inventory.item.read','inventory.item.update','costing.cost_center.read')
def context():return {'tenant':{'id':TENANT,'status':'active'},'user':{'id':'actor','status':'active'},'scope':{'version':2,'all_divisions':True,'divisions':list(DIVISIONS)},'permissions':list(PERMISSIONS),'active_modules':['admin','inventory'],'capabilities':{'cost_center_catalog':{'available':False}}}
def access():return resolve_organization_access(context(),TENANT,'inventory','inventory.item.update')

@pytest.mark.parametrize('field,value,code',[
 ('tenant',{'id':'foreign','status':'active'},'tenant_access_denied'),('user',{'id':'actor','status':'inactive'},'tenant_access_denied'),
 ('active_modules',['admin','accounting'],'module_not_enabled'),('active_modules',['inventory'],'module_not_enabled'),('permissions',[],'permission_denied'),('scope',{'version':1},'organization_scope_review_required'),
 ('scope',{'version':2,'divisions':[{}]},'assignment_authority_unavailable'),('capabilities',[],'assignment_authority_unavailable')])
def test_assignment_authority_fails_closed(field,value,code):
    data=context();data[field]=value
    with pytest.raises(ErclaveError) as exc:resolve_organization_access(data,TENANT,'inventory','inventory.item.update')
    assert exc.value.code==code

@pytest.mark.parametrize('center', [{'id':'cc','code':'CC1','name':'Center','division_ref_id':'foreign','status':'active'}, {'id':'cc','code':'CC1','name':'Center','division_ref_id':'division-a','status':'inactive'}])
def test_costing_reference_must_match_division_and_state(center):
    client=OrganizationClient(Settings());client.get=lambda *args:center
    with pytest.raises(ErclaveError) as exc:client.center(replace(access(),catalog_available=True),'cc','division-a')
    assert exc.value.code=='assignment_center_invalid'

@pytest.mark.parametrize('url', ['http://localhost:8014', '', 'https://127.0.0.1:8014', 'http://costing.example.test', 'https://user:password@costing.example.test', 'https://costing.example.test?token=value'])
def test_remote_center_validation_never_falls_back_to_local_or_ambiguous_url(url):
    client=OrganizationClient(Settings());client.environment='qa';client.costing=url
    def unexpected_request(*args):raise AssertionError('Invalid remote authority must not be contacted')
    client.get=unexpected_request
    with pytest.raises(ErclaveError) as exc:client.center(replace(access(),catalog_available=True),'cc','division-a')
    assert exc.value.code=='assignment_authority_unavailable'
    assert exc.value.status_code==503

def test_optional_costing_is_never_enabled_by_permission():
    client=OrganizationClient(Settings())
    with pytest.raises(ErclaveError) as exc:client.center(access(),'cc','division-a')
    assert exc.value.code=='module_not_enabled'
    with pytest.raises(ErclaveError):replace(access(),all_divisions=False,divisions=()).division('division-a')

class TransactionEngine:
    def __init__(self,conn):self.conn=conn
    @contextmanager
    def begin(self):
        with self.conn.begin_nested():yield self.conn
    @contextmanager
    def connect(self):yield self.conn

@pytest.fixture
def local_store():
    value=os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not value:pytest.skip('Local PostgreSQL URL not configured')
    from sqlalchemy.engine import make_url
    parsed=make_url(value)
    assert parsed.host in ('127.0.0.1','localhost','::1') and parsed.port==5434 and parsed.database=='erclave_local' and not parsed.query
    engine=create_engine(parsed,poolclass=NullPool)
    with engine.connect() as conn:
        txn=conn.begin()
        try:
            assert conn.execute(text('select id from admin.tenants where id=:t'),{'t':TENANT}).scalar()==TENANT
            wh='test_'+uuid4().hex[:26];item='test_'+uuid4().hex[:26]
            conn.execute(text("insert into inventory.warehouses(id,tenant_id,code,name,type,business_center,location,owner) values(:i,:t,:i,'Synthetic warehouse','general','Legacy text','Synthetic','Synthetic')"),{'i':wh,'t':TENANT})
            conn.execute(text("insert into inventory.items(id,tenant_id,code,name,type,base_unit) values(:i,:t,:i,'Synthetic 100% item','material','PZA')"),{'i':item,'t':TENANT})
            yield Store(repos.InventoryRepository(TransactionEngine(conn))),conn,wh,item
        finally:txn.rollback()
    engine.dispose()
class NoCosting:
    def center(self,*args):raise AssertionError('Catalog must not be required when no center is selected')
def save(store,kind,id_,division,payload,key=None,actor=None,client=None):
    schema=schemas.WarehouseDivisionCommand if kind=='warehouse' else schemas.ItemDivisionCommand
    return store.save(actor or access(),kind,id_,division,schema(**payload),key or 'test-'+uuid4().hex,'test-correlation',client or NoCosting())

def test_postgres_warehouse_expansion_immutability_revision_and_scope(local_store):
    store,conn,wh,item=local_store
    assert store.warehouse(access(),wh)['division_ref_id'] is None
    restricted=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],))
    payload={'division_ref_id':'division-a','expected_revision':0}
    with pytest.raises(ErclaveError) as exc:save(store,'warehouse',wh,'division-a',payload,actor=restricted)
    assert exc.value.code=='assignment_unassigned_requires_full_scope'
    key='test-'+uuid4().hex
    first=save(store,'warehouse',wh,'division-a',payload,key)
    assert first==save(store,'warehouse',wh,'division-a',payload,key)
    assert conn.execute(text('select business_center from inventory.warehouses where tenant_id=:t and id=:i'),{'t':TENANT,'i':wh}).scalar()=='Legacy text'
    with pytest.raises(ErclaveError) as exc:save(store,'warehouse',wh,'division-b',{'division_ref_id':'division-b','expected_revision':1})
    assert exc.value.code=='assignment_warehouse_division_locked'
    with pytest.raises(ErclaveError) as exc:save(store,'warehouse',wh,'division-a',payload)
    assert exc.value.code=='assignment_revision_conflict'
    with pytest.raises(ErclaveError):store.warehouse(replace(restricted,divisions=(DIVISIONS[1],)),wh)
    with pytest.raises(ErclaveError) as exc:store.warehouse(replace(access(),tenant_id='foreign'),wh)
    assert exc.value.status_code==404
    assert conn.execute(text("select count(*) from inventory.audit_events where tenant_id=:t and entity_id=:i and action='organization_assignment.warehouse'"),{'t':TENANT,'i':wh}).scalar()==1

def test_postgres_shared_item_assignments_optional_center_and_history(local_store):
    store,conn,wh,item=local_store;payload={'expected_revision':0,'status':'active','cost_center_ref_id':None};key='test-'+uuid4().hex
    first=save(store,'item',item,'division-a',payload,key)
    assert first==save(store,'item',item,'division-a',payload,key)
    save(store,'item',item,'division-b',payload)
    assert store.items(access(),item,25,0)['meta']['total']==2
    assert store.items(replace(access(),all_divisions=False,divisions=(DIVISIONS[0],)),item,25,0)['meta']['total']==1
    assert store.eligible(access(),'division-a','%',20,0)['data'][0]['id']==item
    assert store.eligible(access(),'division-a','__',20,0)['data']==[]
    with pytest.raises(ErclaveError) as exc:save(store,'item',item,'division-a',{**payload,'status':'inactive'},key)
    assert exc.value.code=='idempotency_key_reused'
    class Center:
        def center(self,a,id_,division):return {'id':id_,'code':'CC-01','name':'Synthetic'}
    changed=save(store,'item',item,'division-a',{'expected_revision':1,'cost_center_ref_id':'cc'},client=Center())
    assert changed['revision']==2
    class Down:
        def center(self,*args):raise ErclaveError('assignment_authority_unavailable','unavailable',503)
    with pytest.raises(ErclaveError):save(store,'item',item,'division-a',{'expected_revision':2,'cost_center_ref_id':'cc'},client=Down())
    assert store.items(access(),item,25,0,'division-a')['data'][0]['revision']==2
    inactive=save(store,'item',item,'division-a',{'expected_revision':2,'status':'inactive','cost_center_ref_id':'cc'},client=Down())
    assert inactive['cost_center_snapshot']==changed['cost_center_snapshot']
    assert store.eligible(access(),'division-a','',20,0)['data']==[]
    assert conn.execute(text('select count(*) from inventory.items where tenant_id=:t and id=:i'),{'t':TENANT,'i':item}).scalar()==1
    assert store.items(access(),item,25,0,'division-a')['data'][0]['revision']==3

def test_postgres_downgrade_preserves_assignment_history(local_store):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,wh,item=local_store
    save(store,'item',item,'division-a',{'expected_revision':0})
    path=ROOT.parents[1]/'alembic/versions/20260927_0041_inventory_dimensions.py'
    spec=importlib.util.spec_from_file_location('inventory_dimension_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Inventory assignment history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    assert store.items(access(),item,25,0)['meta']['total']==1

def test_api_checks_scope_permissions_payload_and_idempotency():
    class Client:
        data=context()
        def session(self,*args):return self.data
    class Fake:
        def warehouse(self,*args):return {'warehouse_id':'warehouse','division_ref_id':None,'revision':0}
        def save(self,*args):
            if args[1]=='item':return {'item_id':'item','division_ref_id':'division-a','status':'active','cost_center_ref_id':None,'revision':1}
            return {'warehouse_id':'warehouse','division_ref_id':'division-a','revision':1}
    authority=Client();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'test-assignment'}
        assert http.get('/v1/inventory/organization/divisions?limit=26',headers=headers).status_code==422
        assert http.get('/v1/inventory/organization/divisions?q=DIV-A',headers=headers).json()['meta']['total']==1
        path='/v1/inventory/warehouses/warehouse/division';payload={'division_ref_id':'division-a','expected_revision':0}
        assert http.patch(path,headers=headers,json={**payload,'society_ref_id':'bad'}).status_code==422
        assert http.patch(path,headers={k:v for k,v in headers.items() if k!='Idempotency-Key'},json=payload).status_code==400
        assert http.patch(path,headers=headers,json=payload).status_code==200
        item_path='/v1/inventory/items/item/division-assignments/division-a'
        assert http.put(item_path,headers=headers,json={'expected_revision':0}).status_code==200
        assert http.put(item_path,headers=headers,json={'expected_revision':0,'division_ref_id':'other'}).status_code==422
        assert http.put(item_path,headers=headers,json={'expected_revision':-1}).status_code==422
        authority.data=context();authority.data['permissions']=['inventory.warehouse.read']
        assert http.put(item_path,headers=headers,json={'expected_revision':0}).status_code==403
        assert http.get(path,headers=headers).status_code==200
        assert http.patch(path,headers=headers,json=payload).status_code==403
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
    finally:app.dependency_overrides.clear()


from erclave_common.operational_context import OperationalContext
inventory_schemas=importlib.import_module('app.schemas')

def test_reservation_context_rejects_cross_division_and_copies_to_stock_effect(local_store):
    from datetime import datetime,timezone
    store,conn,wh,item=local_store
    repo=store.repository
    # Existing balance is synthetic and rolled back together with assignments.
    movement=inventory_schemas.MovementCreate(movement_type='entry',inventory_item_id=item,warehouse_id=wh,quantity=10,unit='PZA',unit_cost=2,reason='Synthetic balance',source={'type':'manual','id':'synthetic'},occurred_at=datetime.now(timezone.utc))
    repo.create_movement(TENANT,movement,'entry-'+uuid4().hex,'entry','actor')
    save(store,'warehouse',wh,'division-a',{'division_ref_id':'division-a','expected_revision':0})
    save(store,'item',item,'division-a',{'status':'active','cost_center_ref_id':None,'expected_revision':0})
    context=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='DIV-A',division_name='Frozen A')
    payload=inventory_schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=wh,quantity=2,unit='PZA',source={'type':'sales_order','id':'synthetic-order','line_id':'synthetic-line'})
    with pytest.raises(ErclaveError) as exc:repo.create_reservation(TENANT,payload,'missing-'+uuid4().hex,'hash','actor')
    assert exc.value.code=='operational_context_required'
    with pytest.raises(ErclaveError) as exc:repo.create_reservation(TENANT,payload,'cross-'+uuid4().hex,'hash','actor',organization_context=context.model_copy(update={'division_ref_id':'division-b'}))
    assert exc.value.code=='operational_context_mismatch'
    key='reserve-'+uuid4().hex
    reservation=repo.create_reservation(TENANT,payload,key,'hash','actor',organization_context=context)
    assert repo.create_reservation(TENANT,payload,key,'hash','actor',organization_context=context).id==reservation.id
    assert reservation.organization_context==context
    first=repo.consume_reservation(TENANT,reservation.id,'Synthetic delivery','consume-'+key,'consume','actor',quantity=1,allowed_sources={'sales_order'})
    assert first.organization_context==context
    assert repo.consume_reservation(TENANT,reservation.id,'Synthetic delivery','consume-'+key,'consume','actor',quantity=1,allowed_sources={'sales_order'}).id==first.id
    assert repo.get_reservation(TENANT,reservation.id).quantity==1
    assert repo.list_movements(TENANT,warehouse=wh,allowed_divisions=['division-b'])==[]
    assert len(repo.list_movements(TENANT,warehouse=wh,allowed_divisions=['division-a']))==2
    assert repo.list_balances(TENANT,warehouse_id=wh,allowed_divisions=['division-b'])[0]==[]
    before=conn.execute(text('select count(*) from inventory.movements where tenant_id=:t and source_id=:id'),{'t':TENANT,'id':reservation.id}).scalar()
    conn.execute(text("update inventory.item_division_assignments set status='inactive' where tenant_id=:t and item_id=:id"),{'t':TENANT,'id':item})
    with pytest.raises(ErclaveError):repo.consume_reservation(TENANT,reservation.id,'Synthetic delivery','other-'+key,'other','actor',quantity=1,allowed_sources={'sales_order'})
    assert conn.execute(text('select count(*) from inventory.movements where tenant_id=:t and source_id=:id'),{'t':TENANT,'id':reservation.id}).scalar()==before
    assert repo.release_reservation(TENANT,reservation.id,'Stop synthetic','release-'+key,'release','actor',allowed_sources={'sales_order'}).status=='released'


reservation_context=importlib.import_module('app.reservation_context')

def test_reservation_context_api_scope_before_mutation_and_replay(local_store):
    from datetime import datetime,timezone
    store,conn,wh,item=local_store;repo=store.repository
    repo.create_movement(TENANT,inventory_schemas.MovementCreate(movement_type='entry',inventory_item_id=item,warehouse_id=wh,quantity=10,unit='PZA',unit_cost=2,reason='Synthetic balance',source={'type':'manual','id':'synthetic'},occurred_at=datetime.now(timezone.utc)),'entry-'+uuid4().hex,'entry','actor')
    save(store,'warehouse',wh,'division-a',{'division_ref_id':'division-a','expected_revision':0})
    save(store,'item',item,'division-a',{'status':'active','cost_center_ref_id':None,'expected_revision':0})
    frozen=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='DIV-A',division_name='Frozen A')
    scope=replace(access(),all_divisions=False,divisions=(DIVISIONS[1],))
    class Client:
        def sales_context(self,*args):return frozen
        def access(self,*args):return scope
    app=main.app
    app.dependency_overrides[repos.get_inventory_repository]=lambda:repo
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='demo')
    app.dependency_overrides[reservation_context.get_reservation_context_client]=lambda:Client()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'scope-'+uuid4().hex}
        payload={'inventory_item_id':item,'warehouse_id':wh,'quantity':2,'unit':'PZA','source':{'type':'sales_order','id':'synthetic-order','line_id':'line'}}
        assert http.post('/v1/inventory/reservation-requests',headers=headers,json=payload).status_code==403
        scope=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],))
        response=http.post('/v1/inventory/reservation-requests',headers=headers,json=payload)
        assert response.status_code==201,response.text
        id_=response.json()['data']['id']
        scope=replace(scope,divisions=(DIVISIONS[1],))
        assert http.post('/v1/inventory/reservation-requests',headers=headers,json=payload).status_code==403
        for action in ('release','consume'):
            assert http.post('/v1/inventory/reservations/'+id_+'/'+action,headers=headers,json={'reason':'Synthetic action'}).status_code==403
        assert all(row['warehouse_id']!=wh for row in http.get('/v1/inventory/movements',headers=headers).json()['data'])
        assert repo.get_reservation(TENANT,id_).status=='active'
        for report in ('kardex','balances','critical-reservations','warehouses'):
            response=http.get('/v1/inventory/reports/'+report+'/export',headers=headers)
            assert response.status_code in (200,204),response.text
            assert wh not in response.text
    finally:app.dependency_overrides.clear()


def test_society_currency_cost_precision_reversal_and_history_guard(local_store):
    from datetime import datetime, timezone
    from decimal import Decimal
    store, conn, wh, item = local_store
    repo = store.repository
    save(store, 'warehouse', wh, 'division-a', {'division_ref_id':'division-a','expected_revision':0})
    save(store, 'item', item, 'division-a', {'expected_revision':0})
    context = OperationalContext(division_ref_id='division-a', society_ref_id='society-a', division_code='A', division_name='Synthetic A', cost_currency='USD')
    payload = inventory_schemas.MovementCreate(movement_type='entry', inventory_item_id=item, warehouse_id=wh, quantity=10, unit='PZA', unit_cost=Decimal('12.123456'), reason='Synthetic cost', source={'type':'manual','id':'synthetic'}, occurred_at=datetime.now(timezone.utc))
    with pytest.raises(ValueError, match='operational_unit_cost_required'):
        repo.create_movement(TENANT, payload.model_copy(update={'unit_cost':None}), 'missing-'+uuid4().hex, 'missing', 'actor', organization_context=context)
    key='entry-'+uuid4().hex
    entry=repo.create_movement(TENANT,payload,key,'entry','actor',organization_context=context)
    assert entry.original_unit_cost==Decimal('12.123456')
    assert repo.create_movement(TENANT,payload,key,'entry','actor',organization_context=context).id==entry.id
    changed=context.model_copy(update={'cost_currency':'MXN'})
    with pytest.raises(ErclaveError) as exc:
        repo.create_movement(TENANT,payload,'other-'+key,'other','actor',organization_context=changed)
    assert exc.value.code=='operational_cost_history_review_required'
    reservation=repo.create_reservation(TENANT,inventory_schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=wh,quantity=2,unit='PZA',source={'type':'sales_order','id':'synthetic-order','line_id':'synthetic-line'}),'reserve-'+key,'reserve','actor',organization_context=context)
    assert reservation.original_unit_cost==Decimal('12.123456')
    movement=repo.consume_reservation(TENANT,reservation.id,'Synthetic delivery','consume-'+key,'consume','actor',quantity=1,allowed_sources={'sales_order'})
    assert movement.original_unit_cost==Decimal('12.123456') and movement.organization_context==context
    repo.release_reservation(TENANT,reservation.id,'Synthetic release','release-'+key,'release','actor',allowed_sources={'sales_order'})
    outgoing=repo.create_movement(TENANT,payload.model_copy(update={'movement_type':'exit','quantity':Decimal(1),'unit_cost':None}),'out-'+key,'out','actor',organization_context=context)
    reverse=repo.reverse_movement(TENANT,outgoing.id,'Synthetic reversal','reverse-'+key,'reverse','actor')
    assert reverse.organization_context==context and reverse.original_unit_cost==Decimal('12.123456')
    # Untagged history cannot silently acquire a currency on a later movement.
    conn.execute(text('update inventory.movements set organization_context=null where tenant_id=:t and id=:id'),{'t':TENANT,'id':entry.id})
    with pytest.raises(ErclaveError) as exc:
        repo.create_reservation(TENANT,inventory_schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=wh,quantity=1,unit='PZA',source={'type':'sales_order','id':'another','line_id':'line'}),'history-'+key,'history','actor',organization_context=context)
    assert exc.value.code=='operational_cost_history_review_required'


def test_finished_goods_context_cost_scope_and_replay(local_store):
    from datetime import datetime, timezone
    from decimal import Decimal
    store,conn,wh,item=local_store;repo=store.repository
    save(store,'warehouse',wh,'division-a',{'division_ref_id':'division-a','expected_revision':0})
    save(store,'item',item,'division-a',{'expected_revision':0})
    conn.execute(text("update inventory.items set type='finishedGood',use_in_recipe=true where tenant_id=:t and id=:i"),{'t':TENANT,'i':item})
    frozen=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='A',division_name='A',cost_currency='MXN')
    order_id='test_'+uuid4().hex[:26]
    order={'id':order_id,'code':'OP-SYNTHETIC','product_service_id':'product','status':'completed','quantity':10,'unit':'PZA','unit_cost':999,'original_unit_cost':'12.123456','organization_context':frozen.model_dump()}
    product={'id':'product','code':'PT-SYNTHETIC','name':'Synthetic finished good','inventory_item_id':item,'base_unit':'PZA'}
    payload=inventory_schemas.FinishedGoodsReceiptCreate(production_order_id=order_id,warehouse_id=wh,quantity=2,received_at=datetime.now(timezone.utc))
    key='receipt-'+uuid4().hex
    value=repo.create_finished_goods_receipt(TENANT,payload,order,product,key,'hash','actor')
    assert value.movement.original_unit_cost==Decimal('12.123456')
    assert value.movement.organization_context==frozen
    assert repo.create_finished_goods_receipt(TENANT,payload,order,product,key,'hash','actor').movement.id==value.movement.id
    assert all(row.production_order_id!=order_id for row in repo.list_finished_goods_receipts(TENANT,allowed_divisions=['division-b']))
    assert any(row.production_order_id==order_id for row in repo.list_finished_goods_receipts(TENANT,allowed_divisions=['division-a']))
    cross={**order,'organization_context':frozen.model_copy(update={'division_ref_id':'division-b'}).model_dump()}
    with pytest.raises(ErclaveError) as exc:repo.create_finished_goods_receipt(TENANT,payload,cross,product,'cross-'+key,'cross','actor')
    assert exc.value.code=='operational_context_mismatch'
    request=inventory_schemas.AvailabilityCheckRequest(division_ref_id='division-a',source={'type':'production_validation','id':'recipe'},items=[{'inventory_item_id':item,'quantity':1,'unit':'PZA'}])
    availability=repo.check_availability(TENANT,request,organization_context=frozen)
    assert availability.available and availability.items[0].original_unit_cost==Decimal('12.123456')
    receipt_scope=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],))
    choices=api.received_stock_context(order_id,receipt_scope,repo)['data']
    assert len(choices)==1 and choices[0]['received_quantity']==Decimal('2')
    assert choices[0]['available_quantity']==Decimal('2') and choices[0]['organization_context']['cost_currency']=='MXN'
    assert api.received_stock_context(order_id,replace(receipt_scope,divisions=(DIVISIONS[1],)),repo)['data']==[]
    reservation=repo.create_reservation(TENANT,inventory_schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=wh,quantity=1,unit='PZA',source={'type':'sales_order','id':'synthetic','line_id':'line'}),'proof-reserve-'+key,'proof','actor',organization_context=frozen)
    choices=api.received_stock_context(order_id,receipt_scope,repo)['data']
    assert choices[0]['received_quantity']==Decimal('2') and choices[0]['available_quantity']==Decimal('1')
    # The exact Production projection is authoritative even if its legacy float differs.
    exact_order={**order,'quantity':10,'original_quantity':'2.999999'}
    with pytest.raises(ValueError,match='finished_goods_receipt_quantity_exceeded'):
        repo.create_finished_goods_receipt(TENANT,payload.model_copy(update={'quantity':1}),exact_order,product,'over-'+key,'over','actor')
    conn.execute(text('update inventory.movements set organization_context=null where tenant_id=:t and id=:id'),{'t':TENANT,'id':value.movement.id})
    with pytest.raises(ErclaveError) as exc:repo.create_finished_goods_receipt(TENANT,payload,order,product,'history-'+key,'history','actor')
    assert exc.value.code=='operational_cost_history_review_required'
