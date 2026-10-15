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
from erclave_common.document_presentation import DocumentPresentationSnapshot
from erclave_common.organization_client import OrganizationAccess,OrganizationClient,resolve_organization_access,get_organization_client
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))

def presentation(context):
    return DocumentPresentationSnapshot.model_validate({
        'division_ref_id':context.division_ref_id,'division_code':'DIV','division_name':'Division',
        'society_ref_id':context.society_ref_id,'society_code':'SOC','society_name':'Society',
        'issuer_ref_id':'issuer-a','issuer_code':'EMI','issuer_legal_name':'Original issuer',
        'template_origin':'division','template_origin_id':context.division_ref_id,
        'template':{'primary_color':'#6106A0','accent_color':'#F557D3','text_color':'#190F34','show_page_number':True}
    })
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
main=importlib.import_module('app.main');repos=importlib.import_module('app.repositories')
Store=importlib.import_module('app.organization_store').OrganizationStore
schemas=importlib.import_module('app.organization_schemas')
api=importlib.import_module('app.organization_api')
order_context=importlib.import_module('app.order_context')
production_api=importlib.import_module('app.api')
sales_source_module=importlib.import_module('app.sales_source')
scoped_resources=importlib.import_module('app.scoped_resources')
TENANT='ten_739ee59d765d5e14818674800d'
DIVISIONS=({'id':'division-a','code':'DIV-A','name':'Division A','society_id':'society-a'},{'id':'division-b','code':'DIV-B','name':'Division B','society_id':'society-b'})
PERMISSIONS=('production.machine.read','production.machine.update','production.product_service.read','production.product_service.update','costing.cost_center.read')
def context():return {'tenant':{'id':TENANT,'status':'active'},'user':{'id':'actor','status':'active'},'scope':{'version':2,'all_divisions':True,'divisions':list(DIVISIONS)},'permissions':list(PERMISSIONS),'active_modules':['admin','production'],'capabilities':{'cost_center_catalog':{'available':False}}}
def access():return resolve_organization_access(context(),TENANT,'production','production.product_service.update')

@pytest.mark.parametrize('field,value,code',[
 ('tenant',{'id':'foreign','status':'active'},'tenant_access_denied'),('user',{'id':'actor','status':'inactive'},'tenant_access_denied'),
 ('active_modules',['admin','accounting'],'module_not_enabled'),('active_modules',['production'],'module_not_enabled'),('permissions',[],'permission_denied'),('scope',{'version':1},'organization_scope_review_required'),
 ('scope',{'version':2,'divisions':[{}]},'assignment_authority_unavailable'),('capabilities',[],'assignment_authority_unavailable')])
def test_assignment_authority_fails_closed(field,value,code):
    data=context();data[field]=value
    with pytest.raises(ErclaveError) as exc:resolve_organization_access(data,TENANT,'production','production.product_service.update')
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
            conn.execute(text("insert into production.machines(id,tenant_id,code,name,machine_type,area_name,available_minutes_per_day) values(:i,:t,:i,'Synthetic machine','general','Legacy text',60)"),{'i':wh,'t':TENANT})
            conn.execute(text("insert into production.product_services(id,tenant_id,code,name,type,base_unit) values(:i,:t,:i,'Synthetic 100% item','service','PZA')"),{'i':item,'t':TENANT})
            yield Store(repos.ProductionRepository(TransactionEngine(conn))),conn,wh,item
        finally:txn.rollback()
    engine.dispose()
class NoCosting:
    def center(self,*args):raise AssertionError('Catalog must not be required when no center is selected')
def save(store,kind,id_,division,payload,key=None,actor=None,client=None):
    schema=schemas.MachineDivisionCommand if kind=='machine' else schemas.ProductServiceDivisionCommand
    return store.save(actor or access(),kind,id_,division,schema(**payload),key or 'test-'+uuid4().hex,'test-correlation',client or NoCosting())

def test_postgres_machine_expansion_immutability_revision_and_scope(local_store):
    store,conn,wh,item=local_store
    assert store.machine(access(),wh)['division_ref_id'] is None
    restricted=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],))
    payload={'division_ref_id':'division-a','expected_revision':0}
    with pytest.raises(ErclaveError) as exc:save(store,'machine',wh,'division-a',payload,actor=restricted)
    assert exc.value.code=='assignment_machine_requires_full_scope'
    key='test-'+uuid4().hex
    first=save(store,'machine',wh,'division-a',payload,key)
    assert first==save(store,'machine',wh,'division-a',payload,key)
    assert conn.execute(text('select area_name from production.machines where tenant_id=:t and id=:i'),{'t':TENANT,'i':wh}).scalar()=='Legacy text'
    with pytest.raises(ErclaveError) as exc:save(store,'machine',wh,'division-b',{'division_ref_id':'division-b','expected_revision':1})
    assert exc.value.code=='assignment_machine_division_locked'
    with pytest.raises(ErclaveError) as exc:save(store,'machine',wh,'division-a',payload)
    assert exc.value.code=='assignment_revision_conflict'
    with pytest.raises(ErclaveError):store.machine(replace(restricted,divisions=(DIVISIONS[1],)),wh)
    with pytest.raises(ErclaveError) as exc:store.machine(replace(access(),tenant_id='foreign'),wh)
    assert exc.value.status_code==404
    assert conn.execute(text("select count(*) from production.audit_events where tenant_id=:t and resource_id=:i and action='organization_assignment.machine'"),{'t':TENANT,'i':wh}).scalar()==1

def test_postgres_shared_item_assignments_optional_center_and_history(local_store):
    store,conn,wh,item=local_store;payload={'expected_revision':0,'status':'active','cost_center_ref_id':None};key='test-'+uuid4().hex
    first=save(store,'product_service',item,'division-a',payload,key)
    assert first==save(store,'product_service',item,'division-a',payload,key)
    save(store,'product_service',item,'division-b',payload)
    assert store.products(access(),item,25,0)['meta']['total']==2
    assert store.products(replace(access(),all_divisions=False,divisions=(DIVISIONS[0],)),item,25,0)['meta']['total']==1
    assert store.eligible(access(),'division-a','%',20,0)['data'][0]['id']==item
    assert store.eligible(access(),'division-a','__',20,0)['data']==[]
    with pytest.raises(ErclaveError) as exc:save(store,'product_service',item,'division-a',{**payload,'status':'inactive'},key)
    assert exc.value.code=='idempotency_key_reused'
    class Center:
        def center(self,a,id_,division):return {'id':id_,'code':'CC-01','name':'Synthetic'}
    changed=save(store,'product_service',item,'division-a',{'expected_revision':1,'cost_center_ref_id':'cc'},client=Center())
    assert changed['revision']==2
    class Down:
        def center(self,*args):raise ErclaveError('assignment_authority_unavailable','unavailable',503)
    with pytest.raises(ErclaveError):save(store,'product_service',item,'division-a',{'expected_revision':2,'cost_center_ref_id':'cc'},client=Down())
    assert store.products(access(),item,25,0,'division-a')['data'][0]['revision']==2
    inactive=save(store,'product_service',item,'division-a',{'expected_revision':2,'status':'inactive','cost_center_ref_id':'cc'},client=Down())
    assert inactive['cost_center_snapshot']==changed['cost_center_snapshot']
    assert store.eligible(access(),'division-a','',20,0)['data']==[]
    assert conn.execute(text('select count(*) from production.product_services where tenant_id=:t and id=:i'),{'t':TENANT,'i':item}).scalar()==1
    assert store.products(access(),item,25,0,'division-a')['data'][0]['revision']==3

def test_confirmed_estimated_cost_is_division_scoped_replayable_and_nullable(local_store):
    store,conn,_,item=local_store
    scope=replace(access(),societies=({'id':'society-a','base_currency':'MXN'},{'id':'society-b','base_currency':'USD'}))
    save(store,'product_service',item,'division-a',{'expected_revision':0},actor=scope)
    save(store,'product_service',item,'division-b',{'expected_revision':0},actor=scope)
    assert store.estimated_cost(scope,item,'division-a') is None
    assert store.estimated_cost(scope,item,'division-b') is None
    command=schemas.ProductServiceEstimatedCostCommand(expected_revision=1,estimated_unit_cost='0',cost_currency='MXN')
    key='test-'+uuid4().hex
    first=store.confirm_estimated_cost(scope,item,'division-a',command,key,'correlation')
    assert first['estimated_unit_cost']=='0.000000' and first['cost_currency']=='MXN' and first['revision']==2
    assert store.confirm_estimated_cost(scope,item,'division-a',command,key,'correlation')==first
    visible=store.estimated_cost(scope,item,'division-a')
    assert visible.estimated_unit_cost==0 and visible.cost_currency=='MXN' and visible.society_ref_id=='society-a' and visible.assignment_revision==2
    changed_society=replace(scope,divisions=({'id':'division-a','code':'DIV-A','name':'Division A','society_id':'society-b'},DIVISIONS[1]))
    assert store.estimated_cost(changed_society,item,'division-a') is None
    changed_currency=replace(scope,societies=({'id':'society-a','base_currency':'CAD'},scope.societies[1]))
    assert store.estimated_cost(changed_currency,item,'division-a') is None
    assert store.estimated_cost(scope,item,'division-b') is None
    assert store.products(scope,item,25,0)['data'][0]['estimated_unit_cost']==0
    with pytest.raises(ErclaveError) as exc:
        store.confirm_estimated_cost(scope,item,'division-a',schemas.ProductServiceEstimatedCostCommand(expected_revision=2,estimated_unit_cost='1',cost_currency='USD'),'test-'+uuid4().hex,'correlation')
    assert exc.value.code=='operational_cost_currency_mismatch'
    with pytest.raises(ErclaveError) as exc:
        store.confirm_estimated_cost(scope,item,'division-a',command,'test-'+uuid4().hex,'correlation')
    assert exc.value.code=='assignment_revision_conflict'
    restricted=replace(scope,all_divisions=False,divisions=(DIVISIONS[1],))
    with pytest.raises(ErclaveError) as exc:store.estimated_cost(restricted,item,'division-a')
    assert exc.value.code=='assignment_division_denied'
    clear=schemas.ProductServiceEstimatedCostCommand(expected_revision=2,estimated_unit_cost=None,cost_currency=None)
    store.confirm_estimated_cost(scope,item,'division-a',clear,'test-'+uuid4().hex,'correlation')
    assert store.estimated_cost(scope,item,'division-a') is None
    with pytest.raises(ValidationError):schemas.ProductServiceEstimatedCostCommand(expected_revision=3)

def test_postgres_downgrade_preserves_assignment_history(local_store):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,wh,item=local_store
    save(store,'product_service',item,'division-a',{'expected_revision':0})
    path=ROOT.parents[1]/'alembic/versions/20260927_0042_production_dimensions.py'
    spec=importlib.util.spec_from_file_location('production_dimension_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Production assignment history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    assert store.products(access(),item,25,0)['meta']['total']==1

def test_api_checks_scope_permissions_payload_and_idempotency():
    class Client:
        data=context()
        def session(self,*args):return self.data
    class Fake:
        def machine(self,*args):return {'machine_id':'machine','division_ref_id':None,'revision':0}
        def save(self,*args):
            if args[1]=='product_service':return {'product_service_id':'product_service','division_ref_id':'division-a','status':'active','cost_center_ref_id':None,'revision':1}
            return {'machine_id':'machine','division_ref_id':'division-a','revision':1}
        def estimated_cost(self,*args):return None
        def confirm_estimated_cost(self,*args):return {'product_service_id':'item','division_ref_id':'division-a','status':'active','revision':2,'estimated_unit_cost':'0.000000','cost_currency':'MXN','cost_society_ref_id':'society-a','cost_confirmed_at':'2026-10-14T00:00:00Z'}
    authority=Client();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'test-assignment'}
        preflight=http.options('/v1/production/product-services/product/division-assignments/division-a',headers={'Origin':'http://127.0.0.1:4173','Access-Control-Request-Method':'PUT','Access-Control-Request-Headers':'content-type,x-tenant-id,x-actor-id,x-correlation-id,idempotency-key,authorization'})
        assert preflight.status_code==200
        assert preflight.headers['access-control-allow-origin']=='http://127.0.0.1:4173'
        assert http.get('/v1/production/organization/divisions?limit=26',headers=headers).status_code==422
        assert http.get('/v1/production/organization/divisions?q=DIV-A',headers=headers).json()['meta']['total']==1
        path='/v1/production/machines/machine/division';payload={'division_ref_id':'division-a','expected_revision':0}
        assert http.patch(path,headers=headers,json={**payload,'society_ref_id':'bad'}).status_code==422
        assert http.patch(path,headers={k:v for k,v in headers.items() if k!='Idempotency-Key'},json=payload).status_code==400
        assert http.patch(path,headers=headers,json=payload).status_code==200
        item_path='/v1/production/product-services/item/division-assignments/division-a'
        assert http.put(item_path,headers=headers,json={'expected_revision':0}).status_code==200
        assert http.put(item_path,headers=headers,json={'expected_revision':0,'division_ref_id':'other'}).status_code==422
        assert http.put(item_path,headers=headers,json={'expected_revision':-1}).status_code==422
        cost_path=item_path+'/estimated-unit-cost'
        assert http.put(cost_path,headers=headers,json={'expected_revision':1}).status_code==422
        assert http.put(cost_path,headers=headers,json={'expected_revision':1,'estimated_unit_cost':None,'cost_currency':None}).status_code==200
        estimate_path='/v1/production/division-product-services/item/estimated-cost?division_id=division-a'
        assert http.get(estimate_path,headers=headers).json()=={'data':None}
        authority.data=context();authority.data['permissions']=['sales.quote.approve'];authority.data['active_modules'].append('sales')
        assert http.get(estimate_path,headers=headers).status_code==200
        assert http.put(cost_path,headers=headers,json={'expected_revision':1,'estimated_unit_cost':'0','cost_currency':'MXN'}).status_code==403
        authority.data=context();authority.data['permissions']=['production.machine.read']
        assert http.get(estimate_path,headers=headers).status_code==403
        assert http.put(item_path,headers=headers,json={'expected_revision':0}).status_code==403
        assert http.get(path,headers=headers).status_code==200
        assert http.patch(path,headers=headers,json=payload).status_code==403
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
    finally:app.dependency_overrides.clear()

@pytest.mark.parametrize('product_type', ['product', 'service'])
def test_postgres_product_types_legacy_values_and_negative_boundaries(local_store, product_type):
    store, conn, machine, product = local_store
    long_id = 'product_' + uuid4().hex
    conn.execute(text("update production.product_services set id=:long_id,type=:type,cost_center='Legacy center',status='pending_approval' where tenant_id=:t and id=:i"), {'long_id':long_id,'type':product_type,'t':TENANT,'i':product})
    division = 'division' + 'x' * 32
    scope = replace(access(), divisions=({'id':division,'code':'DIV-LONG','name':'Long division','society_id':'society'},))
    payload = {'expected_revision':0}
    with pytest.raises(ErclaveError) as exc:save(store,'product_service',long_id,division,payload,actor=scope)
    assert exc.value.code == 'assignment_resource_inactive'
    conn.execute(text("update production.product_services set status='active' where tenant_id=:t and id=:i"), {'t':TENANT,'i':long_id})
    result = save(store,'product_service',long_id,division,payload,actor=scope)
    assert result['cost_center_ref_id'] is None and result['revision'] == 1
    assert conn.execute(text('select cost_center from production.product_services where tenant_id=:t and id=:i'), {'t':TENANT,'i':long_id}).scalar() == 'Legacy center'
    assert store.products(replace(scope,all_divisions=False,divisions=()),long_id,25,0)['data'] == []
    with pytest.raises(ErclaveError) as exc:store.products(replace(scope,tenant_id='foreign'),long_id,25,0)
    assert exc.value.status_code == 404
    with pytest.raises(ErclaveError):store.eligible(replace(scope,all_divisions=False,divisions=()),division,'',20,0)
    # Master state controls eligibility without erasing the saved assignment.
    conn.execute(text("update production.product_services set status='inactive' where tenant_id=:t and id=:i"), {'t':TENANT,'i':long_id})
    assert store.eligible(scope,division,'',20,0)['data'] == []
    assert store.products(scope,long_id,25,0)['meta']['total'] == 1
    conn.execute(text("update production.machines set status='maintenance' where tenant_id=:t and id=:i"), {'t':TENANT,'i':machine})
    with pytest.raises(ErclaveError) as exc:save(store,'machine',machine,division,{'expected_revision':0,'division_ref_id':division},actor=scope)
    assert exc.value.code == 'assignment_resource_inactive'


def test_creation_context_binds_actor_capture_allocation_and_recovery(local_store):
    from types import SimpleNamespace
    from erclave_common.operational_context import OperationalContext
    store,conn,machine,item=local_store;repo=store.repository;order='ctx_'+uuid4().hex[:26]
    snapshot=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='A',division_name='Division A',cost_currency='MXN')
    preview=SimpleNamespace(rows=[SimpleNamespace(resource_type='material',resource_ref_id='material',unit='PZA',allocations=[{'warehouse_id':'warehouse-a','quantity':2}])])
    repo.prepare_creation_context(TENANT,order,'actor','a'*64,snapshot,preview)
    repo.prepare_creation_context(TENANT,order,'actor','a'*64,snapshot,preview)
    proof=repo.creation_context(TENANT,order,'actor','material:0')
    assert proof['organization_context']==snapshot.model_dump()
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    migration_path=ROOT.parents[1]/'alembic/versions/20261007_0050_production_context.py'
    spec=importlib.util.spec_from_file_location('production_context_migration',migration_path)
    migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Production context history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    with pytest.raises(DBAPIError):
        with conn.begin_nested():
            conn.execute(text("update production.order_creation_contexts set organization_context=jsonb_set(organization_context,'{cost_currency}','null') where tenant_id=:t and order_id=:id"),{'t':TENANT,'id':order})

    assert proof['allocation']=={'line_id':'material:0','inventory_item_id':'material','warehouse_id':'warehouse-a','quantity':'2','unit':'PZA'}
    assert repo.creation_context('foreign',order,'actor','material:0') is None
    for actor,hash_ in [('another','a'*64),('actor','b'*64)]:
        with pytest.raises(ErclaveError) as exc:repo.prepare_creation_context(TENANT,order,actor,hash_,snapshot,preview)
        assert exc.value.code=='idempotency_key_reused'
    with pytest.raises(ErclaveError) as exc:repo.creation_context(TENANT,order,'another','material:0')
    assert exc.value.code=='permission_denied'
    with pytest.raises(ErclaveError):repo.creation_context(TENANT,order,'actor','other:0')
    repo.record_failed_creation(TENANT,order,'Synthetic','actor','test_failure')
    with pytest.raises(ErclaveError) as exc:repo.creation_context(TENANT,order,'actor','material:0')
    assert exc.value.code=='production_creation_attempt_failed'


def test_scoped_production_reads_and_commands_deny_before_effects(local_store,monkeypatch):
    from erclave_common.operational_context import OperationalContext
    store,conn,machine,item=local_store;repo=store.repository
    recipe=conn.execute(text('select id,recipe_id from production.recipe_versions where tenant_id=:t limit 1'),{'t':TENANT}).mappings().one()
    product=conn.execute(text('select product_service_id from production.recipes where tenant_id=:t and id=:id'),{'t':TENANT,'id':recipe['recipe_id']}).scalar()
    snapshot=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='A',division_name='Division A',cost_currency='MXN')
    order='scoped_'+uuid4().hex[:25]
    conn.execute(text("""insert into production.production_orders(id,tenant_id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,responsible_name_snapshot,planned_cost,recipe_snapshot,resource_validation_snapshot,validated_at,created_by,organization_context) values(:id,:t,:id,:product,:recipe,:version,1,'H87','released','Synthetic',0,'{}','{}',now(),'actor',cast(:ctx as jsonb))"""),{'id':order,'t':TENANT,'product':product,'recipe':recipe['recipe_id'],'version':recipe['id'],'ctx':snapshot.model_dump_json()})
    assert repo.get_order(TENANT,order).organization_context==snapshot
    scope=replace(access(),all_divisions=False,divisions=(DIVISIONS[1],))
    assert order not in [row.id for row in repo.list_orders(TENANT,scope=scope)]
    monkeypatch.setattr(order_context,'production_access',lambda *args:scope)
    main.app.dependency_overrides[repos.get_production_repository]=lambda:repo
    try:
        http=TestClient(main.app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'negative-'+uuid4().hex}
        assert http.get('/v1/production/orders/'+order,headers=headers).status_code==403
        assert http.post('/v1/production/orders/'+order+'/issue-materials',headers=headers,json={}).status_code==403
        assert http.patch('/v1/production/orders/'+order+'/status',headers=headers,json={'status':'in_progress','reason':'Synthetic attempt'}).status_code==403
        assert http.patch('/v1/production/orders/'+order+'/resources/missing',headers=headers,json={'actual_quantity':1}).status_code==403
        assert conn.execute(text('select status from production.production_orders where tenant_id=:t and id=:id'),{'t':TENANT,'id':order}).scalar()=='released'
        scope=replace(scope,divisions=(DIVISIONS[0],))
        assert http.get('/v1/production/orders/'+order,headers=headers).status_code==200
    finally:main.app.dependency_overrides.clear()


def test_production_resource_context_rejects_unassigned_product_and_cross_division_machine(local_store):
    from types import SimpleNamespace
    from erclave_common.operational_context import OperationalContext
    store,conn,machine,item=local_store;repo=store.repository
    recipe=conn.execute(text('select id,product_service_id from production.recipes where tenant_id=:t limit 1'),{'t':TENANT}).mappings().one()
    context=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='A',division_name='A',cost_currency='MXN')
    version=SimpleNamespace(recipe_id=recipe['id'],resources=[SimpleNamespace(resource_type='machine',resource_ref_id=machine)])
    with pytest.raises(ErclaveError):repo.validate_context_resources(conn,TENANT,version,context)
    store.save(access(),'product_service',recipe['product_service_id'],'division-a',schemas.ProductServiceDivisionCommand(expected_revision=0),'context-product-'+uuid4().hex,'test',NoCosting())
    store.save(access(),'machine',machine,'division-a',schemas.MachineDivisionCommand(division_ref_id='division-a',expected_revision=0),'context-machine-'+uuid4().hex,'test',NoCosting())
    repo.validate_context_resources(conn,TENANT,version,context)
    with pytest.raises(ErclaveError) as exc:repo.validate_context_resources(conn,TENANT,version,None)
    assert exc.value.code=='operational_context_required'
    with pytest.raises(ErclaveError):repo.validate_context_resources(conn,TENANT,version,context.model_copy(update={'division_ref_id':'division-b'}))


# CC-10: monetary confirmation is explicit and shared machines keep one capacity pool.
from datetime import date, datetime, timezone
from decimal import Decimal
from pydantic import ValidationError
machine_capacity=importlib.import_module('app.machine_capacity')
production_schemas=importlib.import_module('app.schemas')

def tariff_scope():
    return replace(access(), societies=({'id':'society-a','base_currency':'MXN'}, {'id':'society-b','base_currency':'USD'}))

@pytest.mark.parametrize('amount', ['0','0.000001','999999999999.999999'])
def test_machine_tariff_decimal_precision_and_zero(amount):
    value=production_schemas.MachineUpdateRequest(cost_per_minute=amount,cost_currency='MXN')
    assert value.cost_per_minute==Decimal(amount)
    assert value.model_dump(mode='json')['cost_per_minute']==amount

@pytest.mark.parametrize('amount', ['-1','0.0000001','1000000000000','NaN','Infinity'])
def test_machine_tariff_invalid_decimal_rejected(amount):
    with pytest.raises(ValidationError):production_schemas.MachineUpdateRequest(cost_per_minute=amount)

def test_machine_tariff_confirmation_never_infers_currency_and_rechecks_scope():
    payload=production_schemas.MachineUpdateRequest(cost_per_minute='0.123456',cost_currency='MXN')
    before={'division_ref_id':'division-a','cost_currency':None}
    result=machine_capacity.confirmed_tariff_update(before,payload,tariff_scope())
    assert result['cost_society_ref_id']=='society-a'
    assert result['cost_confirmed_at'].tzinfo is not None
    assert machine_capacity.confirmed_tariff_update(before,production_schemas.MachineUpdateRequest(cost_per_minute=1),tariff_scope())=={}
    scenarios=[({**before,'division_ref_id':None},tariff_scope(),'operational_context_required'),
      (before,replace(tariff_scope(),all_divisions=False,divisions=(DIVISIONS[1],)),'organization_division_forbidden'),
      (before,replace(tariff_scope(),societies=({'id':'society-a','base_currency':'USD'},)),'operational_cost_currency_mismatch')]
    for row,scope,code in scenarios:
        with pytest.raises(ErclaveError) as exc:machine_capacity.confirmed_tariff_update(row,payload,scope)
        if code=='organization_division_forbidden':assert exc.value.status_code==403
        else:assert exc.value.code==code
    with pytest.raises(ErclaveError) as exc:
        machine_capacity.confirmed_tariff_update({**before,'cost_currency':'MXN'},production_schemas.MachineUpdateRequest(cost_per_minute=2),tariff_scope())
    assert exc.value.code=='machine_tariff_confirmation_required'
    with pytest.raises(ValidationError):production_schemas.MachineUpdateRequest(cost_currency='MXN')
    with pytest.raises(ValidationError):production_schemas.MachineUpdateRequest(cost_per_minute=1,cost_society_ref_id='forged')


def test_postgres_machine_tariff_confirmation_replay_history_and_capacity(local_store):
    store,conn,machine,item=local_store;repo=store.repository;scope=tariff_scope()
    save(store,'machine',machine,'division-a',{'expected_revision':0,'division_ref_id':'division-a'})
    assert repo.get_machine(TENANT,machine).cost_currency is None
    assert machine not in [value.id for value in repo.list_machines(TENANT)]
    lookup=machine_capacity.MachineCapacityStore(repo)
    day=date(2026,10,7)
    assert lookup.eligible(scope,'division-a',day,'',25,0,machine)['data']==[]
    payload=production_schemas.MachineUpdateRequest(cost_per_minute='0.000001',cost_currency='MXN')
    key='tariff-'+uuid4().hex
    first=repo.update_machine(TENANT,machine,payload,key,'a'*64,'actor',lambda:scope)
    assert first.cost_per_minute==Decimal('0.000001') and first.cost_currency=='MXN'
    assert first==repo.update_machine(TENANT,machine,payload,key,'a'*64,'actor',lambda:scope)
    forbidden=replace(scope,all_divisions=False,divisions=(DIVISIONS[1],))
    with pytest.raises(ErclaveError):repo.update_machine(TENANT,machine,payload,key,'a'*64,'actor',lambda:forbidden)
    changed=replace(scope,societies=({'id':'society-a','base_currency':'USD'},))
    assert first==repo.update_machine(TENANT,machine,payload,key,'a'*64,'actor',lambda:changed)
    with pytest.raises(ErclaveError):repo.update_machine(TENANT,machine,payload,'new-'+uuid4().hex,'a'*64,'actor',lambda:changed)
    assert lookup.eligible(changed,'division-a',day,'',25,0,machine)['data']==[]
    result=lookup.eligible(scope,'division-a',day,'',25,0,machine)['data'][0]
    assert result['available_minutes']==Decimal('60') and result['capacity_pool_key']==machine
    order=conn.execute(text('select id from production.production_orders where tenant_id=:t limit 1'),{'t':TENANT}).scalar_one()
    conn.execute(text("insert into production.capacity_commitments(id,tenant_id,production_order_id,resource_type,resource_ref_id,planned_date,quantity_minutes) values(:id,:t,:o,'machine',:m,:day,25)"),{'id':'cap_'+uuid4().hex[:25],'t':TENANT,'o':order,'m':machine,'day':day})
    result=lookup.eligible(scope,'division-a',day,'',25,0,machine)['data'][0]
    assert result['committed_minutes']==25 and result['available_minutes']==35
    # A restricted caller sees the same physical pool, including legacy order commitments.
    restricted=replace(scope,all_divisions=False,divisions=(DIVISIONS[0],))
    assert lookup.eligible(restricted,'division-a',day,'',25,0,machine)['data'][0]['available_minutes']==35
    assert lookup.eligible(scope,'division-b',day,'',25,0,machine)['data']==[]
    assert lookup.eligible(scope,'division-a',date(2026,10,10),'',25,0,machine)['data'][0]['available_minutes']==0
    assert repo.list_machines(TENANT,scope=forbidden)==[] or machine not in [m.id for m in repo.list_machines(TENANT,scope=forbidden)]
    assert repo.get_machine('foreign',machine) is None
    assert conn.execute(text("select count(*) from production.audit_events where tenant_id=:t and resource_id=:i and action='machine.update'"),{'t':TENANT,'i':machine}).scalar()==1


def test_machine_capacity_api_requires_scope_permission_and_date(monkeypatch):
    class Authority:
        data=context()
        def session(self,*args):return self.data
    authority=Authority()
    calls=[]
    def eligible(self,scope,division,day,q,limit,offset,resource_id):
        scope.division(division)
        calls.append((scope.tenant_id,division,day))
        return {'data':[],'meta':{'total':0,'limit':limit,'offset':offset,'capacity_scope':'physical_machine','commitments_included':True}}
    monkeypatch.setattr(machine_capacity.MachineCapacityStore,'eligible',eligible)
    main.app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    main.app.dependency_overrides[get_organization_client]=lambda:authority
    main.app.dependency_overrides[repos.get_production_repository]=lambda:object()
    try:
        http=TestClient(main.app)
        path='/v1/production/division-machines?division_id=division-a&planned_date=2026-10-07'
        headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic'}
        assert http.get(path,headers=headers).status_code==200
        assert calls==[(TENANT,'division-a',date(2026,10,7))]
        assert http.get(path+'&limit=26',headers=headers).status_code==422
        assert http.get('/v1/production/division-machines?division_id=division-a',headers=headers).status_code==422
        authority.data={**context(),'scope':{'version':2,'all_divisions':False,'divisions':[DIVISIONS[1]]}}
        assert http.get(path,headers=headers).status_code==403
        authority.data={**context(),'permissions':[]}
        assert http.get(path,headers=headers).status_code==403
        authority.data=context()
        assert http.get(path,headers={**headers,'X-Tenant-Id':'foreign'}).status_code==403
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
        assert len(calls)==1
    finally:main.app.dependency_overrides.clear()


def test_machine_legacy_hash_requires_lossless_decimal():
    assert production_api.machine_legacy_fingerprint(production_schemas.MachineUpdateRequest(cost_per_minute='0.123456'),{'machine_id':'m'})
    assert production_api.machine_legacy_fingerprint(production_schemas.MachineUpdateRequest(cost_per_minute='999999999999.999999'),{'machine_id':'m'}) is None
    assert production_api.machine_legacy_fingerprint(production_schemas.MachineUpdateRequest(cost_per_minute='1',cost_currency='MXN'),{'machine_id':'m'}) is None


def test_postgres_machine_replays_original_schema_without_hash_collisions(local_store):
    import hashlib,json
    store,conn,machine,item=local_store;repo=store.repository
    payload=production_schemas.MachineUpdateRequest(cost_per_minute='0.123456')
    path={'machine_id':machine}
    old_body={'name':None,'machine_type':None,'area_ref_id':None,'area_name':None,'available_minutes_per_day':None,'cost_per_minute':0.123456,'status':None}
    old_hash=hashlib.sha256(json.dumps({'path':path,'body':old_body},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    assert old_hash==production_api.machine_legacy_fingerprint(payload,path)
    key='legacy-tariff-'+uuid4().hex
    original=repo.get_machine(TENANT,machine).model_dump(mode='json')
    original={k:v for k,v in original.items() if k not in {'division_ref_id','cost_currency','cost_society_ref_id','cost_confirmed_at'}}
    original['cost_per_minute']=0.123456
    repo._claim_idempotency(conn,TENANT,'machine.update',key,old_hash,'actor')
    repo._complete_idempotency(conn,TENANT,'machine.update',key,original,200)
    replay=repo.update_machine(TENANT,machine,payload,key,production_api.request_fingerprint(payload,path),'actor',legacy_request_hash=old_hash)
    assert replay.cost_per_minute==Decimal('0.123456') and replay.cost_currency is None
    assert repo.get_machine(TENANT,machine).cost_per_minute==0
    assert conn.execute(text("select response_payload from production.idempotency_records where tenant_id=:t and operation='machine.update' and idempotency_key=:k"),{'t':TENANT,'k':key}).scalar()==original
    for amount in ['0.123457','999999999999.999999']:
        other=production_schemas.MachineUpdateRequest(cost_per_minute=amount)
        with pytest.raises(ErclaveError) as exc:
            repo.update_machine(TENANT,machine,other,key,production_api.request_fingerprint(other,path),'actor',legacy_request_hash=old_hash)
        assert exc.value.code=='idempotency_key_reused'
    with pytest.raises(ErclaveError) as exc:
        repo.update_machine(TENANT,machine,payload,key,production_api.request_fingerprint(payload,path),'other',legacy_request_hash=old_hash)
    assert exc.value.code=='idempotency_actor_mismatch'
    # New responses serialize decimals as strings: never grant the legacy hash exception.
    fresh='decimal-tariff-'+uuid4().hex
    repo._claim_idempotency(conn,TENANT,'machine.update',fresh,old_hash,'actor')
    repo._complete_idempotency(conn,TENANT,'machine.update',fresh,{**original,'cost_per_minute':'0.123456'},200)
    with pytest.raises(ErclaveError) as exc:
        repo.update_machine(TENANT,machine,payload,fresh,production_api.request_fingerprint(payload,path),'actor',legacy_request_hash=old_hash)
    assert exc.value.code=='idempotency_key_reused'


def test_postgres_machine_legacy_create_and_metadata_only_replay(local_store):
    store,conn,machine,item=local_store;repo=store.repository
    original=repo.get_machine(TENANT,machine).model_dump(mode='json')
    original={k:v for k,v in original.items() if k not in {'division_ref_id','cost_currency','cost_society_ref_id','cost_confirmed_at'}}
    original['cost_per_minute']=0.0
    create=production_schemas.MachineCreateRequest(code='old-code',name='Legacy',machine_type='general',area_ref_id='area',area_name='Area',available_minutes_per_day=60,cost_per_minute=0)
    key='legacy-create-'+uuid4().hex;old_hash=production_api.machine_legacy_fingerprint(create)
    repo._claim_idempotency(conn,TENANT,'machine.create',key,old_hash,'actor')
    repo._complete_idempotency(conn,TENANT,'machine.create',key,original,201)
    replay=repo.create_machine(TENANT,create,key,production_api.request_fingerprint(create),'actor',legacy_request_hash=old_hash)
    assert replay.id==machine and replay.cost_per_minute==0
    payload=production_schemas.MachineUpdateRequest(name='New name')
    path={'machine_id':machine};old_hash=production_api.machine_legacy_fingerprint(payload,path);key='legacy-name-'+uuid4().hex
    repo._claim_idempotency(conn,TENANT,'machine.update',key,old_hash,'actor')
    repo._complete_idempotency(conn,TENANT,'machine.update',key,{**original,'name':'New name'},200)
    replay=repo.update_machine(TENANT,machine,payload,key,production_api.request_fingerprint(payload,path),'actor',legacy_request_hash=old_hash)
    assert replay.name=='New name'
    assert repo.get_machine(TENANT,machine).name!='New name'


# CC-11 manual production: fixtures never leave the authorized tenant transaction.
@pytest.fixture
def scoped_recipe(local_store):
    from erclave_common.operational_context import OperationalContext
    store,conn,machine,product=local_store;repo=store.repository
    conn.execute(text("update production.product_services set type='product' where tenant_id=:t and id=:p"),{'t':TENANT,'p':product})
    for division in ['division-a','division-b']:
        save(store,'product_service',product,division,{'expected_revision':0})
    value=production_schemas.RecipeCreateRequest(product_service_id=product,code='recipe-'+uuid4().hex,name='Scoped recipe',base_quantity=1,base_unit='PZA',resources=[{'resource_type':'labor','resource_ref_id':'shared-position','resource_code':'LAB','resource_name':'Shared labor','quantity':60,'unit':'MIN','unit_cost':999}],stages=[{'labor_area_ref_id':'synthetic-area','labor_area_name':'Area','name':'Phase','sort_order':1,'weight_percent':100}])
    recipe=repo.create_recipe(TENANT,value,'recipe-'+uuid4().hex,'r'*64,'actor');version=recipe.versions[0]
    conn.execute(text("update production.recipe_versions set status='approved' where tenant_id=:t and id=:v"),{'t':TENANT,'v':version.id})
    conn.execute(text('update production.recipes set current_version_id=:v where tenant_id=:t and id=:r'),{'t':TENANT,'v':version.id,'r':recipe.id})
    conn.execute(text('update production.product_services set current_recipe_version_id=:v where tenant_id=:t and id=:p'),{'t':TENANT,'v':version.id,'p':product})
    context=OperationalContext(division_ref_id='division-a',society_ref_id='society-a',division_code='A',division_name='A',cost_currency='MXN')
    payload=production_schemas.ProductionOrderCreateRequest(division_ref_id='division-a',recipe_version_id=version.id,quantity=1,unit='PZA',planned_start_date=date(2099,1,5),responsible_worker_id='shared-worker',stage_assignments=[{'recipe_stage_id':version.stages[0].id,'responsible_worker_id':'shared-worker'}],code='OP-'+uuid4().hex)
    payload=payload.model_copy(update={'responsible_name':'Shared worker','stage_assignments':[payload.stage_assignments[0].model_copy(update={'responsible_name':'Shared worker'})]})
    obs=production_schemas.ResourceAvailabilityInput(resource_ref_id='shared-position',resource_type='labor',available_quantity=90,unit='MIN',original_unit_cost=Decimal('1')/60,cost_currency='MXN',eligible_worker_ids=['shared-worker'],minutes_per_worker=90,source='hr.division_production_capacity')
    return repo,conn,recipe,version,payload,context,obs


def test_scoped_release_consumes_global_worker_capacity_and_frozen_decimal(scoped_recipe):
    repo,conn,recipe,version,payload,context,obs=scoped_recipe
    preview=repo.preview_resources(TENANT,payload,[obs],context)
    assert preview.can_release and preview.original_planned_cost==Decimal('1.000000')
    assert preview.rows[0].daily_allocations[0].worker_allocations==[{'worker_ref_id':'shared-worker','quantity_minutes':'60.000000'}]
    order_id='scoped-'+uuid4().hex[:25];key='scoped-'+uuid4().hex
    order=repo.create_order(TENANT,payload,[obs],order_id,{},key,production_api.request_fingerprint(payload),'actor',context,presentation_snapshot=presentation(context))
    assert order.organization_context==context and order.original_planned_cost==Decimal('1.000000')
    assert order.presentation_snapshot.issuer_legal_name=='Original issuer'
    # A second PostgreSQL transaction cannot claim this physical worker/day, regardless of Division.
    with conn.engine.connect() as competing:
        key_worker=f'production:{TENANT}:worker:shared-worker:{payload.planned_start_date}'
        assert competing.execute(text('select pg_try_advisory_xact_lock(hashtextextended(:k,0))'),{'k':key_worker}).scalar() is False
    with pytest.raises(ErclaveError) as exc:
        repo.preview_resources(TENANT,payload.model_copy(update={'division_ref_id':None}),[obs.model_copy(update={'unit_cost':0.5})])
    assert exc.value.code=='operational_context_required'
    assert order.resources[0].original_unit_cost==Decimal('1')/60
    assert conn.execute(text('select quantity_minutes from production.labor_worker_commitments where tenant_id=:t and production_order_id=:o'),{'t':TENANT,'o':order_id}).scalar()==60
    other=context.model_copy(update={'division_ref_id':'division-b','society_ref_id':'society-b','cost_currency':'USD'})
    other_obs=obs.model_copy(update={'cost_currency':'USD'})
    second=repo.preview_resources(TENANT,payload.model_copy(update={'division_ref_id':'division-b'}),[other_obs],other)
    assert not second.can_release and second.rows[0].available_quantity==30
    with pytest.raises(ValueError,match='resources_unavailable'):
        repo.create_order(TENANT,payload.model_copy(update={'division_ref_id':'division-b','code':'second-'+uuid4().hex}),[other_obs],'another-'+uuid4().hex[:24],{},'second-'+uuid4().hex,'s'*64,'actor',other)
    updated=repo.update_order_resource_actual(TENANT,order_id,order.resources[0].id,production_schemas.ProductionOrderResourceUpdateRequest(actual_quantity=60),'actual-'+uuid4().hex,'c'*64,'actor')
    assert updated.original_actual_cost==Decimal('1.000000')
    repo.update_order_status(TENANT,order_id,production_schemas.ProductionOrderStatusRequest(status='cancelled',reason='Synthetic test'),'cancel-'+uuid4().hex,'d'*64,'actor')
    assert conn.execute(text('select status from production.labor_worker_commitments where tenant_id=:t and production_order_id=:o'),{'t':TENANT,'o':order_id}).scalar()=='released'
    assert repo.preview_resources(TENANT,payload,[other_obs],other).can_release
    assert repo.division_recipes(tariff_scope(),'division-a','Scoped',25,0)['data'][0].id==recipe.id
    with pytest.raises(ErclaveError):repo.division_recipes(replace(tariff_scope(),all_divisions=False,divisions=(DIVISIONS[1],)),'division-a','',25,0)


def test_scoped_capacity_rejects_unconfirmed_and_legacy_overlap(scoped_recipe):
    repo,conn,recipe,version,payload,context,obs=scoped_recipe
    for rows in [[],[obs.model_copy(update={'cost_currency':'USD'})]]:
        with pytest.raises(ErclaveError):repo.preview_resources(TENANT,payload,rows,context)
    legacy=repo.create_order(TENANT,payload.model_copy(update={'division_ref_id':None}),[obs.model_copy(update={'unit_cost':0.5})],'legacy-'+uuid4().hex[:25],{},'legacy-'+uuid4().hex,'e'*64,'actor')
    blocked=repo.preview_resources(TENANT,payload,[obs],context)
    assert not blocked.can_release and 'production_legacy_labor_capacity_review_required' in blocked.blockers
    with pytest.raises(ErclaveError):repo.preview_resources(TENANT,payload,[obs],context.model_copy(update={'division_ref_id':'unassigned'}))


def test_global_locks_are_worker_date_without_division():
    from types import SimpleNamespace
    scoped=scoped_resources
    class Connection:
        keys=[]
        def execute(self,sql,params):self.keys.append(params['key'])
    conn=Connection();day=date(2099,1,5)
    obs=production_schemas.ResourceAvailabilityInput(resource_ref_id='position',resource_type='labor',available_quantity=60,unit='MIN',source='hr',eligible_worker_ids=['shared-worker'])
    scoped.lock_resources(conn,TENANT,SimpleNamespace(resources=[]),[obs],[day])
    assert f'production:{TENANT}:worker:shared-worker:{day}' in conn.keys
    assert f'production:{TENANT}:labor-capacity:{day}' in conn.keys
    assert conn.keys==sorted(set(conn.keys))


def test_legacy_creation_fingerprint_unchanged_when_division_omitted():
    import hashlib,json
    value=production_schemas.ResourceValidationRequest(recipe_version_id='version',quantity=1,unit='PZA')
    body=value.model_dump(mode='json');body.pop('division_ref_id')
    digest=hashlib.sha256(json.dumps({'path':{},'body':body},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    assert production_api.request_fingerprint(value)==digest
    assert production_api.request_fingerprint(value.model_copy(update={'division_ref_id':'division-a'}))!=digest


def test_scoped_creation_api_replay_precedes_external_effects_and_rechecks_scope(scoped_recipe,monkeypatch):
    from contextlib import nullcontext
    import erclave_common.document_presentation as document_presentation
    repo,conn,recipe,version,payload,context,obs=scoped_recipe
    repo.material_command_lock=lambda *args:nullcontext()
    calls=[]
    class Workers:
        def eligible(self,*args,**kwargs):calls.append('workers');assert kwargs['division_id']=='division-a';return [{'id':'shared-worker','full_name':'Shared','labor_position_id':'shared-position'}]
    class Authority:
        def observations(self,*args,**kwargs):calls.append('observations');assert kwargs['organization_context']==context;return [obs]
        def rollback_creation(self,*args):calls.append('rollback')
    monkeypatch.setattr(production_api,'manual_context',lambda *args:context)
    monkeypatch.setattr(document_presentation,'resolve_document_presentation',lambda *args:presentation(context))
    scope=tariff_scope()
    monkeypatch.setattr(order_context,'production_access',lambda *args:scope)
    main.app.dependency_overrides[repos.get_production_repository]=lambda:repo
    main.app.dependency_overrides[production_api.get_hr_worker_client]=lambda:Workers()
    main.app.dependency_overrides[production_api.get_resource_authority_client]=lambda:Authority()
    main.app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='demo')
    try:
        http=TestClient(main.app);headers={'X-Tenant-Id':TENANT,'X-Actor-Id':'actor','Idempotency-Key':'release-'+uuid4().hex}
        body=payload.model_dump(mode='json')
        response=http.post('/v1/production/orders',headers=headers,json=body)
        assert response.status_code==201,response.text
        first=response.json();assert first['data']['original_planned_cost']=='1.000000'
        assert calls==['workers','observations']
        replay=http.post('/v1/production/orders',headers=headers,json=body)
        assert replay.status_code==201 and replay.json()==first and calls==['workers','observations']
        changed=http.post('/v1/production/orders',headers=headers,json={**body,'quantity':2})
        assert changed.status_code==409 and changed.json()['error']['code']=='idempotency_key_reused'
        scope=replace(tariff_scope(),all_divisions=False,divisions=(DIVISIONS[1],))
        assert http.post('/v1/production/orders',headers=headers,json=body).status_code==403
        assert calls==['workers','observations']
        forged=http.post('/v1/production/orders',headers={**headers,'Idempotency-Key':'source-'+uuid4().hex},json={**body,'source_type':'sales_order','source_id':'unproven','source_line_id':'line'})
        assert forged.status_code==409 and calls==['workers','observations']
    finally:main.app.dependency_overrides.clear()


def test_scoped_creation_material_proof_precedes_reserve_and_failure_compensates(scoped_recipe,monkeypatch):
    from contextlib import nullcontext
    import erclave_common.document_presentation as document_presentation
    repo,conn,recipe,version,payload,context,obs=scoped_recipe
    conn.execute(text("insert into production.recipe_resources(id,tenant_id,recipe_version_id,resource_type,resource_ref_id,resource_code,resource_name,quantity,unit,unit_cost,total_cost,sort_order) values(:id,:t,:v,'material','synthetic-material','MAT','Material',1,'PZA',0,0,2)"),{'id':'rr_'+uuid4().hex[:25],'t':TENANT,'v':version.id})
    material=production_schemas.ResourceAvailabilityInput(resource_ref_id='synthetic-material',resource_type='material',available_quantity=1,unit='PZA',original_unit_cost='0.123456',cost_currency='MXN',source='inventory',allocations=[{'warehouse_id':'warehouse-a','quantity':1}])
    repo.material_command_lock=lambda *args:nullcontext();calls=[]
    class Workers:
        def eligible(self,*args,**kwargs):return [{'id':'shared-worker','full_name':'Shared','labor_position_id':'shared-position'}]
    class Authority:
        def observations(self,*args,**kwargs):return [obs,material]
        def reserve(self,tenant,id_,row,*args):
            proof=repo.creation_context(tenant,id_,'actor','synthetic-material:0')
            assert proof['organization_context']==context.model_dump()
            assert proof['allocation']=={'line_id':'synthetic-material:0','inventory_item_id':'synthetic-material','warehouse_id':'warehouse-a','quantity':'1','unit':'PZA'}
            calls.append(('reserve',id_))
            raise ErclaveError('synthetic_partial_failure','Simulated timeout after reservation.',status_code=503)
        def rollback_creation(self,tenant,id_,authorization):
            assert repo.failed_creation(tenant,id_,'actor')['status']=='pending'
            calls.append(('rollback',id_))
    monkeypatch.setattr(production_api,'manual_context',lambda *args:context)
    monkeypatch.setattr(document_presentation,'resolve_document_presentation',lambda *args:presentation(context))
    main.app.dependency_overrides[repos.get_production_repository]=lambda:repo
    main.app.dependency_overrides[production_api.get_hr_worker_client]=lambda:Workers()
    main.app.dependency_overrides[production_api.get_resource_authority_client]=lambda:Authority()
    main.app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='demo')
    try:
        http=TestClient(main.app);headers={'X-Tenant-Id':TENANT,'X-Actor-Id':'actor','Idempotency-Key':'failure-'+uuid4().hex}
        body=payload.model_dump(mode='json')
        response=http.post('/v1/production/orders',headers=headers,json=body)
        assert response.status_code==503,response.text
        assert [c[0] for c in calls]==['reserve','rollback']
        attempt=calls[0][1]
        assert repo.get_order(TENANT,attempt) is None and repo.failed_creation(TENANT,attempt,'actor')['status']=='recovered'
        with pytest.raises(ErclaveError):repo.creation_context(TENANT,attempt,'actor','synthetic-material:0')
        replay=http.post('/v1/production/orders',headers=headers,json=body)
        assert replay.status_code==409 and len(calls)==2
    finally:main.app.dependency_overrides.clear()


def test_scoped_lifecycle_revalidates_allocated_worker_and_preserves_finished_cost(scoped_recipe,monkeypatch):
    from contextlib import nullcontext
    repo,conn,recipe,version,payload,context,obs=scoped_recipe
    order_id='life-'+uuid4().hex[:25]
    order=repo.create_order(TENANT,payload,[obs],order_id,{},'life-'+uuid4().hex,'f'*64,'actor',context,presentation_snapshot=presentation(context))
    repo.material_command_lock=lambda *args:nullcontext()
    class Workers:
        position='wrong-position'
        def eligible(self,*args,**kwargs):assert kwargs['division_id']=='division-a';return [{'id':'shared-worker','full_name':'Shared','labor_position_id':self.position}]
    workers=Workers()
    monkeypatch.setattr(order_context,'production_access',lambda *args:tariff_scope())
    main.app.dependency_overrides[repos.get_production_repository]=lambda:repo
    main.app.dependency_overrides[production_api.get_hr_worker_client]=lambda:workers
    main.app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='demo')
    try:
        http=TestClient(main.app);headers={'X-Tenant-Id':TENANT,'X-Actor-Id':'actor','Idempotency-Key':'start-'+uuid4().hex}
        path='/v1/production/orders/'+order_id+'/status'
        body={'status':'in_progress','reason':'Synthetic execution'}
        rejected=http.patch(path,headers=headers,json=body)
        assert rejected.status_code==409 and rejected.json()['error']['code']=='production_execution_worker_not_eligible'
        assert repo.get_order(TENANT,order_id).status=='released'
        workers.position='shared-position'
        started=http.patch(path,headers=headers,json=body)
        assert started.status_code==200,started.text
        resource=repo.get_order(TENANT,order_id).resources[0]
        repo.update_order_resource_actual(TENANT,order_id,resource.id,production_schemas.ProductionOrderResourceUpdateRequest(actual_quantity=60),'cost-'+uuid4().hex,'h'*64,'actor')
        paused=http.patch(path,headers={**headers,'Idempotency-Key':'pause-'+uuid4().hex},json={'status':'paused','reason':'Synthetic pause'})
        assert paused.status_code==200,paused.text
        workers.position='wrong-position'
        assert http.patch(path,headers={**headers,'Idempotency-Key':'resume-'+uuid4().hex},json=body).status_code==409
        workers.position='shared-position'
        assert http.patch(path,headers={**headers,'Idempotency-Key':'resume-'+uuid4().hex},json=body).status_code==200
        repo.update_order_stage(TENANT,order.stages[0].id,production_schemas.OrderStageUpdateRequest(status='completed',progress_percent=100),'stage-'+uuid4().hex,'i'*64,'actor')
        completed=http.patch(path,headers={**headers,'Idempotency-Key':'complete-'+uuid4().hex},json={'status':'completed','reason':'Synthetic completion'})
        assert completed.status_code==200,completed.text
        result=repo.get_order(TENANT,order_id)
        assert result.original_actual_cost==Decimal('1.000000')
        candidate=production_api.finished_goods_candidate(repo,TENANT,result)
        assert candidate.order.organization_context==context and candidate.order.original_unit_cost==Decimal('1.000000')
        assert conn.execute(text('select status from production.labor_worker_commitments where tenant_id=:t and production_order_id=:o'),{'t':TENANT,'o':order_id}).scalar()=='completed'
    finally:main.app.dependency_overrides.clear()

@pytest.fixture
def sales_conversion(scoped_recipe,monkeypatch):
    from contextlib import nullcontext
    import erclave_common.document_presentation as document_presentation
    source_module=sales_source_module
    repo,conn,recipe,version,payload,ctx,obs=scoped_recipe
    repo.material_command_lock=lambda *args:nullcontext()
    line='line-'+uuid4().hex[:24];order='sales-'+uuid4().hex[:23]
    capture=production_schemas.ProductionSalesRequestCreate(sales_order_id=order,sales_order_line_id=line,product_service_id=recipe.product_service_id,quantity='1.000000',unit='PZA')
    proof={'order_id':order,'order_line_id':line,'product_service_id':recipe.product_service_id,'quantity':'1.000000','unit':'PZA','requested_due_date':None,'organization_context':ctx.model_dump(mode='json')}
    request=repo.create_sales_order_request(TENANT,capture,'request-'+uuid4().hex,'s'*64,'actor',source_proof=proof)
    state={'proof':proof,'calls':[],'scope':tariff_scope()}
    class Source:
        def proof(self,*args):
            state['calls'].append('proof')
            if isinstance(state['proof'],Exception):raise state['proof']
            return state['proof']
    class Workers:
        def eligible(self,*args,**kwargs):state['calls'].append('workers');return [{'id':'shared-worker','full_name':'Shared','labor_position_id':'shared-position'}]
    class Authority:
        def observations(self,*args,**kwargs):state['calls'].append('resources');return [obs]
        def rollback_creation(self,*args):state['calls'].append('rollback')
        def reservation_action(self,*args):state['calls'].append('release')
    monkeypatch.setattr(order_context,'production_access',lambda *args:state['scope'])
    monkeypatch.setattr(source_module,'production_access',lambda *args:state['scope'])
    monkeypatch.setattr(production_api,'manual_context',lambda *args:ctx)
    monkeypatch.setattr(document_presentation,'resolve_document_presentation',lambda *args:presentation(ctx))
    main.app.dependency_overrides[repos.get_production_repository]=lambda:repo
    main.app.dependency_overrides[production_api.get_hr_worker_client]=lambda:Workers()
    main.app.dependency_overrides[production_api.get_resource_authority_client]=lambda:Authority()
    main.app.dependency_overrides[source_module.get_sales_source_client]=lambda:Source()
    main.app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='demo')
    state.update(repo=repo,conn=conn,request=request,capture=capture,payload=payload,context=ctx,obs=obs,http=TestClient(main.app),headers={'X-Tenant-Id':TENANT,'X-Actor-Id':'actor','Idempotency-Key':'convert-'+uuid4().hex},body=payload.model_dump(mode='json'),path='/v1/production/order-requests/'+request.id)
    try:yield state
    finally:main.app.dependency_overrides.clear()

def test_sales_request_conversion_unique_replay_scope_and_cost(sales_conversion):
    s=sales_conversion;http=s['http'];path=s['path'];headers=s['headers']
    lookup=http.get(path+'/recipes',headers=headers);assert lookup.status_code==200,lookup.text
    assert lookup.json()['data'][0]['product_service_id']==s['request'].product_service_id
    made=http.post(path+'/orders',headers=headers,json=s['body']);assert made.status_code==201,made.text
    order=made.json()['data'];assert order['source_type']=='sales_order' and order['source_id']==s['request'].sales_order_id
    assert order['original_planned_cost']=='1.000000'
    assert s['repo'].get_sales_request(TENANT,s['request'].id).production_order_id==order['id']
    status=http.get(path+'/production-status',headers=headers);assert status.status_code==200,status.text
    assert status.json()['data']['quantity']=='1.000000' and status.json()['data']['production_order_status']=='released'
    count=len(s['calls']);s['proof']=ErclaveError('resource_authority_unavailable','down',status_code=503)
    replay=http.post(path+'/orders',headers=headers,json=s['body']);assert replay.status_code==201 and replay.json()==made.json()
    assert len(s['calls'])==count
    other=http.post(path+'/orders',headers={**headers,'Idempotency-Key':'other-'+uuid4().hex},json=s['body'])
    assert other.status_code==409 and other.json()['error']['code']=='production_request_already_converted'
    changed=http.post(path+'/orders',headers=headers,json={**s['body'],'priority':'high'})
    assert changed.status_code==409 and changed.json()['error']['code']=='idempotency_key_reused'
    s['scope']=replace(tariff_scope(),all_divisions=False,divisions=(DIVISIONS[1],))
    assert http.post(path+'/orders',headers=headers,json=s['body']).status_code==403
    assert http.get(path+'/production-status',headers=headers).status_code==403
    assert len(s['calls'])==count

@pytest.mark.parametrize('field,value',[('quantity','2.000000'),('unit','MIN'),('division_ref_id','division-b'),('source_id','forged')])
def test_sales_conversion_rejects_tampered_input_before_effects(sales_conversion,field,value):
    s=sales_conversion
    response=s['http'].post(s['path']+'/orders',headers=s['headers'],json={**s['body'],field:value})
    assert response.status_code==409 and response.json()['error']['code']=='production_request_source_conflict'
    assert s['calls']==[]
    assert s['repo'].get_sales_request(TENANT,s['request'].id).status=='pending_configuration'

@pytest.mark.parametrize('field,value',[('quantity','2'),('unit','MIN'),('product_service_id','foreign'),('organization_context',None)])
def test_sales_conversion_rejects_changed_authority(sales_conversion,field,value):
    s=sales_conversion;s['proof']={**s['proof'],field:value}
    response=s['http'].post(s['path']+'/orders',headers=s['headers'],json=s['body'])
    assert response.status_code==409 and response.json()['error']['code']=='production_request_source_conflict'
    assert s['calls']==['proof']

def test_sales_request_cancel_pending_replay_and_refuse_conversion(sales_conversion):
    s=sales_conversion;headers=s['headers'];body={'reason':'Sales order cancelled'}
    value=s['http'].post(s['path']+'/cancel',headers=headers,json=body);assert value.status_code==200,value.text
    assert value.json()['data']['status']=='cancelled'
    assert s['http'].post(s['path']+'/cancel',headers=headers,json=body).json()==value.json()
    denied=s['http'].post(s['path']+'/orders',headers=headers,json=s['body'])
    assert denied.status_code==409 and denied.json()['error']['code']=='production_request_cancelled'
    assert not s['calls']

def test_sales_cancellation_requires_linked_order_cancel_and_rechecks_start(sales_conversion):
    s=sales_conversion;http=s['http'];headers=s['headers']
    made=http.post(s['path']+'/orders',headers=headers,json=s['body']);assert made.status_code==201,made.text
    order_id=made.json()['data']['id'];path='/v1/production/orders/'+order_id+'/status'
    denied=http.post(s['path']+'/cancel',headers={**headers,'Idempotency-Key':'cancel-request'},json={'reason':'Cancel parent'})
    assert denied.status_code==409 and denied.json()['error']['code']=='production_request_has_order'
    s['proof']=ErclaveError('sales_order_cancellation_pending','Cancellation pending.',status_code=409)
    start=http.patch(path,headers={**headers,'Idempotency-Key':'start-sales'},json={'status':'in_progress','reason':'Start order'})
    assert start.status_code==409 and start.json()['error']['code']=='sales_order_cancellation_pending'
    cancel=http.patch(path,headers={**headers,'Idempotency-Key':'cancel-production'},json={'status':'cancelled','reason':'Cancel production'})
    assert cancel.status_code==200,cancel.text
    cancelled=http.post(s['path']+'/cancel',headers={**headers,'Idempotency-Key':'cancel-request'},json={'reason':'Cancel parent'})
    assert cancelled.status_code==200,cancelled.text
    assert s['repo'].get_sales_request(TENANT,s['request'].id).production_order_id==order_id

def test_sales_attempt_recovery_blocks_new_capture_and_cancel(sales_conversion):
    s=sales_conversion;repo=s['repo'];attempt='ord_'+uuid4().hex[:26]
    repo.select_sales_attempt(TENANT,s['request'].id,attempt)
    preview=repo.preview_resources(TENANT,s['payload'],[s['obs']],s['context'])
    repo.prepare_creation_context(TENANT,attempt,'actor','d'*64,s['context'],preview)
    with pytest.raises(ErclaveError) as exc:repo.select_sales_attempt(TENANT,s['request'].id,'new-attempt')
    assert exc.value.code=='production_creation_recovery_pending'
    response=s['http'].post(s['path']+'/cancel',headers=s['headers'],json={'reason':'Cancel parent'})
    assert response.status_code==409 and response.json()['error']['code']=='production_creation_recovery_pending'
    repo.record_failed_creation(TENANT,attempt,None,'actor','interrupted_creation');repo.recover_failed_creation(TENANT,attempt,'actor')
    repo.select_sales_attempt(TENANT,s['request'].id,'new-attempt')

def test_sales_request_quantity_precision_and_legacy_fingerprint():
    source=sales_source_module
    payload=production_schemas.ProductionSalesRequestCreate(sales_order_id='order',sales_order_line_id='line',product_service_id='product',quantity='999999999999.123456',unit='PZA')
    assert payload.quantity==Decimal('999999999999.123456')
    ordinary=payload.model_copy(update={'quantity':Decimal('1')})
    from types import SimpleNamespace
    historical=SimpleNamespace(model_dump=lambda **kwargs:{**ordinary.model_dump(mode='json'),'quantity':1.0})
    assert source.source_request_fingerprint(ordinary)==production_api.request_fingerprint(historical)

def test_sales_request_api_proves_source_and_replays_without_sales(sales_conversion):
    s=sales_conversion;source=sales_source_module
    class Catalog:
        def require_active(self,*args):pass
    main.app.dependency_overrides[production_api.get_unit_catalog_client]=lambda:Catalog()
    capture=s['capture'].model_dump(mode='json');capture['sales_order_line_id']='new-'+uuid4().hex[:25]
    s['proof']={**s['proof'],'order_line_id':capture['sales_order_line_id']}
    path='/v1/production/order-requests';http=s['http'];headers=s['headers']
    made=http.post(path,headers=headers,json=capture);assert made.status_code==201,made.text
    assert made.json()['data']['organization_context']==s['context'].model_dump(mode='json')
    assert made.json()['data']['original_quantity']=='1.000000'
    snapshot=s['repo'].sales_request_source(TENANT,made.json()['data']['id'])
    assert snapshot['order_line_id']==capture['sales_order_line_id']
    s['proof']=ErclaveError('sales_unavailable','down',status_code=503);calls=len(s['calls'])
    replay=http.post(path,headers=headers,json=capture);assert replay.status_code==201 and replay.json()==made.json()
    assert len(s['calls'])==calls
    s['scope']=replace(tariff_scope(),all_divisions=False,divisions=(DIVISIONS[1],))
    assert http.post(path,headers=headers,json=capture).status_code==403

def test_sales_request_duplicate_line_refuses_distinct_source_data(sales_conversion):
    s=sales_conversion;capture=s['capture'].model_copy(update={'quantity':Decimal('2')})
    proof={**s['proof'],'quantity':'2'}
    with pytest.raises(ErclaveError) as error:
        s['repo'].create_sales_order_request(TENANT,capture,'different-'+uuid4().hex,'b'*64,'actor',source_proof=proof)
    assert error.value.code=='production_request_source_conflict'

def test_sales_request_list_paginates_with_exact_total_and_scope(sales_conversion):
    s=sales_conversion;headers=s['headers'];http=s['http']
    response=http.get('/v1/production/order-requests?limit=1&q='+s['request'].sales_order_id,headers=headers)
    assert response.status_code==200,response.text
    assert response.json()['meta']['total']==1 and len(response.json()['data'])==1
    s['scope']=replace(tariff_scope(),all_divisions=False,divisions=(DIVISIONS[1],))
    response=http.get('/v1/production/order-requests?limit=1&q='+s['request'].sales_order_id,headers=headers)
    assert response.json()['data']==[] and response.json()['meta']['total']==0

def test_sales_request_conversion_cancel_share_database_lock(local_store):
    # Two independent PostgreSQL connections; lock-only, no committed fixture writes.
    store,conn,_,_=local_store
    engine=create_engine(conn.engine.url,poolclass=NullPool)
    first=repos.ProductionRepository(engine);second=repos.ProductionRepository(engine)
    request_id='sales-request:race-'+uuid4().hex[:24]
    try:
        with first.material_command_lock(TENANT,request_id):
            with pytest.raises(ErclaveError) as error:
                with second.material_command_lock(TENANT,request_id):pass
            assert error.value.code=='command_in_progress'
        with second.material_command_lock(TENANT,request_id):pass
    finally:engine.dispose()

def test_sales_conversion_reservation_timeout_compensates_and_keeps_request(sales_conversion):
    s=sales_conversion;repo=s['repo'];version=s['payload'].recipe_version_id
    s['conn'].execute(text("insert into production.recipe_resources(id,tenant_id,recipe_version_id,resource_type,resource_ref_id,resource_code,resource_name,quantity,unit,unit_cost,total_cost,sort_order) values(:id,:t,:v,'material','sales-material','MAT','Material',1,'PZA',0,0,2)"),{'id':'rr_'+uuid4().hex[:25],'t':TENANT,'v':version})
    material=production_schemas.ResourceAvailabilityInput(resource_ref_id='sales-material',resource_type='material',available_quantity=1,unit='PZA',original_unit_cost='0.123456',cost_currency='MXN',source='inventory',allocations=[{'warehouse_id':'warehouse-a','quantity':1}])
    class FailingAuthority:
        def observations(self,*args,**kwargs):return [s['obs'],material]
        def reserve(self,tenant,id,row,*args):
            proof=repo.creation_context(tenant,id,'actor','sales-material:0')
            assert proof['allocation']['inventory_item_id']=='sales-material'
            assert s['conn'].execute(text('select creation_attempt_ref_id from production.sales_order_requests where tenant_id=:t and id=:id'),{'t':TENANT,'id':s['request'].id}).scalar()==id
            s['attempt']=id;s['calls'].append('reserve')
            raise ErclaveError('synthetic_timeout','Reservation response lost.',status_code=503)
        def rollback_creation(self,*args):s['calls'].append('rollback')
    main.app.dependency_overrides[production_api.get_resource_authority_client]=lambda:FailingAuthority()
    response=s['http'].post(s['path']+'/orders',headers=s['headers'],json=s['body'])
    assert response.status_code==503,response.text
    assert s['calls'][-2:]==['reserve','rollback']
    assert repo.get_order(TENANT,s['attempt']) is None
    assert repo.get_sales_request(TENANT,s['request'].id).status=='pending_configuration'
    assert repo.failed_creation(TENANT,s['attempt'],'actor')['status']=='recovered'
    assert s['http'].post(s['path']+'/orders',headers=s['headers'],json=s['body']).status_code==409
    assert s['calls'].count('reserve')==1


def test_sales_source_schema_rejects_untrusted_context():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        production_schemas.ProductionSalesRequestCreate(sales_order_id='order',sales_order_line_id='line',product_service_id='product',quantity=1,unit='PZA',organization_context={'division_ref_id':'forged'})

def test_sales_request_legacy_context_remains_sql_null_and_can_convert(sales_conversion):
    s=sales_conversion;source=sales_source_module
    capture=s['capture'].model_copy(update={'sales_order_line_id':'legacy-'+uuid4().hex[:24]})
    proof={**s['proof'],'order_line_id':capture.sales_order_line_id,'organization_context':None}
    request=s['repo'].create_sales_order_request(TENANT,capture,'legacy-request-'+uuid4().hex,'l'*64,'actor',source_proof=proof)
    assert request.organization_context is None
    assert s['conn'].execute(text('select organization_context is null from production.sales_order_requests where tenant_id=:t and id=:id'),{'t':TENANT,'id':request.id}).scalar()
    s['proof']=proof
    body={**s['body'],'division_ref_id':None,'source_type':'sales_order','source_id':capture.sales_order_id,'source_line_id':capture.sales_order_line_id}
    result=s['http'].post('/v1/production/orders',headers=s['headers'],json=body)
    assert result.status_code==201,result.text
    assert result.json()['data']['organization_context'] is None
    assert s['repo'].get_sales_request(TENANT,request.id).production_order_id==result.json()['data']['id']

def test_sales_request_preserves_full_quantity_decimal(sales_conversion):
    s=sales_conversion
    quantity=Decimal('999999999999.123456')
    capture=s['capture'].model_copy(update={'quantity':quantity,'sales_order_line_id':'exact-'+uuid4().hex[:24]})
    proof={**s['proof'],'quantity':str(quantity),'order_line_id':capture.sales_order_line_id}
    request=s['repo'].create_sales_order_request(TENANT,capture,'exact-'+uuid4().hex,'e'*64,'actor',source_proof=proof)
    assert request.original_quantity==quantity
    assert s['repo'].sales_request_status(TENANT,request.id).quantity==quantity
