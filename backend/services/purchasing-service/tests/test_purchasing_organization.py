import importlib,sys,os
from datetime import date
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
from erclave_common.organization_client import resolve_organization_access,get_organization_client
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
main=importlib.import_module('app.main');repos=importlib.import_module('app.repositories')
purchase_schemas=importlib.import_module('app.schemas')
Store=importlib.import_module('app.organization_store').OrganizationStore
schemas=importlib.import_module('app.organization_schemas');api=importlib.import_module('app.organization_api')
TENANT='ten_739ee59d765d5e14818674800d'
MODULE='purchasing';KIND='supplier'
DIVISIONS=({'id':'division-a','code':'DIV-A','name':'Division A','society_id':'society-a'},{'id':'division-b','code':'DIV-B','name':'Division B','society_id':'society-b'})
def context():return {'tenant':{'id':TENANT,'status':'active'},'user':{'id':'actor','status':'active'},'scope':{'version':2,'all_divisions':True,'divisions':list(DIVISIONS)},'permissions':[f'{MODULE}.{KIND}.read',f'{MODULE}.{KIND}.update'],'active_modules':['admin',MODULE],'capabilities':{}}
def access():return resolve_organization_access(context(),TENANT,MODULE,f'{MODULE}.{KIND}.update')

@pytest.mark.parametrize('field,value,code',[
 ('tenant',{'id':'foreign','status':'active'},'tenant_access_denied'),('user',{'id':'actor','status':'inactive'},'tenant_access_denied'),
 ('active_modules',['admin','accounting'],'module_not_enabled'),('active_modules',[MODULE],'module_not_enabled'),('permissions',[],'permission_denied'),('scope',{'version':1},'organization_scope_review_required')])
def test_authority_fails_closed(field,value,code):
    data=context();data[field]=value
    with pytest.raises(ErclaveError) as exc:resolve_organization_access(data,TENANT,MODULE,f'{MODULE}.{KIND}.update')
    assert exc.value.code==code

class TransactionEngine:
    def __init__(self,conn):self.conn=conn
    @contextmanager
    def begin(self):
        with self.conn.begin_nested():yield self.conn
    @contextmanager
    def connect(self):yield self.conn

@pytest.fixture
def local_store():
    from sqlalchemy.engine import make_url
    value=os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not value:pytest.skip('Local PostgreSQL URL not configured')
    parsed=make_url(value)
    assert parsed.host in ('127.0.0.1','localhost','::1') and parsed.port==5434 and parsed.database=='erclave_local' and not parsed.query
    engine=create_engine(parsed,poolclass=NullPool)
    with engine.connect() as conn:
        txn=conn.begin()
        try:
            assert conn.execute(text('select id from admin.tenants')).scalars().all()==[TENANT]
            id_='party_'+uuid4().hex[:26]
            conn.execute(text("insert into purchasing.suppliers(id,tenant_id,code,commercial_name,currency,payment_terms,status) values(:i,:t,:i,'Synthetic 100% supplier','MXN','cash','active')"),{'t':TENANT,'i':id_})
            repository=repos.PurchasingRepository.__new__(repos.PurchasingRepository);repository.engine=TransactionEngine(conn)
            yield Store(repository),conn,id_
        finally:txn.rollback()
    engine.dispose()

def save(store,id_,division='division-a',payload=None,key=None,actor=None):
    return store.save(actor or access(),id_,division,schemas.AssignmentCommand(**(payload or {'expected_revision':0})),key or 'test-'+uuid4().hex,'test-correlation')

def test_purchasing_managed_code_is_persisted_and_locked_on_edit(local_store):
    _,conn,_=local_store
    repository=repos.PurchasingRepository.__new__(repos.PurchasingRepository)
    repository.engine=TransactionEngine(conn)
    payload=purchase_schemas.RequisitionWrite(code='REQ-ADMIN-000001',required_date=date.today(),lines=[
        purchase_schemas.PurchaseLineInput(line_type='service',description='Servicio',quantity=1,unit_code='E48')
    ])
    created=repository.create_requisition(TENANT,payload,'cc18-create-'+uuid4().hex,'cc18-hash','actor',code_mode='managed')
    assert created['code']=='REQ-ADMIN-000001' and created['code_mode']=='managed'
    with pytest.raises(ValueError,match='managed_code_locked'):
        repository.update_requisition(TENANT,created['id'],payload.model_copy(update={'code':'REQ-OTHER'}),'cc18-update-'+uuid4().hex,'cc18-update-hash','actor')
    unchanged=repository.get_requisition(TENANT,created['id'])
    assert unchanged['code']=='REQ-ADMIN-000001' and unchanged['code_mode']=='managed'

    manual=repository.create_requisition(TENANT,payload.model_copy(update={'code':'REQ-MANUAL'}),'cc18-manual-'+uuid4().hex,'cc18-manual-hash','actor',code_mode='manual')
    revised=repository.update_requisition(TENANT,manual['id'],payload.model_copy(update={'code':'REQ-MANUAL-2'}),'cc18-edit-'+uuid4().hex,'cc18-edit-hash','actor')
    assert revised['code']=='REQ-MANUAL-2' and revised['code_mode']=='manual'

def test_postgres_single_master_multiple_divisions_atomic_audit_and_replay(local_store):
    store,conn,id_=local_store;key='test-'+uuid4().hex
    first=save(store,id_,key=key);assert first==save(store,id_,key=key)
    assert first['society_ref_id']=='society-a'
    save(store,id_,'division-b')
    assert store.assignments(access(),id_,25,0)['meta']['total']==2
    assert store.assignments(access(),id_,1,1)['data'][0]['division_ref_id']=='division-b'
    limited=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],))
    assert store.assignments(limited,id_,25,0)['meta']['total']==1
    assert store.assignments(replace(limited,divisions=()),id_,25,0)['data']==[]
    with pytest.raises(ErclaveError):store.assignments(replace(access(),tenant_id='foreign'),id_,25,0)
    with pytest.raises(ErclaveError) as exc:save(store,id_,payload={'expected_revision':0,'status':'inactive'},key=key)
    assert exc.value.code=='idempotency_key_reused'
    with pytest.raises(ErclaveError) as exc:save(store,id_)
    assert exc.value.code=='assignment_revision_conflict'
    # Authorization precedes a cached success.
    with pytest.raises(ErclaveError):save(store,id_,key=key,actor=replace(limited,divisions=()))
    assert conn.execute(text(f'select count(*) from {MODULE}.{KIND}s where tenant_id=:t and id=:i'),{'t':TENANT,'i':id_}).scalar()==1
    assert conn.execute(text(f"select count(*) from {MODULE}.audit_events where tenant_id=:t and entity_id=:i and action=:a"),{'t':TENANT,'i':id_,'a':f'organization_assignment.{KIND}'}).scalar()==2
    audit=conn.execute(text(f"select payload from {MODULE}.audit_events where tenant_id=:t and entity_id=:i and action=:a limit 1"),{'t':TENANT,'i':id_,'a':f'organization_assignment.{KIND}'}).scalar()
    assert not any(field in str(audit) for field in ('tax_id','commercial_name','payment_terms','credit_limit','email'))
    master=conn.execute(text(f'select payment_terms,currency from {MODULE}.{KIND}s where tenant_id=:t and id=:i'),{'t':TENANT,'i':id_}).first()
    assert tuple(master)==('cash','MXN')

def test_postgres_eligibility_literal_search_minimal_identity_and_society_change(local_store):
    store,conn,id_=local_store;save(store,id_)
    result=store.eligible(access(),'division-a','%',20,0)
    assert result['meta']['total']==1 and result['data'][0]['id']==id_
    assert set(result['data'][0])=={'id','code','name','division_ref_id','society_ref_id'}
    assert store.eligible(access(),'division-a','__',20,0)['data']==[]
    assert store.eligible(access(),'division-a','',20,1)['data']==[]
    moved=replace(access(),divisions=({**DIVISIONS[0],'society_id':'society-new'},DIVISIONS[1]))
    assert store.eligible(moved,'division-a','',20,0)['data']==[]
    assert save(store,id_,payload={'expected_revision':1},actor=moved)['society_ref_id']=='society-new'
    assert store.eligible(moved,'division-a','',20,0)['data'][0]['id']==id_

@pytest.mark.parametrize('status',['inactive'])
def test_postgres_inactive_master_and_historical_deactivation(local_store,status):
    store,conn,id_=local_store;save(store,id_)
    conn.execute(text(f'update {MODULE}.{KIND}s set status=:s where tenant_id=:t and id=:i'),{'t':TENANT,'i':id_,'s':status})
    assert store.eligible(access(),'division-a','',20,0)['data']==[]
    with pytest.raises(ErclaveError) as exc:save(store,id_,payload={'expected_revision':1})
    assert exc.value.code=='assignment_resource_inactive'
    assert store.assignments(access(),id_,25,0)['data'][0]['revision']==1
    historical=replace(access(),divisions=())
    value=save(store,id_,payload={'expected_revision':1,'status':'inactive'},actor=historical)
    assert value['society_ref_id']=='society-a' and value['revision']==2
    with pytest.raises(ErclaveError):save(store,id_,'division-b',payload={'expected_revision':0,'status':'inactive'})

def test_postgres_downgrade_protects_history(local_store):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,id_=local_store;save(store,id_)
    path=ROOT.parents[1]/'alembic/versions/20260928_0044_commercial_dimensions.py'
    spec=importlib.util.spec_from_file_location('commercial_dimension_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Commercial assignment history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    assert store.assignments(access(),id_,25,0)['meta']['total']==1

def test_api_permissions_validation_and_cors():
    class Client:
        data=context()
        def session(self,*args):return self.data
    class Fake:
        def assignments(self,*args):return {'data':[],'meta':{'total':0,'limit':25,'offset':0}}
        def eligible(self,*args):return {'data':[],'meta':{'total':0,'limit':20,'offset':0}}
        def save(self,a,id_,division,payload,*args):return {KIND+'_id':id_,'division_ref_id':division,'society_ref_id':'society-a','revision':1,'status':payload.status}
    authority=Client();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'test-assignment'}
        path=f'/v1/{MODULE}/{KIND}s/resource/division-assignments';payload={'expected_revision':0}
        assert http.options(path+'/division-a',headers={'Origin':'http://127.0.0.1:4173','Access-Control-Request-Method':'PUT','Access-Control-Request-Headers':'content-type,x-tenant-id,x-correlation-id,idempotency-key,authorization'}).status_code==200
        assert http.get(f'/v1/{MODULE}/organization/divisions',headers=headers).status_code==200
        assert http.get(path,headers=headers).status_code==200
        assert http.get(f'/v1/{MODULE}/division-{KIND}s?division_id=division-a',headers=headers).status_code==200
        assert http.put(path+'/division-a',headers=headers,json=payload).status_code==200
        for extra in ('society_ref_id','cost_center_ref_id','payment_terms','credit_limit'):
            assert http.put(path+'/division-a',headers=headers,json={**payload,extra:'secret'}).status_code==422
        assert http.put(path+'/division-a',headers={k:v for k,v in headers.items() if k!='Idempotency-Key'},json=payload).status_code==400
        assert http.put(path+'/division-a',headers=headers,json={'expected_revision':-1}).status_code==422
        authority.data['permissions']=[f'{MODULE}.{KIND}.read']
        assert http.put(path+'/division-a',headers=headers,json=payload).status_code==403
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
        authority.data['active_modules']=['admin']
        assert http.get(path,headers=headers).status_code==403
    finally:app.dependency_overrides.clear()


TermsStore=importlib.import_module('app.commercial_terms_store').CommercialTermsStore
terms_schemas=importlib.import_module('app.commercial_terms_schemas')
class TermAuthority:
    def require_catalog_item(self,*args):return args[2]
    def require_catalog(self,*args):return {'code':args[2],'status':'active'}

def terms_payload(revision=0, **changes):
    return terms_schemas.CommercialTermsCommand(expected_revision=revision, values={'currency':'MXN','payment_terms':'cash','lead_time_days':0,**changes})

def save_terms(store,id_,division='division-a',payload=None,key=None,actor=None,authority=None):
    return TermsStore(store.repository).save(actor or access(),id_,division,payload or terms_payload(),key or 'terms-'+uuid4().hex,'terms-correlation',authority or TermAuthority())

def test_postgres_terms_explicit_independent_and_no_master_fallback(local_store):
    store,conn,id_=local_store;terms=TermsStore(store.repository)
    with pytest.raises(ErclaveError):terms.read(access(),id_,'division-a')
    with pytest.raises(ErclaveError):save_terms(store,id_)
    save(store,id_);save(store,id_,'division-b')
    pending=terms.read(access(),id_,'division-a')
    assert pending['values'] is None and pending['revision']==0 and pending['requires_confirmation']
    key='terms-'+uuid4().hex;first=save_terms(store,id_,key=key)
    assert first==save_terms(store,id_,key=key)
    assert first['values']['lead_time_days']==0
    save_terms(store,id_,'division-b',terms_payload(currency='USD',payment_terms='net30',lead_time_days=15))
    conn.execute(text(f"update {MODULE}.{KIND}s set currency='EUR',payment_terms='net60',lead_time_days=99 where tenant_id=:t and id=:i"),{'t':TENANT,'i':id_})
    assert terms.read(access(),id_,'division-a')['values']==first['values']
    assert terms.read(access(),id_,'division-b')['values']['currency']=='USD'
    with pytest.raises(ErclaveError) as exc:save_terms(store,id_)
    assert exc.value.code=='assignment_revision_conflict'
    with pytest.raises(ErclaveError) as exc:save_terms(store,id_,payload=terms_payload(currency='USD'),key=key)
    assert exc.value.code=='idempotency_key_reused'
    assert conn.execute(text(f"select count(*) from {MODULE}.audit_events where tenant_id=:t and entity_id=:i and action=:a"),{'t':TENANT,'i':id_,'a':f'commercial_terms.{KIND}'}).scalar()==2
    # Assignment lifecycle never erases or rewrites explicit terms.
    save(store,id_,payload={'expected_revision':1,'status':'inactive'})
    historical=terms.read(access(),id_,'division-a');assert historical['values']==first['values'] and not historical['assignment_active']
    with pytest.raises(ErclaveError):save_terms(store,id_,payload=terms_payload(1))

def test_postgres_terms_catalog_failure_rollback_and_scope_before_replay(local_store):
    store,conn,id_=local_store;save(store,id_);key='terms-'+uuid4().hex
    class Invalid(TermAuthority):
        def require_catalog_item(self,*args):raise ErclaveError('authoritative_reference_not_found','Private',422)
        def require_catalog(self,*args):raise ErclaveError('catalog_item_not_found','Private',422)
    with pytest.raises(ErclaveError) as exc:save_terms(store,id_,key=key,authority=Invalid())
    assert exc.value.details['issues'][0]['loc']==['body','values','currency']
    assert TermsStore(store.repository).read(access(),id_,'division-a')['revision']==0
    save_terms(store,id_,key=key)
    denied=replace(access(),all_divisions=False,divisions=())
    for method in [lambda:save_terms(store,id_,key=key,actor=denied),lambda:TermsStore(store.repository).read(denied,id_,'division-a'),lambda:save_terms(store,id_,actor=replace(access(),tenant_id='foreign'))]:
        with pytest.raises(ErclaveError):method()
    class Down(TermAuthority):
        def require_catalog_item(self,*args):raise ErclaveError('authority_unavailable','Private',503)
        def require_catalog(self,*args):raise ErclaveError('purchasing_dependency_unavailable','Private',503)
    with pytest.raises(ErclaveError) as exc:save_terms(store,id_,payload=terms_payload(1),authority=Down())
    assert exc.value.status_code==503
    assert TermsStore(store.repository).read(access(),id_,'division-a')['revision']==1

def test_postgres_terms_society_reconfirmation_and_safe_downgrade(local_store):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,id_=local_store;save(store,id_);first=save_terms(store,id_)
    moved=replace(access(),divisions=({**DIVISIONS[0],'society_id':'society-new'},))
    value=TermsStore(store.repository).read(moved,id_,'division-a')
    assert value['requires_confirmation'] and not value['assignment_active'] and value['values']==first['values']
    with pytest.raises(ErclaveError):save_terms(store,id_,payload=terms_payload(1),actor=moved)
    save(store,id_,payload={'expected_revision':1},actor=moved)
    result=save_terms(store,id_,payload=terms_payload(1),actor=moved)
    assert not result['requires_confirmation'] and result['confirmed_society_ref_id']=='society-new'
    historical=TermsStore(store.repository).read(replace(access(),divisions=()),id_,'division-a')
    assert not historical['assignment_active'] and historical['values']==first['values']
    path=ROOT.parents[1]/'alembic/versions/20260928_0045_commercial_terms.py'
    spec=importlib.util.spec_from_file_location('commercial_terms_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Commercial terms history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()

@pytest.mark.parametrize('values', [{}, {'currency':'MXN','payment_terms':'cash'}, {'currency':'MXN','payment_terms':'cash','lead_time_days':-1}, {'currency':'MXN','payment_terms':'cash','lead_time_days':3651}, {'currency':'MXN','payment_terms':'cash','lead_time_days':0,'society_ref_id':'arbitrary'}])
def test_terms_require_complete_explicit_values(values):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):terms_schemas.CommercialTermsCommand(expected_revision=0,values=values)

def test_terms_api_read_update_permissions_missing_key_and_no_inheritance():
    class Authority:
        data=context()
        def session(self,*args):return self.data
    class Fake:
        def read(self,a,id_,d):return {'resource_id':id_,'division_ref_id':d,'revision':0,'values':None,'confirmed_society_ref_id':None,'current_society_ref_id':'society-a','requires_confirmation':True,'assignment_active':True}
        def save(self,a,id_,d,p,*args):return {**self.read(a,id_,d),'revision':1,'values':p.values.model_dump(mode='json'),'confirmed_society_ref_id':'society-a','requires_confirmation':False}
    authority=Authority();app=main.app;app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase');app.dependency_overrides[get_organization_client]=lambda:authority;app.dependency_overrides[api.terms_store]=lambda:Fake()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'terms-test-key'}
        path=f'/v1/{MODULE}/{KIND}s/resource/division-assignments/division-a/commercial-terms';payload=terms_payload().model_dump(mode='json')
        assert http.get(path,headers=headers).json()['data']['values'] is None
        assert http.put(path,headers=headers,json=payload).status_code==200
        for value in (None,{}, {'currency':'MXN'}):assert http.put(path,headers=headers,json={**payload,'values':value}).status_code==422
        assert http.put(path,headers={k:v for k,v in headers.items() if k!='Idempotency-Key'},json=payload).status_code==400
        authority.data['permissions']=[f'{MODULE}.{KIND}.read'];assert http.put(path,headers=headers,json=payload).status_code==403
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
        authority.data['active_modules']=['admin'];assert http.get(path,headers=headers).status_code==403
    finally:app.dependency_overrides.clear()
