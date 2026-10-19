from decimal import Decimal
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
from erclave_common.organization_client import resolve_organization_access,get_organization_client
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
main=importlib.import_module('app.main');repos=importlib.import_module('app.repositories')
Store=importlib.import_module('app.organization_store').OrganizationStore
schemas=importlib.import_module('app.organization_schemas');api=importlib.import_module('app.organization_api')
TENANT='ten_739ee59d765d5e14818674800d'
MODULE='sales';KIND='customer'
DIVISIONS=({'id':'division-a','code':'DIV-A','name':'Division A','society_id':'society-a'},{'id':'division-b','code':'DIV-B','name':'Division B','society_id':'society-b'})
def context():return {'tenant':{'id':TENANT,'status':'active'},'user':{'id':'actor','status':'active'},'scope':{'version':2,'all_divisions':True,'divisions':list(DIVISIONS),'societies':[{'id':'society-a','base_currency':'MXN'},{'id':'society-b','base_currency':'MXN'}]},'permissions':[f'{MODULE}.{KIND}.read',f'{MODULE}.{KIND}.update'],'active_modules':['admin',MODULE],'capabilities':{}}
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
            conn.execute(text("insert into sales.customers(id,tenant_id,code,commercial_name,customer_type,status,responsible_worker_ref_id,responsible_worker_name,payment_terms,currency) values(:i,:t,:i,'Synthetic 100% customer','company','active','synthetic','Synthetic','cash','MXN')"),{'t':TENANT,'i':id_})
            repository=repos.SalesRepository.__new__(repos.SalesRepository);repository.engine=TransactionEngine(conn)
            yield Store(repository),conn,id_
        finally:txn.rollback()
    engine.dispose()

def save(store,id_,division='division-a',payload=None,key=None,actor=None):
    return store.save(actor or access(),id_,division,schemas.AssignmentCommand(**(payload or {'expected_revision':0})),key or 'test-'+uuid4().hex,'test-correlation')

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

@pytest.mark.parametrize('status',['inactive', 'blocked', 'prospect'])
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
    return terms_schemas.CommercialTermsCommand(expected_revision=revision, values={'currency':'MXN','payment_terms':'cash','credit_limit':'0.00',**changes})

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
    assert first['values']['credit_limit']=='0.00'
    save_terms(store,id_,'division-b',terms_payload(currency='USD',payment_terms='net30',credit_limit='123.45'))
    conn.execute(text(f"update {MODULE}.{KIND}s set currency='EUR',payment_terms='net60',credit_limit=99 where tenant_id=:t and id=:i"),{'t':TENANT,'i':id_})
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

@pytest.mark.parametrize('values', [{}, {'currency':'MXN','payment_terms':'cash'}, {'currency':'MXN','payment_terms':'cash','credit_limit':-1}, {'currency':'MXN','payment_terms':'cash','credit_limit':'0.001'}, {'currency':'MXN','payment_terms':'cash','credit_limit':0,'society_ref_id':'arbitrary'}])
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


quote_context=importlib.import_module('app.quote_context')
quote_schemas=importlib.import_module('app.schemas')
sales_api=importlib.import_module('app.api')
from erclave_common.document_presentation import DocumentPresentationSnapshot

def presentation():
    return DocumentPresentationSnapshot.model_validate({
        'division_ref_id':'division-a','division_code':'DIV','division_name':'Division',
        'society_ref_id':'society-a','society_code':'SOC','society_name':'Society',
        'issuer_ref_id':'issuer-a','issuer_code':'EMI','issuer_legal_name':'Issuer at approval',
        'template_origin':'society','template_origin_id':'society-a',
        'template':{'primary_color':'#6106A0','accent_color':'#F557D3','text_color':'#190F34','show_page_number':True}
    })
class QuoteAuthority(TermAuthority):
    hr_url='http://127.0.0.1:8006'
    production_url='http://127.0.0.1:8002'
    def get_division_estimated_cost(self,*args):return None
    def _get(self,url,*args):
        from urllib.parse import urlparse,parse_qs
        query=parse_qs(urlparse(url).query)
        return [{'id':query['resource_id'][0],'division_ref_id':query['division_id'][0]}]

@pytest.fixture
def scoped_quote(local_store):
    store,conn,id_=local_store;save(store,id_);save_terms(store,id_)
    quote_id='quo_'+uuid4().hex[:26]
    conn.execute(text("insert into sales.quotes(id,tenant_id,code,customer_id,customer_code_snapshot,customer_name_snapshot,responsible_worker_ref_id,responsible_worker_name,status,currency,payment_terms,valid_until,subtotal,discount_total,total) values(:i,:t,:i,:c,:c,'Synthetic','worker','Synthetic','draft','MXN','cash',current_date+30,10,0,10)"),{'i':quote_id,'t':TENANT,'c':id_})
    conn.execute(text("insert into sales.quote_lines(id,tenant_id,quote_id,line_number,product_service_ref_id,product_service_code,product_service_name,product_service_type,unit,quantity,unit_price,discount_percentage,subtotal,discount_amount,total) values(:i,:t,:q,1,'product','PRD','Synthetic','service','HUR',1,10,0,10,0,10)"),{'i':'line_'+uuid4().hex[:26],'t':TENANT,'q':quote_id})
    yield store,conn,id_,quote_id

def attach(data,revision=0,division='division-a',actor=None,key=None,authority=None,rate=None):
    store,conn,id_,quote_id=data
    fields={'division_ref_id':division,'expected_revision':revision}
    if rate is not None:fields['cost_exchange_rate']=rate
    return quote_context.QuoteContextStore(store.repository).save(actor or access(),quote_id,quote_context.QuoteContextCommand(**fields),key or 'quote-'+uuid4().hex,'test-context',authority or QuoteAuthority())

def test_quote_context_clears_global_cost_and_freezes_confirmed_society_cost(scoped_quote):
    store,conn,_,quote_id=scoped_quote
    conn.execute(text('update sales.quotes set estimated_cost=99,estimated_margin=1 where tenant_id=:t and id=:i'),{'t':TENANT,'i':quote_id})
    conn.execute(text('update sales.quote_lines set standard_unit_cost_snapshot=99,estimated_cost=99 where tenant_id=:t and quote_id=:i'),{'t':TENANT,'i':quote_id})
    assigned=attach(scoped_quote)
    assert assigned['estimated_cost'] is None and assigned['estimated_margin'] is None
    assert assigned['estimated_cost_snapshot']['status']=='incomplete'
    assert assigned['estimated_cost_snapshot']['cost_exchange_rate']=='1'
    current=store.repository.get_quote(TENANT,quote_id)
    assert current.lines[0].standard_unit_cost_snapshot is None and current.lines[0].estimated_cost is None
    store.repository.transition_quote(TENANT,quote_id,'quoted','cc21-submit-'+uuid4().hex,'hash','actor',organization_revision=1,estimated_costs={'product':None},cost_currency='MXN')
    source={'product_service_id':'product','division_ref_id':'division-a','society_ref_id':'society-a','cost_currency':'MXN','estimated_unit_cost':'2.123456','assignment_revision':4,'confirmed_at':'2026-10-14T12:00:00Z'}
    key='cc21-approve-'+uuid4().hex
    approved=store.repository.transition_quote(TENANT,quote_id,'approved',key,'hash','actor',organization_revision=1,presentation_snapshot=presentation(),estimated_costs={'product':source},cost_currency='MXN')
    assert approved.estimated_cost==Decimal('2.12') and approved.estimated_margin==Decimal('78.8000')
    assert approved.estimated_cost_snapshot['status']=='complete'
    assert approved.lines[0].estimated_cost_snapshot['original_unit_cost']=='2.123456'
    assert approved.lines[0].estimated_cost_snapshot['assignment_revision']==4
    assert approved.lines[0].standard_unit_cost_snapshot is None
    replay=store.repository.transition_quote(TENANT,quote_id,'approved',key,'hash','actor',organization_revision=1,presentation_snapshot=presentation(),estimated_costs={'product':None},cost_currency='MXN')
    assert replay==approved
    order=store.repository.create_order(TENANT,quote_schemas.SalesOrderCreateRequest(code='ORD-'+uuid4().hex[:12],quote_id=quote_id),approved,'cc21-order-'+uuid4().hex,'hash','actor')
    assert order.estimated_cost_snapshot==approved.estimated_cost_snapshot
    assert order.lines[0].estimated_cost_snapshot==approved.lines[0].estimated_cost_snapshot
    assert order.cost_currency is None and order.cost_exchange_rate is None
    margin_report=importlib.import_module('app.reports').build_report(store.repository,TENANT,'commercial-margin',{'_scope_all':True})
    assert next(row for row in margin_report.rows if row['code']==order.code)['margin_percent']==Decimal('78.8000')

def test_quote_preview_refreshes_at_context_draft_edit_submit_and_approval(scoped_quote):
    store,_,_,quote_id=scoped_quote
    def source(amount,revision):return {'product_service_id':'product','division_ref_id':'division-a','society_ref_id':'society-a','cost_currency':'MXN','estimated_unit_cost':amount,'assignment_revision':revision,'confirmed_at':'2026-10-14T12:00:00Z'}
    class CostAuthority(QuoteAuthority):
        def get_division_estimated_cost(self,*args):return source('2.000000',1)
    assigned=attach(scoped_quote,authority=CostAuthority())
    assert assigned['estimated_cost']=='2.00' and assigned['estimated_cost_snapshot']['phase']=='preview'
    updated=store.repository.update_quote(TENANT,quote_id,quote_schemas.QuoteUpdateRequest(notes='revised'),None,None,None,'cc21-update-'+uuid4().hex,'hash','actor',organization_revision=1,cost_currency='MXN',estimated_costs={'product':source('3.000000',2)})
    assert updated.estimated_cost==Decimal('3.00') and updated.lines[0].estimated_cost_snapshot['assignment_revision']==2
    submitted=store.repository.transition_quote(TENANT,quote_id,'quoted','cc21-submit-'+uuid4().hex,'hash','actor',organization_revision=1,estimated_costs={'product':source('4.000000',3)},cost_currency='MXN')
    assert submitted.estimated_cost==Decimal('4.00') and submitted.estimated_cost_snapshot['phase']=='preview'
    approved=store.repository.transition_quote(TENANT,quote_id,'approved','cc21-approve-'+uuid4().hex,'hash','actor',organization_revision=1,presentation_snapshot=presentation(),estimated_costs={'product':source('5.000000',4)},cost_currency='MXN')
    assert approved.estimated_cost==Decimal('5.00') and approved.estimated_cost_snapshot['phase']=='approved'
    assert approved.lines[0].estimated_cost_snapshot['assignment_revision']==4

def test_quote_cost_missing_or_fx_missing_allows_approval_with_null_estimate(scoped_quote):
    store,conn,id_,quote_id=scoped_quote
    save_terms(store,id_,payload=terms_payload(1,currency='USD'))
    conn.execute(text("update sales.quotes set currency='USD' where tenant_id=:t and id=:i"),{'t':TENANT,'i':quote_id})
    attach(scoped_quote)
    store.repository.transition_quote(TENANT,quote_id,'quoted','cc21-submit-'+uuid4().hex,'hash','actor',organization_revision=1,estimated_costs={'product':None},cost_currency='MXN')
    current=store.repository.get_quote(TENANT,quote_id)
    source={'product_service_id':'product','division_ref_id':'division-a','society_ref_id':'society-a','cost_currency':'MXN','estimated_unit_cost':'20.000000','assignment_revision':2,'confirmed_at':'2026-10-14T12:00:00Z'}
    approved=store.repository.transition_quote(TENANT,quote_id,'approved','cc21-approve-'+uuid4().hex,'hash','actor',organization_revision=1,presentation_snapshot=presentation(),estimated_costs={'product':source},cost_currency='MXN')
    assert approved.estimated_cost is None and approved.estimated_margin is None
    assert approved.estimated_cost_snapshot['status']=='incomplete'
    assert approved.lines[0].estimated_cost_snapshot['status']=='exchange_rate_required'
    assert approved.lines[0].estimated_cost_snapshot['original_cost']=='20.000000'

def test_quote_explicit_fx_survives_context_revision_and_converts_at_approval(scoped_quote):
    store,conn,id_,quote_id=scoped_quote
    save_terms(store,id_,payload=terms_payload(1,currency='USD'))
    conn.execute(text("update sales.quotes set currency='USD' where tenant_id=:t and id=:i"),{'t':TENANT,'i':quote_id})
    assigned=attach(scoped_quote,rate=Decimal('0.050000000000'))
    assert assigned['estimated_cost_snapshot']['cost_exchange_rate']=='0.050000000000'
    revised=attach(scoped_quote,revision=1)
    assert revised['estimated_cost_snapshot']['cost_exchange_rate']=='0.050000000000'
    store.repository.transition_quote(TENANT,quote_id,'quoted','cc21-submit-'+uuid4().hex,'hash','actor',organization_revision=2,estimated_costs={'product':None},cost_currency='MXN')
    current=store.repository.get_quote(TENANT,quote_id)
    source={'product_service_id':'product','division_ref_id':'division-a','society_ref_id':'society-a','cost_currency':'MXN','estimated_unit_cost':'20.000000','assignment_revision':2,'confirmed_at':'2026-10-14T12:00:00Z'}
    approved=store.repository.transition_quote(TENANT,quote_id,'approved','cc21-approve-'+uuid4().hex,'hash','actor',organization_revision=2,presentation_snapshot=presentation(),estimated_costs={'product':source},cost_currency='MXN')
    assert approved.estimated_cost==Decimal('1.00')
    assert approved.estimated_margin==Decimal('90.0000')
    assert approved.lines[0].estimated_cost_snapshot['cost_exchange_rate']=='0.050000000000'

def test_quote_same_currency_rejects_nonunit_fx_and_missing_cost_stays_null(scoped_quote):
    store,_,_,quote_id=scoped_quote
    with pytest.raises(ErclaveError) as captured:attach(scoped_quote,rate=Decimal('1.1'))
    assert captured.value.code=='operational_exchange_rate_invalid'
    attached=attach(scoped_quote)
    assert attached['estimated_cost'] is None and attached['estimated_margin'] is None
    submitted=store.repository.transition_quote(TENANT,quote_id,'quoted','cc21-submit-'+uuid4().hex,'hash','actor',organization_revision=1,estimated_costs={'product':None},cost_currency='MXN')
    assert submitted.estimated_cost is None and submitted.estimated_cost_snapshot['status']=='incomplete'
    approved=store.repository.transition_quote(TENANT,quote_id,'approved','cc21-approve-'+uuid4().hex,'hash','actor',organization_revision=1,presentation_snapshot=presentation(),estimated_costs={'product':None},cost_currency='MXN')
    assert approved.estimated_cost is None and approved.estimated_margin is None
    assert approved.lines[0].estimated_cost_snapshot['status']=='cost_unavailable'

def test_postgres_quote_context_snapshot_is_explicit_and_fixed(scoped_quote):
    store,conn,id_,quote_id=scoped_quote;key='quote-'+uuid4().hex
    first=attach(scoped_quote,key=key);assert first==attach(scoped_quote,key=key)
    assert first['division_ref_id']=='division-a' and first['commercial_terms_snapshot']['terms_revision']==1
    save_terms(store,id_,payload=terms_payload(1,payment_terms='net30'))
    assert store.repository.get_quote(TENANT,quote_id).payment_terms=='cash'
    updated=attach(scoped_quote,revision=1);assert updated['payment_terms']=='net30'
    with pytest.raises(ErclaveError):attach(scoped_quote,revision=2,division='division-b')
    with pytest.raises(ErclaveError):attach(scoped_quote,revision=1)
    with pytest.raises(ErclaveError):attach(scoped_quote,key=key,actor=replace(access(),all_divisions=False,divisions=()))
    quote=store.repository.get_quote(TENANT,quote_id)
    store.repository.transition_quote(TENANT,quote_id,'quoted','transition-'+uuid4().hex,'digest','actor',organization_revision=2,estimated_costs={'product':None},cost_currency='MXN')
    with pytest.raises(ErclaveError):attach(scoped_quote,revision=2)
    assert store.repository.get_quote(TENANT,quote_id).commercial_terms_snapshot==quote.commercial_terms_snapshot
    assert conn.execute(text("select count(*) from sales.audit_events where tenant_id=:t and entity_id=:i and action='quote.context'"),{'t':TENANT,'i':quote_id}).scalar()==2

def test_postgres_quote_presentation_is_frozen_at_approval(scoped_quote):
    store,conn,_,quote_id=scoped_quote
    attach(scoped_quote)
    store.repository.transition_quote(TENANT,quote_id,'quoted','submit-'+uuid4().hex,'hash','actor',organization_revision=1,estimated_costs={'product':None},cost_currency='MXN')
    with pytest.raises(ValueError,match='document_presentation_unavailable'):
        store.repository.transition_quote(TENANT,quote_id,'approved','missing-'+uuid4().hex,'hash','actor',organization_revision=1)
    assert store.repository.get_quote(TENANT,quote_id).status=='quoted'
    frozen=presentation()
    approved=store.repository.transition_quote(TENANT,quote_id,'approved','approve-'+uuid4().hex,'hash','actor',organization_revision=1,presentation_snapshot=frozen,estimated_costs={'product':None},cost_currency='MXN')
    assert approved.presentation_snapshot==frozen
    assert store.repository.get_quote(TENANT,quote_id).presentation_snapshot.issuer_legal_name=='Issuer at approval'

def test_postgres_quote_context_resources_currency_and_tenant_fail_closed(scoped_quote):
    store,conn,id_,quote_id=scoped_quote
    class Missing(QuoteAuthority):
        def _get(self,*args):return []
    with pytest.raises(ErclaveError) as exc:attach(scoped_quote,authority=Missing())
    assert exc.value.code=='quote_context_resource_unavailable'
    assert store.repository.get_quote(TENANT,quote_id).organization_revision==0
    save_terms(store,id_,payload=terms_payload(1,currency='USD'))
    with pytest.raises(ErclaveError) as exc:attach(scoped_quote)
    assert exc.value.code=='quote_context_currency_mismatch'
    with pytest.raises(ErclaveError):attach(scoped_quote,actor=replace(access(),tenant_id='foreign'))
    save(store,id_,payload={'expected_revision':1,'status':'inactive'})
    with pytest.raises(ErclaveError):attach(scoped_quote)

def test_postgres_quote_context_guards_existing_repository_mutations(scoped_quote):
    store,conn,id_,quote_id=scoped_quote;attach(scoped_quote)
    payload=quote_schemas.QuoteUpdateRequest(currency='USD')
    with pytest.raises(ErclaveError):store.repository.update_quote(TENANT,quote_id,payload,None,None,None,'update-'+uuid4().hex,'hash','actor',organization_revision=1)
    payload=quote_schemas.QuoteUpdateRequest(notes='safe')
    with pytest.raises(ErclaveError):store.repository.update_quote(TENANT,quote_id,payload,None,None,None,'update-'+uuid4().hex,'hash','actor')
    updated=store.repository.update_quote(TENANT,quote_id,payload,None,None,None,'update-'+uuid4().hex,'hash','actor',organization_revision=1,cost_currency='MXN',estimated_costs={'product':None})
    assert updated.notes=='safe'
    save(store,id_,payload={'expected_revision':1,'status':'inactive'})
    with pytest.raises(ErclaveError):store.repository.transition_quote(TENANT,quote_id,'quoted','transition-'+uuid4().hex,'hash','actor',organization_revision=1)

def test_postgres_quote_context_api_read_scope_and_downstream_block(scoped_quote,monkeypatch):
    store,conn,id_,quote_id=scoped_quote;attach(scoped_quote)
    monkeypatch.setattr(quote_context,'quote_access',lambda *args: replace(access(),all_divisions=False,divisions=()))
    monkeypatch.setattr(sales_api,'quote_access',lambda *args: replace(access(),all_divisions=False,divisions=()))
    app=main.app;app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    try:
        client=TestClient(app);headers={'X-Tenant-Id':TENANT}
        assert client.get('/v1/sales/quotes/'+quote_id,headers=headers).status_code==403
        assert quote_id not in [row['id'] for row in client.get('/v1/sales/quotes',headers=headers).json()['data']]
        report=client.get('/v1/sales/reports/quotes/export',headers=headers)
        assert report.status_code==200 and quote_id not in report.text
        monkeypatch.setattr(quote_context,'quote_access',lambda *args:access())
        assert client.get('/v1/sales/quotes/'+quote_id,headers=headers).json()['data']['division_ref_id']=='division-a'
        conn.execute(text("update sales.quotes set status='approved' where tenant_id=:t and id=:i"),{'t':TENANT,'i':quote_id})
        monkeypatch.setattr(quote_context,'quote_access',lambda *args:replace(access(),all_divisions=False,divisions=()))
        response=client.post('/v1/sales/orders',headers={**headers,'Idempotency-Key':'test-context-order'},json={'code':'TEST-ORDER','quote_id':quote_id})
        assert response.status_code==403
    finally:app.dependency_overrides.clear()

def test_postgres_quote_context_downgrade_preserves_history(scoped_quote):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,id_,quote_id=scoped_quote;attach(scoped_quote)
    path=ROOT.parents[1]/'alembic/versions/20261005_0046_quote_context.py'
    spec=importlib.util.spec_from_file_location('quote_context_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Quote context history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()

def test_cross_module_quote_lookup_requires_sales_enabled():
    data=context();data['active_modules']=['admin','hr'];data['permissions']=['sales.quote.update']
    with pytest.raises(ErclaveError) as exc:resolve_organization_access(data,TENANT,'hr',('hr.worker.read','sales.quote.update'))
    assert exc.value.code=='module_not_enabled'
    data['active_modules'].append('sales')
    assert resolve_organization_access(data,TENANT,'hr',('hr.worker.read','sales.quote.update')).tenant_id==TENANT


def test_postgres_quote_context_api_command_permissions_and_extra_fields(scoped_quote):
    store,conn,id_,quote_id=scoped_quote
    class Authority:
        data={**context(),'permissions':['sales.quote.read','sales.quote.update']}
        def session(self,*args):return self.data
    source=Authority();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:source
    app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    app.dependency_overrides[api.get_sales_authority_client]=lambda:QuoteAuthority()
    try:
        client=TestClient(app);path=f'/v1/sales/quotes/{quote_id}/organization-context';headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'quote-http-test'};payload={'division_ref_id':'division-a','expected_revision':0}
        assert client.get('/v1/sales/organization/quote-divisions',headers=headers).status_code==200
        assert client.put(path,headers={'X-Tenant-Id':TENANT},json=payload).status_code in (400,401)
        assert client.put(path,headers={k:v for k,v in headers.items() if k!='Idempotency-Key'},json=payload).status_code==400
        assert client.put(path,headers=headers,json={**payload,'society_ref_id':'fake'}).status_code==422
        response=client.put(path,headers=headers,json=payload);assert response.status_code==200,response.text
        source.data['permissions']=['sales.quote.read']
        assert client.put(path,headers=headers,json=payload).status_code==403
    finally:app.dependency_overrides.clear()


@pytest.fixture
def scoped_order(scoped_quote):
    store,conn,id_,quote_id=scoped_quote;attach(scoped_quote)
    conn.execute(text("update sales.quotes set status='approved' where tenant_id=:t and id=:i"),{'t':TENANT,'i':quote_id})
    quote=store.repository.get_quote(TENANT,quote_id)
    payload=quote_schemas.SalesOrderCreateRequest(code='ORD-'+uuid4().hex[:12],quote_id=quote_id)
    key='order-'+uuid4().hex
    order=store.repository.create_order(TENANT,payload,quote,key,'hash','actor')
    return store,conn,id_,quote,payload,key,order

def test_scoped_legacy_estimates_are_hidden_from_csv_without_verified_snapshot(scoped_order):
    report_module=importlib.import_module('app.reports')
    store,conn,_,quote,_,_,order=scoped_order
    conn.execute(text('update sales.quotes set estimated_cost=99,estimated_margin=1,estimated_cost_snapshot=null where tenant_id=:t and id=:i'),{'t':TENANT,'i':quote.id})
    conn.execute(text('update sales.orders set estimated_cost=99,estimated_margin=1,estimated_cost_snapshot=null where tenant_id=:t and id=:i'),{'t':TENANT,'i':order.id})
    for kind,code in [('quotes',quote.code),('orders',order.code),('commercial-margin',order.code)]:
        result=report_module.build_report(store.repository,TENANT,kind,{'_scope_all':True})
        row=next(row for row in result.rows if row['code']==code)
        assert row['estimated_cost'] is None and row['estimated_margin'] is None
        if kind=='commercial-margin':assert row['margin_percent'] is None

def test_postgres_order_context_frozen_snapshot_idempotency_and_child(scoped_order):
    store,conn,id_,quote,payload,key,order=scoped_order
    assert order.division_ref_id==quote.division_ref_id and order.society_ref_id==quote.society_ref_id
    assert order.commercial_terms_snapshot==quote.commercial_terms_snapshot and order.quote_organization_revision==1
    assert store.repository.create_order(TENANT,payload,quote,key,'hash','actor')==order
    save_terms(store,id_,payload=terms_payload(1,payment_terms='net30'))
    assert store.repository.get_order(TENANT,order.id).payment_terms=='cash'
    child=store.repository.list_service_orders(TENANT,order_id=order.id)[0]
    assert child.commercial_terms_snapshot==order.commercial_terms_snapshot and child.division_ref_id=='division-a'
    assert store.repository.get_order('foreign',order.id) is None
    assert conn.execute(text("select count(*) from sales.audit_events where tenant_id=:t and entity_id=:i and action='order.context'"),{'t':TENANT,'i':order.id}).scalar()==1

def test_postgres_order_context_scope_reports_and_execution_boundary(scoped_order,monkeypatch):
    store,conn,id_,quote,payload,key,order=scoped_order
    child=store.repository.list_service_orders(TENANT,order_id=order.id)[0]
    scope=replace(access(),all_divisions=False,divisions=())
    monkeypatch.setattr(quote_context,'quote_access',lambda *args:scope)
    monkeypatch.setattr(sales_api,'quote_access',lambda *args:scope)
    app=main.app;app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    app.dependency_overrides[sales_api.get_sales_authority_client]=lambda:ServiceAuthority()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'order-boundary-command'}
        for kind,value in [('orders',order),('service-orders',child)]:
            assert http.get('/v1/sales/'+kind+'/'+value.id,headers=headers).status_code==403
            assert value.id not in [v['id'] for v in http.get('/v1/sales/'+kind,headers=headers).json()['data']]
        for report,code in [('orders',order.code),('commercial-margin',order.code),('service-orders',child.code)]:
            result=http.get('/v1/sales/reports/'+report+'/export',headers=headers)
            assert result.status_code in (200,204) and code not in result.text
        assert http.post('/v1/sales/orders/'+order.id+'/cancel',headers=headers,json={'reason':'test'}).status_code==403
        scope=access()
        assert http.get('/v1/sales/orders/'+order.id,headers=headers).json()['data']['division_ref_id']=='division-a'
        result=http.post('/v1/sales/service-orders/'+child.id+'/transitions/start',headers=headers,json={'reason':'test'})
        assert result.status_code==409 and result.json()['error']['code']=='service_order_transition_invalid'
        assert store.repository.get_service_order(TENANT,child.id).status=='draft'
        assert http.post('/v1/sales/orders/'+order.id+'/cancel',headers=headers,json={'reason':'test'}).status_code==200
        assert store.repository.get_service_order(TENANT,child.id).status=='cancelled'
    finally:app.dependency_overrides.clear()

def test_postgres_order_context_creation_revalidates_quote_and_assignment(scoped_quote):
    store,conn,id_,quote_id=scoped_quote;attach(scoped_quote)
    quote=store.repository.get_quote(TENANT,quote_id)
    payload=quote_schemas.SalesOrderCreateRequest(code='ORD-'+uuid4().hex[:12],quote_id=quote_id)
    with pytest.raises(ValueError,match='approved_quote_required'):store.repository.create_order(TENANT,payload,quote,'key-'+uuid4().hex,'hash','actor')
    conn.execute(text("update sales.quotes set status='approved' where tenant_id=:t and id=:i"),{'t':TENANT,'i':quote_id})
    quote=store.repository.get_quote(TENANT,quote_id)
    with pytest.raises(ValueError,match='assignment_revision_conflict'):store.repository.create_order(TENANT,payload,quote.model_copy(update={'organization_revision':0}),'key-'+uuid4().hex,'hash','actor')
    save(store,id_,payload={'expected_revision':1,'status':'inactive'})
    with pytest.raises(ErclaveError):store.repository.create_order(TENANT,payload,quote,'key-'+uuid4().hex,'hash','actor')
    assert conn.execute(text('select count(*) from sales.orders where tenant_id=:t and quote_id=:i'),{'t':TENANT,'i':quote_id}).scalar()==0

def test_postgres_order_context_downgrade_preserves_history(scoped_order):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,*_=scoped_order
    path=ROOT.parents[1]/'alembic/versions/20261005_0047_order_context.py'
    spec=importlib.util.spec_from_file_location('order_context_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Order context history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()


def test_postgres_order_context_api_conversion_replay_and_resource_failure(scoped_quote,monkeypatch):
    from types import SimpleNamespace
    store,conn,id_,quote_id=scoped_quote;attach(scoped_quote)
    conn.execute(text("update sales.quotes set status='approved' where tenant_id=:t and id=:i"),{'t':TENANT,'i':quote_id})
    class ConversionAuthority(QuoteAuthority):
        fail=False
        def _get(self,*args):return [] if self.fail else super()._get(*args)
        def get_worker(self,*args):return SimpleNamespace(id='worker')
        def get_product(self,*args):return SimpleNamespace(base_unit='HUR')
        def require_unit(self,*args):return 'HUR'
        def allocate_document_code(self,*args):return 'OS-'+quote_id
    authority=ConversionAuthority();scope=access()
    monkeypatch.setattr(quote_context,'quote_access',lambda *args:scope)
    app=main.app;app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    app.dependency_overrides[sales_api.get_sales_authority_client]=lambda:authority
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'convert-'+uuid4().hex};payload={'quote_id':quote_id,'code':'ORD-'+uuid4().hex[:12]}
        authority.fail=True
        assert http.post('/v1/sales/orders',headers=headers,json=payload).status_code==422
        assert conn.execute(text('select count(*) from sales.orders where tenant_id=:t and quote_id=:i'),{'t':TENANT,'i':quote_id}).scalar()==0
        authority.fail=False
        first=http.post('/v1/sales/orders',headers=headers,json=payload)
        assert first.status_code==201,first.text
        assert first.json()['data']['division_ref_id']=='division-a'
        assert http.post('/v1/sales/orders',headers=headers,json=payload).json()==first.json()
        scope=replace(access(),all_divisions=False,divisions=())
        assert http.post('/v1/sales/orders',headers=headers,json=payload).status_code==403
    finally:app.dependency_overrides.clear()

def test_postgres_order_context_blocks_all_pending_effects_before_commands(scoped_order,monkeypatch):
    store,conn,id_,quote,payload,key,order=scoped_order;child=store.repository.list_service_orders(TENANT,order_id=order.id)[0]
    monkeypatch.setattr(quote_context,'quote_access',lambda *args:replace(access(),societies=()))
    app=main.app;app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    service='/v1/sales/service-orders/'+child.id
    commands=[
      ('/v1/sales/orders/'+order.id+'/fulfillment',{'lines':[{'order_line_id':order.lines[0].id,'mode':'production','allocations':[]}]}),
      ('/v1/sales/deliveries',{'code':'DEL-SCOPE','order_id':order.id,'scheduled_date':'2026-10-10','lines':[{'order_line_id':order.lines[0].id,'quantity':'1'}]}),
]
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'effect-'+uuid4().hex}
        for path,body in commands:
            response=http.post(path,headers=headers,json=body)
            assert response.status_code==409,(path,response.text)
            assert response.json()['error']['code']==('operational_cost_currency_unavailable' if path.endswith('/fulfillment') else 'order_context_downstream_pending')
        assert store.repository.get_order(TENANT,order.id).fulfillment_state=='idle'
        assert store.repository.get_service_order(TENANT,child.id).status=='draft'
        assert not store.repository.list_deliveries(TENANT,order_id=order.id)
    finally:app.dependency_overrides.clear()


class ServiceAuthority(QuoteAuthority):
    missing=None
    def _get(self,url,*args):
        from urllib.parse import urlparse,parse_qs
        query=parse_qs(urlparse(url).query)
        if self.missing is not None and query.get('resource_id',[None])[0]==self.missing:return []
        if 'resource_id' not in query:return [{'id':'worker','employee_number':'EMP','full_name':'Synthetic','position_name':'Role','division_ref_id':query['division_id'][0]}]
        return super()._get(url,*args)
    def get_worker(self,tenant,worker_id,*args):
        from types import SimpleNamespace
        return SimpleNamespace(id=worker_id,full_name='Synthetic')

@pytest.fixture
def scoped_service_http(scoped_order,monkeypatch):
    store,conn,id_,quote,payload,key,order=scoped_order
    child=store.repository.list_service_orders(TENANT,order_id=order.id)[0]
    authority=ServiceAuthority();scope={'value':replace(access(),societies=({'id':'society-a','base_currency':'MXN'},))}
    monkeypatch.setattr(quote_context,'quote_access',lambda *args:scope['value'])
    app=main.app;app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    app.dependency_overrides[sales_api.get_sales_authority_client]=lambda:authority
    try:yield TestClient(app),store,conn,order,child,authority,scope
    finally:app.dependency_overrides.clear()

def test_postgres_service_context_full_execution_cost_and_replay(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    path='/v1/sales/service-orders/'+child.id;headers={'X-Tenant-Id':TENANT}
    commands=[('plan',{'planned_start_date':'2026-10-06','planned_end_date':'2026-10-07'},'planned'),('transitions/assign',{'responsible_worker_id':'worker'},'assigned'),('transitions/start',{},'in_progress'),('time-entries',{'worker_id':'worker','worked_on':'2026-10-06','minutes':30,'hourly_cost':'4','cost_currency':'MXN'},'in_progress'),('cost-entries',{'cost_type':'other','description':'Explicit','quantity':'2','unit_cost':'3','cost_currency':'MXN'},'in_progress'),('evidence',{'evidence_reference':'LOCAL'},'in_progress'),('transitions/submit_acceptance',{},'pending_acceptance'),('transitions/accept',{'reason':'Accepted'},'accepted')]
    for route,body,status in commands:
        command_headers={**headers,'Idempotency-Key':'service-'+uuid4().hex}
        response=http.post(path+'/'+route,headers=command_headers,json=body)
        assert response.status_code in (200,201),(route,response.text)
        value=response.json()['data'];assert value['status']==status
        assert value['commercial_terms_snapshot']==order.model_dump(mode='json')['commercial_terms_snapshot']
        replay=http.post(path+'/'+route,headers=command_headers,json=body)
        assert replay.json()==response.json(),(route,replay.text)
    final=store.repository.get_order(TENANT,order.id)
    assert final.status=='delivered' and final.actual_cost==Decimal('8.00')
    assert len(value['time_entries'])==1 and len(value['cost_entries'])==1 and len(value['evidence'])==1

def test_postgres_service_context_scope_resources_and_stop_are_independent(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    path='/v1/sales/service-orders/'+child.id;headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'service-'+uuid4().hex};body={'planned_start_date':'2026-10-06','planned_end_date':'2026-10-07'}
    scope['value']=replace(access(),all_divisions=False,divisions=())
    assert http.post(path+'/plan',headers=headers,json=body).status_code==403
    scope['value']=access();authority.missing='product'
    assert http.post(path+'/plan',headers=headers,json=body).json()['error']['code']=='service_context_resource_unavailable'
    authority.missing=None;assert http.post(path+'/plan',headers=headers,json=body).status_code==200
    scope['value']=replace(access(),all_divisions=False,divisions=())
    assert http.post(path+'/plan',headers=headers,json=body).status_code==403 # Recheck authorization before replay.
    scope['value']=access();authority.missing='outside'
    rejected=http.post(path+'/transitions/assign',headers={**headers,'Idempotency-Key':'assign-'+uuid4().hex},json={'responsible_worker_id':'outside'})
    assert rejected.json()['error']['code']=='service_context_resource_unavailable'
    assert store.repository.get_service_order(TENANT,child.id).status=='planned'
    authority.missing='product'
    cancelled=http.post(path+'/transitions/cancel',headers={**headers,'Idempotency-Key':'cancel-'+uuid4().hex},json={'reason':'Stop'})
    assert cancelled.status_code==200 and cancelled.json()['data']['status']=='cancelled'

def test_postgres_service_context_parent_cancellation_blocks_mutation(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'cancel-'+uuid4().hex}
    assert http.post('/v1/sales/orders/'+order.id+'/cancel',headers=headers,json={'reason':'Stop'}).status_code==200
    response=http.post('/v1/sales/service-orders/'+child.id+'/plan',headers={**headers,'Idempotency-Key':'plan-'+uuid4().hex},json={'planned_start_date':'2026-10-06','planned_end_date':'2026-10-07'})
    assert response.status_code==409
    assert store.repository.get_service_order(TENANT,child.id).status=='cancelled'


def test_postgres_service_context_cancellation_in_progress_serializes_execution(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    conn.execute(text("update sales.orders set cancellation_state='processing' where tenant_id=:t and id=:i"),{'t':TENANT,'i':order.id})
    response=http.post('/v1/sales/service-orders/'+child.id+'/plan',headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'plan-'+uuid4().hex},json={'planned_start_date':'2026-10-06','planned_end_date':'2026-10-07'})
    assert response.status_code==409 and response.json()['error']['code']=='service_context_order_unavailable'
    assert store.repository.get_service_order(TENANT,child.id).status=='draft'

def test_postgres_service_context_worker_lookup_permissions_scope_and_minimization(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    class Source:
        data={**context(),'permissions':['sales.service_order.assign']}
        def session(self,*args):return self.data
    source=Source();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:source
    headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer local-test'};path='/v1/sales/service-orders/'+child.id+'/eligible-workers'
    value=http.get(path,headers=headers);assert value.status_code==200,value.text
    assert set(value.json()['data'][0])=={'id','employee_number','full_name','position_name','division_ref_id'}
    assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
    source.data['permissions']=['sales.service_order.read'];assert http.get(path,headers=headers).status_code==403
    source.data['permissions']=['sales.service_order.assign'];source.data['active_modules']=['admin'];assert http.get(path,headers=headers).status_code==403


def test_order_execution_context_is_minimized_and_scope_authorized(scoped_order):
    store,conn,id_,quote,payload,key,order=scoped_order
    line=order.lines[0]
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='pending',fulfillment_status='pending' where tenant_id=:t and id=:id"),{'t':TENANT,'id':line.id})
    data=context();data['permissions']=['sales.order.fulfill'];data['scope']['all_divisions']=False
    class Client:
        def session(self,*args):return data
    app=main.app
    app.dependency_overrides[repos.get_sales_repository]=lambda:store.repository
    app.dependency_overrides[get_organization_client]=lambda:Client()
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    try:
        http=TestClient(app);path='/v1/sales/orders/'+order.id+'/execution-context?line_id='+line.id
        headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic'}
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
        assert http.get(path,headers=headers).status_code==409
        conn.execute(text("update sales.orders set fulfillment_state='processing',cost_currency=currency,cost_exchange_rate=1 where tenant_id=:t and id=:id"),{'t':TENANT,'id':order.id})
        response=http.get(path,headers=headers)
        assert response.status_code==200,response.text
        value=response.json()['data']
        assert set(value)=={'order_id','order_line_id','organization_context'}
        assert value['organization_context']['division_ref_id']=='division-a'
        data['scope']['divisions']=[DIVISIONS[1]]
        assert http.get(path,headers=headers).status_code==403
        data['scope']['divisions']=list(DIVISIONS);data['permissions']=[]
        assert http.get(path,headers=headers).status_code==403
    finally:app.dependency_overrides.clear()


def test_scoped_stock_delivery_preserves_original_and_converted_cost(scoped_order,monkeypatch):
    from types import SimpleNamespace
    store,conn,id_,quote,payload,key,order=scoped_order;repo=store.repository;line=order.lines[0]
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='pending',fulfillment_status='pending' where tenant_id=:t and id=:id"),{'t':TENANT,'id':line.id})
    scope=replace(access(),societies=({'id':'society-a','base_currency':'USD'},))
    monkeypatch.setattr(quote_context,'quote_access',lambda *args:scope)
    class StockAuthority(ServiceAuthority):
        def get_product(self,*args):return SimpleNamespace(inventory_item_id='item')
        def get_inventory_item(self,*args):return {'id':'item','code':'ITEM','name':'Synthetic','base_unit':line.unit}
        def reserve_stock(self,*args):
            source=repo.get_order(TENANT,order.id)
            assert source.cost_currency=='USD' and source.cost_exchange_rate==Decimal('20')
            return {'id':'reserve-'+order.id,'warehouse_id':'warehouse','quantity':str(line.ordered_quantity),'unit_cost_snapshot':'4','original_unit_cost':'4','organization_context':{'division_ref_id':'division-a','society_ref_id':'society-a','cost_currency':'USD'}}
        def consume_reservation(self,*args):return {'unit_cost':'4','original_unit_cost':'4','organization_context':{'division_ref_id':'division-a','society_ref_id':'society-a','cost_currency':'USD'}}
    app=main.app;app.dependency_overrides[repos.get_sales_repository]=lambda:repo
    app.dependency_overrides[sales_api.get_sales_authority_client]=lambda:StockAuthority()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'stock-'+uuid4().hex}
        command={'lines':[{'order_line_id':line.id,'mode':'stock','allocations':[{'warehouse_id':'warehouse','inventory_item_id':'item','quantity':str(line.ordered_quantity)}]}]}
        url='/v1/sales/orders/'+order.id+'/fulfillment'
        assert http.post(url,headers=headers,json=command).status_code==422
        assert repo.get_order(TENANT,order.id).fulfillment_state=='idle'
        command['cost_exchange_rate']='20'
        response=http.post(url,headers=headers,json=command);assert response.status_code==200,response.text
        assert http.post(url,headers=headers,json=command).status_code==200
        delivery={'code':'D-'+uuid4().hex[:12],'order_id':order.id,'scheduled_date':'2026-10-10','lines':[{'order_line_id':line.id,'quantity':str(line.ordered_quantity)}]}
        response=http.post('/v1/sales/deliveries',headers={**headers,'Idempotency-Key':'delivery-'+order.id},json=delivery)
        assert response.status_code==201,response.text
        delivery_id=response.json()['data']['id']
        # No distributed effect or replay is allowed after scope is revoked.
        scope=replace(scope,all_divisions=False,divisions=())
        assert http.post('/v1/sales/deliveries/'+delivery_id+'/confirm',headers=headers,json={'reason':'Synthetic dispatch'}).status_code==403
        assert http.get('/v1/sales/deliveries/'+delivery_id,headers=headers).status_code==403
        scope=replace(scope,all_divisions=False,divisions=(DIVISIONS[0],))
        # Exercise repository finalization inside fixture transaction; the public advisory lock commits by design.
        current,plan,dispatch_key=repo.prepare_delivery_confirmation(TENANT,delivery_id,'dispatch-'+order.id,'dispatch',actor_id='actor')
        with pytest.raises(ValueError,match='delivery_not_cancellable'):
            repo.cancel_delivery(TENANT,delivery_id,'Synthetic cancellation','cancel-'+order.id,'cancel','actor')
        result=repo.confirm_delivery(TENANT,delivery_id,plan,dispatch_key,'dispatch','actor')
        expected=line.ordered_quantity*Decimal('4')
        assert result.lines[0].original_actual_cost==expected
        assert result.lines[0].actual_cost==expected*Decimal('20')
        assert result.cost_currency=='USD' and result.currency==order.currency
        assert repo.get_order(TENANT,order.id).actual_cost==expected*Decimal('20')
        assert repo.confirm_delivery(TENANT,delivery_id,plan,dispatch_key,'dispatch','actor').id==result.id
        assert repo.list_deliveries(TENANT,order_id=order.id)[0].division_ref_id=='division-a'
    finally:app.dependency_overrides.clear()


@pytest.mark.parametrize('base,order,captured,code', [('USD','MXN',None,'operational_exchange_rate_required'),('USD','USD',Decimal('2'),'operational_exchange_rate_invalid'),('USD','MXN',Decimal('0'),'operational_exchange_rate_required')])
def test_stock_cost_requires_explicit_valid_exchange_rate(base,order,captured,code):
    cost_rate = repos.cost_rate
    with pytest.raises(ErclaveError) as exc:cost_rate(base,order,captured)
    assert exc.value.code==code


def test_stock_cost_decimal_conversion_and_same_currency():
    cost_rate,convert_cost = repos.cost_rate,repos.convert_cost
    assert cost_rate('USD','USD',None)==Decimal('1')
    assert convert_cost(Decimal('12.34'),Decimal('20.123456789012'))==Decimal('248.32')



def start_money_service(fixture):
    http,store,conn,order,child,authority,scope=fixture
    path='/v1/sales/service-orders/'+child.id
    for route,body in [('plan',{'planned_start_date':'2026-10-06','planned_end_date':'2026-10-07'}),('transitions/assign',{'responsible_worker_id':'worker'}),('transitions/start',{})]:
        response=http.post(path+'/'+route,headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'money-start-'+uuid4().hex},json=body)
        assert response.status_code==200,(route,response.text)
    return path


def test_postgres_service_money_original_converted_precision_zero_and_acceptance(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    path=start_money_service(scoped_service_http)
    scope['value']=replace(scope['value'],societies=({'id':'society-a','base_currency':'USD'},))
    commands=[('time-entries',{'worker_id':'worker','worked_on':'2026-10-06','minutes':30,'hourly_cost':'1.234567','cost_currency':'USD','cost_exchange_rate':'20'},'time_entries',Decimal('0.617284'),Decimal('12.35')),
              ('cost-entries',{'cost_type':'other','description':'Explicit original','quantity':'3','unit_cost':'0.123456','cost_currency':'USD','cost_exchange_rate':'20'},'cost_entries',Decimal('0.370368'),Decimal('7.41')),
              ('cost-entries',{'cost_type':'other','description':'Explicit zero','quantity':'2','unit_cost':'0','cost_currency':'USD','cost_exchange_rate':'20'},'cost_entries',Decimal('0'),Decimal('0'))]
    for route,body,field,original,total in commands:
        headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'money-'+uuid4().hex}
        response=http.post(path+'/'+route,headers=headers,json=body)
        assert response.status_code==201,response.text
        entry=next(row for row in response.json()['data'][field] if field=='time_entries' or row['description']==body['description'])
        assert entry['cost_currency']=='USD' and entry['document_currency']=='MXN'
        assert Decimal(entry['cost_exchange_rate'])==Decimal('20')
        assert Decimal(entry['original_total_cost'])==original and Decimal(entry['total_cost'])==total
        assert http.post(path+'/'+route,headers=headers,json=body).json()==response.json()
    for route,body in [('evidence',{'evidence_reference':'LOCAL-MONEY'}),('transitions/submit_acceptance',{}),('transitions/accept',{'reason':'Confirmed'})]:
        response=http.post(path+'/'+route,headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'money-final-'+uuid4().hex},json=body)
        assert response.status_code in (200,201),response.text
    assert store.repository.get_order(TENANT,order.id).actual_cost==Decimal('19.76')
    assert store.repository.get_service_order(TENANT,child.id).actual_cost==Decimal('19.76')
    row=conn.execute(text('select hourly_cost,original_total_cost,total_cost,cost_currency,document_currency,cost_exchange_rate from sales.service_time_entries where tenant_id=:t and service_order_id=:i'),{'t':TENANT,'i':child.id}).mappings().one()
    assert row['hourly_cost']==Decimal('1.234567') and row['original_total_cost']==Decimal('0.617284')
    assert row['total_cost']==Decimal('12.35')


@pytest.mark.parametrize('extra,code',[
    ({},'operational_cost_currency_required'),
    ({'cost_currency':'USD'},'operational_cost_currency_mismatch'),
    ({'cost_currency':'MXN','cost_exchange_rate':'2'},'operational_exchange_rate_invalid'),
])
def test_postgres_service_money_rejects_missing_cross_currency_and_same_currency_rate(scoped_service_http,extra,code):
    http,store,conn,order,child,authority,scope=scoped_service_http;path=start_money_service(scoped_service_http)
    body={'cost_type':'other','description':'Invalid monetary capture','quantity':'1','unit_cost':'1',**extra}
    response=http.post(path+'/cost-entries',headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'money-invalid-'+uuid4().hex},json=body)
    assert response.status_code==422 and response.json()['error']['code']==code,response.text
    assert store.repository.get_service_order(TENANT,child.id).cost_entries==[]


def test_postgres_service_money_rate_required_and_scope_before_effect_and_replay(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http;path=start_money_service(scoped_service_http)
    scope['value']=replace(scope['value'],societies=({'id':'society-a','base_currency':'USD'},))
    body={'cost_type':'other','description':'Foreign monetary capture','quantity':'1','unit_cost':'2','cost_currency':'USD'}
    headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'money-scope-'+uuid4().hex}
    response=http.post(path+'/cost-entries',headers=headers,json=body)
    assert response.status_code==422 and response.json()['error']['code']=='operational_exchange_rate_required',response.text
    body['cost_exchange_rate']='20'
    valid=scope['value'];scope['value']=replace(valid,all_divisions=False,divisions=())
    assert http.post(path+'/cost-entries',headers=headers,json=body).status_code==403
    assert store.repository.get_service_order(TENANT,child.id).cost_entries==[]
    scope['value']=valid
    response=http.post(path+'/cost-entries',headers=headers,json=body);assert response.status_code==201,response.text
    scope['value']=replace(valid,all_divisions=False,divisions=())
    assert http.post(path+'/cost-entries',headers=headers,json=body).status_code==403
    assert len(store.repository.get_service_order(TENANT,child.id).cost_entries)==1


def test_postgres_service_money_replay_preserves_frozen_values_after_society_currency_change(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http;path=start_money_service(scoped_service_http)
    headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'money-frozen-'+uuid4().hex}
    body={'worker_id':'worker','worked_on':'2026-10-06','minutes':60,'hourly_cost':'3.123456','cost_currency':'MXN'}
    response=http.post(path+'/time-entries',headers=headers,json=body);assert response.status_code==201,response.text
    scope['value']=replace(scope['value'],societies=({'id':'society-a','base_currency':'USD'},))
    replay=http.post(path+'/time-entries',headers=headers,json=body)
    assert replay.status_code==201 and replay.json()==response.json(),replay.text
    fresh=http.post(path+'/time-entries',headers={**headers,'Idempotency-Key':'fresh-'+uuid4().hex},json=body)
    assert fresh.status_code==422 and fresh.json()['error']['code']=='operational_cost_currency_mismatch'
    changed=http.post(path+'/time-entries',headers=headers,json={**body,'cost_currency':'USD','cost_exchange_rate':'20'})
    assert changed.status_code==409 and changed.json()['error']['code']=='idempotency_key_reused'
    assert len(store.repository.get_service_order(TENANT,child.id).time_entries)==1


def test_postgres_service_money_legacy_remains_unknown_and_cannot_be_reinterpreted(scoped_service_http):
    http,store,conn,order,child,authority,scope=scoped_service_http
    original=store.repository.get_order(TENANT,order.id)
    conn.execute(text('update sales.orders set division_ref_id=null,society_ref_id=null,commercial_terms_snapshot=null,quote_organization_revision=0 where tenant_id=:t and id=:i'),{'t':TENANT,'i':order.id})
    path=start_money_service(scoped_service_http)
    body={'cost_type':'other','description':'Legacy unknown currency','quantity':'2','unit_cost':'1.234567'}
    response=http.post(path+'/cost-entries',headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'legacy-'+uuid4().hex},json=body)
    assert response.status_code==201,response.text
    entry=response.json()['data']['cost_entries'][0]
    assert entry['cost_currency'] is None and entry['document_currency'] is None and entry['original_total_cost'] is None and entry['cost_exchange_rate'] is None
    assert Decimal(entry['total_cost'])==Decimal('2.47')
    rejected=http.post(path+'/cost-entries',headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'legacy-explicit-'+uuid4().hex},json={**body,'cost_currency':'MXN'})
    assert rejected.status_code==409 and rejected.json()['error']['code']=='operational_context_required'
    # Restoring synthetic context represents old captures attached before monetary rollout.
    import json
    conn.execute(text('update sales.orders set division_ref_id=:d,society_ref_id=:s,commercial_terms_snapshot=cast(:v as jsonb),quote_organization_revision=:r where tenant_id=:t and id=:i'),{'t':TENANT,'i':order.id,'d':original.division_ref_id,'s':original.society_ref_id,'r':original.quote_organization_revision,'v':json.dumps(original.commercial_terms_snapshot)})
    for route,payload in [('evidence',{'evidence_reference':'LOCAL-UNKNOWN'}),('transitions/submit_acceptance',{})]:
        result=http.post(path+'/'+route,headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'unknown-'+uuid4().hex},json=payload)
        assert result.status_code in (200,201),result.text
    rejected=http.post(path+'/transitions/accept',headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'unknown-accept-'+uuid4().hex},json={'reason':'Review'})
    assert rejected.status_code==409 and rejected.json()['error']['code']=='operational_cost_history_review_required',rejected.text
    current=store.repository.get_service_order(TENANT,child.id)
    assert current.status=='pending_acceptance' and current.actual_cost is None and current.cost_entries[0].cost_currency is None


def test_postgres_service_money_constraints_and_downgrade_preserve_history(scoped_service_http):
    from sqlalchemy.exc import DBAPIError
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    http,store,conn,order,child,authority,scope=scoped_service_http;path=start_money_service(scoped_service_http)
    response=http.post(path+'/cost-entries',headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'constraint-'+uuid4().hex},json={'cost_type':'other','description':'Constraint proof','quantity':'1','unit_cost':'0','cost_currency':'MXN'})
    assert response.status_code==201,response.text
    entry=response.json()['data']['cost_entries'][0]
    for expression in ("cost_currency=null", "cost_exchange_rate=2", "original_total_cost=-1"):
        with pytest.raises(DBAPIError):
            with conn.begin_nested():conn.execute(text('update sales.service_cost_entries set '+expression+' where tenant_id=:t and id=:i'),{'t':TENANT,'i':entry['id']})
    module_path=ROOT.parents[1]/'alembic/versions/20261008_0053_service_entry_currency.py'
    spec=importlib.util.spec_from_file_location('service_currency_migration',module_path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Service cost currency history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    assert store.repository.get_service_order(TENANT,child.id).cost_entries[0].original_total_cost==Decimal('0')


@pytest.mark.parametrize('route,body,base,field',[
    ('cost-entries',{'cost_type':'other','description':'Original overflow','quantity':'2','unit_cost':'999999999999.999999','cost_currency':'MXN'},'MXN','unit_cost'),
    ('time-entries',{'worker_id':'worker','worked_on':'2026-10-06','minutes':1440,'hourly_cost':'999999999999.999999','cost_currency':'MXN'},'MXN','hourly_cost'),
    ('cost-entries',{'cost_type':'other','description':'Converted overflow','quantity':'1','unit_cost':'999999999999.999999','cost_currency':'USD','cost_exchange_rate':'999999999999.999999999999'},'USD','unit_cost'),
])
def test_postgres_service_money_overflow_is_field_error_before_storage(scoped_service_http,route,body,base,field):
    http,store,conn,order,child,authority,scope=scoped_service_http;path=start_money_service(scoped_service_http)
    scope['value']=replace(scope['value'],societies=({'id':'society-a','base_currency':base},))
    response=http.post(path+'/'+route,headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'overflow-'+uuid4().hex},json=body)
    assert response.status_code==422,response.text
    assert response.json()['error']['code']=='operational_cost_amount_out_of_range'
    assert response.json()['error']['details']['field']==field
    assert response.json()['error']['details']['issues'][0]['loc']==['body',field]
    current=store.repository.get_service_order(TENANT,child.id)
    assert current.time_entries==[] and current.cost_entries==[]


def test_manufacturing_receipt_reconciliation_recovery_and_original_cost(scoped_order,monkeypatch):
    from types import SimpleNamespace
    store,conn,id_,quote,payload,key,order=scoped_order;repo=store.repository;line=order.lines[0]
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='pending',fulfillment_status='pending' where tenant_id=:t and id=:id"),{'t':TENANT,'id':line.id})
    scope=replace(access(),societies=({'id':'society-a','base_currency':'USD'},))
    monkeypatch.setattr(quote_context,'quote_access',lambda *args:scope)
    session=context();session['permissions']=['sales.order.fulfill'];session['societies']=[{'id':'society-a','base_currency':'USD'}]
    class Client:
        def session(self,*args):return session
    class ManufacturingAuthority(ServiceAuthority):
        production_url='http://production';inventory_url='http://inventory'
        completed=False;received=False;fail_once=True;reserve_calls=[]
        def get_product(self,*args):return SimpleNamespace(inventory_item_id='item')
        def get_inventory_item(self,*args):return {'id':'item','code':'ITEM','name':'Synthetic','base_unit':line.unit}
        def snapshot(self):
            source=repo.get_order(TENANT,order.id);frozen=source.commercial_terms_snapshot['division']
            return {'division_ref_id':source.division_ref_id,'society_ref_id':source.society_ref_id,'division_code':frozen['code'],'division_name':frozen['name'],'cost_currency':source.cost_currency}
        def request_production(self,*args):
            assert repo.production_intent(TENANT,order.id,line.id)['mode']=='production'
            assert repo.get_order(TENANT,order.id).cost_currency=='USD'
            proof=http.get('/v1/sales/orders/'+order.id+'/production-context?line_id='+line.id,headers=headers)
            assert proof.status_code==200,proof.text
            assert proof.json()['data']['quantity']==str(line.ordered_quantity)
            return {'id':'request-'+order.id}
        def _get(self,url,*args):
            if url.endswith('/production-status'):
                return {'request_id':'request-'+order.id,'status':'converted','sales_order_id':order.id,'sales_order_line_id':line.id,'product_service_id':line.product_service_id,'quantity':str(line.ordered_quantity),'unit':line.unit,'organization_context':self.snapshot(),'production_order_id':'prod-'+order.id,'production_order_status':'completed' if self.completed else 'in_progress'}
            if url.endswith('/stock-context'):
                return [{'warehouse_id':'warehouse','warehouse_code':'WH','warehouse_name':'Synthetic','inventory_item_id':'item','item_code':'ITEM','item_name':'Synthetic','received_quantity':str(line.ordered_quantity if self.received else 0),'available_quantity':str(line.ordered_quantity),'unit':line.unit,'organization_context':self.snapshot()}]
            return super()._get(url,*args)
        def reserve_stock(self,*args):
            self.reserve_calls.append(args[-1])
            proof=http.get('/v1/sales/orders/'+order.id+'/execution-context?line_id='+line.id,headers=headers)
            assert proof.status_code==200,proof.text
            assert proof.json()['data']['allocation']['warehouse_id']=='warehouse'
            if self.fail_once:
                self.fail_once=False
                raise ErclaveError('authority_unavailable','Synthetic lost response',503)
            return {'id':'reserved-'+order.id,'inventory_item_id':'item','warehouse_id':'warehouse','quantity':str(line.ordered_quantity),'unit':line.unit,'status':'active','source_type':'sales_order','source_id':order.id,'source_line_id':line.id,'unit_cost_snapshot':4.123456,'original_unit_cost':'4.123456','organization_context':self.snapshot()}
    authority=ManufacturingAuthority();app=main.app
    app.dependency_overrides[repos.get_sales_repository]=lambda:repo
    app.dependency_overrides[sales_api.get_sales_authority_client]=lambda:authority
    app.dependency_overrides[get_organization_client]=lambda:Client()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'manufacture-'+uuid4().hex}
        url='/v1/sales/orders/'+order.id
        command={'lines':[{'order_line_id':line.id,'mode':'production'}],'cost_exchange_rate':'20'}
        response=http.post(url+'/fulfillment',headers=headers,json=command)
        assert response.status_code==200,response.text
        assert response.json()['data']['lines'][0]['fulfillment_status']=='production_requested'
        assert http.post(url+'/fulfillment',headers=headers,json=command).status_code==200
        assert http.get(url+'/production-context?line_id='+line.id,headers=headers).json()['data']['request_id']=='request-'+order.id
        import json
        conn.execute(text("update sales.orders set commercial_terms_snapshot='{}'::jsonb where tenant_id=:t and id=:i"),{'t':TENANT,'i':order.id})
        broken=http.get(url+'/production-context?line_id='+line.id,headers=headers)
        assert broken.status_code==409 and broken.json()['error']['code']=='operational_context_mismatch'
        conn.execute(text("update sales.orders set commercial_terms_snapshot=cast(:snapshot as jsonb) where tenant_id=:t and id=:i"),{'t':TENANT,'i':order.id,'snapshot':json.dumps(order.commercial_terms_snapshot)})
        reconcile={'order_line_id':line.id,'warehouse_id':'warehouse'}
        reconciliation_headers={**headers,'Idempotency-Key':'reconcile-'+uuid4().hex}
        assert http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile).json()['error']['code']=='sales_production_not_completed'
        authority.completed=True
        status=http.get(url+'/production-status?line_id='+line.id,headers=headers);assert status.status_code==200,status.text
        assert status.json()['data']['warehouses'][0]['eligible_for_reconciliation'] is False
        assert http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile).json()['error']['code']=='sales_production_receipt_required'
        assert not authority.reserve_calls
        authority.received=True
        response=http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile)
        assert response.status_code==503,response.text
        assert repo.production_reconciliation(TENANT,order.id,line.id)['status']=='needs_reconciliation'
        with pytest.raises(ValueError,match='production_reconciliation_in_progress'):repo.prepare_cancel_order(TENANT,order.id,'cancel-manufacturing','hash',actor_id='actor')
        response=http.post(url+'/production-reconciliations',headers=reconciliation_headers,json={**reconcile,'warehouse_id':'other'})
        assert response.status_code==409
        response=http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile)
        assert response.status_code==200,response.text
        assert authority.reserve_calls[0]==authority.reserve_calls[1]
        assert response.json()['data']['lines'][0]['fulfillment_mode']=='production'
        assert response.json()['data']['lines'][0]['fulfillment_status']=='reserved'
        assert http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile).status_code==200
        assert len(authority.reserve_calls)==2
        delivery=quote_schemas.DeliveryCreateRequest(code='D-'+uuid4().hex[:12],order_id=order.id,scheduled_date='2026-10-10',lines=[{'order_line_id':line.id,'quantity':line.ordered_quantity}])
        created=repo.create_delivery(TENANT,delivery,'delivery-'+order.id,'hash','actor')
        current,plan,dispatch_key=repo.prepare_delivery_confirmation(TENANT,created.id,'dispatch-'+order.id,'dispatch',actor_id='actor')
        result=repo.confirm_delivery(TENANT,created.id,plan,dispatch_key,'dispatch','actor')
        assert result.lines[0].original_actual_cost==line.ordered_quantity*Decimal('4.123456')
        assert result.lines[0].actual_cost==(line.ordered_quantity*Decimal('4.123456')*20).quantize(Decimal('0.01'))
        assert http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile).status_code==200
        session['scope']['all_divisions']=False;session['scope']['divisions']=[]
        assert http.post(url+'/production-reconciliations',headers=reconciliation_headers,json=reconcile).status_code==403
        assert len(authority.reserve_calls)==2
    finally:app.dependency_overrides.clear()


def test_manufacturing_per_line_commands_preserve_prior_replay_and_cancel_recovery(scoped_order,monkeypatch):
    store,conn,id_,quote,payload,key,order=scoped_order;repo=store.repository;line=order.lines[0];second='sol_'+uuid4().hex[:26]
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='pending',fulfillment_status='pending' where tenant_id=:t and id=:id"),{'t':TENANT,'id':line.id})
    conn.execute(text("""insert into sales.order_lines(id,tenant_id,order_id,quote_line_id,line_number,product_service_ref_id,product_service_code,product_service_name,product_service_type,unit,ordered_quantity,unit_price,discount_percentage,total,fulfillment_mode,fulfillment_status)
      select :id,tenant_id,order_id,:id,line_number+1,product_service_ref_id,product_service_code,product_service_name,'product',unit,ordered_quantity,unit_price,discount_percentage,total,'pending','pending' from sales.order_lines where tenant_id=:t and id=:source"""),{'t':TENANT,'id':second,'source':line.id})
    command=quote_schemas.SalesOrderFulfillmentRequest(lines=[{'order_line_id':line.id,'mode':'production'}],cost_exchange_rate='1')
    repo.prepare_order_fulfillment(TENANT,order.id,command,'first-command','hash1','MXN',Decimal('1'),actor_id='actor')
    repo.configure_order_fulfillment(TENANT,order.id,[{'order_line_id':line.id,'mode':'production','production_request_id':'request-first'}],'first-command','hash1','actor')
    command2=quote_schemas.SalesOrderFulfillmentRequest(lines=[{'order_line_id':second,'mode':'stock','allocations':[{'inventory_item_id':'item','warehouse_id':'wh','quantity':str(line.ordered_quantity)}]}],cost_exchange_rate='1')
    repo.prepare_order_fulfillment(TENANT,order.id,command2,'second-command','hash2','MXN',Decimal('1'),actor_id='actor')
    repo.configure_order_fulfillment(TENANT,order.id,[{'order_line_id':second,'mode':'stock','inventory_item_id':'item','inventory_item_code':'ITEM','inventory_item_name':'Synthetic','reservations':[{'id':'reservation-second','warehouse_id':'wh','quantity':str(line.ordered_quantity),'unit_cost_snapshot':'0'}]}],'second-command','hash2','actor')
    assert repo.fulfillment_replay(TENANT,order.id,'first-command','hash1',actor_id='actor').lines[0].production_request_id=='request-first'
    assert repo.get_order(TENANT,order.id).lines[1].fulfillment_status=='reserved'
    with pytest.raises(ValueError,match='idempotency_key_reused'):repo.fulfillment_replay(TENANT,order.id,'first-command','different',actor_id='actor')
    scope=access();monkeypatch.setattr(quote_context,'quote_access',lambda *args:scope)
    class CancelAuthority:
        blocked=True;released=[];cancelled=[]
        def cancel_production_request(self,*args):
            self.cancelled.append(args[1])
            if self.blocked:raise ErclaveError('production_request_has_order','Cancel production first',409)
        def release_reservation(self,*args):self.released.append(args[1])
    authority=CancelAuthority();app=main.app
    app.dependency_overrides[repos.get_sales_repository]=lambda:repo
    app.dependency_overrides[sales_api.get_sales_authority_client]=lambda:authority
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Idempotency-Key':'cancel-manufactured'};url='/v1/sales/orders/'+order.id+'/cancel';body={'reason':'Synthetic cancellation'}
        response=http.post(url,headers=headers,json=body);assert response.status_code==409,response.text
        assert repo.get_order(TENANT,order.id).cancellation_state=='needs_reconciliation' and not authority.released
        authority.blocked=False
        response=http.post(url,headers=headers,json=body);assert response.status_code==200,response.text
        assert response.json()['data']['status']=='cancelled' and authority.released==['reservation-second']
        assert http.post(url,headers=headers,json=body).status_code==200
        assert authority.cancelled==['request-first','request-first'] and authority.released==['reservation-second']
    finally:app.dependency_overrides.clear()
