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
PERMISSIONS=('hr.worker.read','hr.worker.update','hr.position.read','hr.position.update','costing.cost_center.read')
def context():return {'tenant':{'id':TENANT,'status':'active'},'user':{'id':'actor','status':'active'},'scope':{'version':2,'all_divisions':True,'divisions':list(DIVISIONS),'societies':[{'id':'society-a','base_currency':'MXN'},{'id':'society-b','base_currency':'USD'}]},'permissions':list(PERMISSIONS),'active_modules':['admin','hr'],'capabilities':{'cost_center_catalog':{'available':False}}}
def access():return resolve_organization_access(context(),TENANT,'hr','hr.position.update')

@pytest.mark.parametrize('field,value,code',[
 ('tenant',{'id':'foreign','status':'active'},'tenant_access_denied'),('user',{'id':'actor','status':'inactive'},'tenant_access_denied'),
 ('active_modules',['admin','accounting'],'module_not_enabled'),('active_modules',['hr'],'module_not_enabled'),('permissions',[],'permission_denied'),('scope',{'version':1},'organization_scope_review_required'),
 ('scope',{'version':2,'divisions':[{}]},'assignment_authority_unavailable'),('capabilities',[],'assignment_authority_unavailable')])
def test_assignment_authority_fails_closed(field,value,code):
    data=context();data[field]=value
    with pytest.raises(ErclaveError) as exc:resolve_organization_access(data,TENANT,'hr','hr.position.update')
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
            area='area_'+uuid4().hex[:26];position='role_'+uuid4().hex[:26];worker='worker_'+uuid4().hex[:26]
            conn.execute(text("insert into hr.labor_areas(id,tenant_id,code,name) values(:i,:t,:i,'Synthetic area')"),{'t':TENANT,'i':area})
            conn.execute(text("insert into hr.labor_roles(id,tenant_id,labor_area_id,position,recipe_name,hourly_cost,intervenes_in_production,intervenes_in_maintenance) values(:i,:t,:a,'Synthetic 100% position','Synthetic position',90,true,false)"),{'t':TENANT,'i':position,'a':area})
            token=uuid4().hex
            conn.execute(text("insert into hr.workers(id,tenant_id,employee_number,first_names,first_last_name,curp,rfc,nss,hire_date,labor_position_id) values(:i,:t,:i,'Synthetic','Worker',:curp,:rfc,:nss,'2020-01-01',:p)"),{'t':TENANT,'i':worker,'p':position,'curp':token[:18],'rfc':token[:13],'nss':str(int(token[:9],16)).zfill(11)[-11:]})
            yield Store(repos.HrRepository(TransactionEngine(conn))),conn,area,position,worker
        finally:txn.rollback()
    engine.dispose()

class NoCosting:
    def center(self,*args):raise AssertionError('Null centers and workers must not call Costing')

def test_new_position_code_is_unique_and_replay_is_stable(local_store):
    store,conn,area,position,worker=local_store
    from app.schemas import RoleCreate
    repo=store.repository
    payload=RoleCreate(labor_area_id=area,position='Synthetic coded position',recipe_name='Synthetic coded profile')
    code='PUE-'+uuid4().hex[:12].upper()
    created=repo.create_role(TENANT,payload,'coded-position','payload-a','actor',code=code)
    assert created.code==code
    assert repo.create_role(TENANT,payload,'coded-position','payload-a','actor',code=code).id==created.id
    assert repo.list_roles(TENANT,area=area)[0].code in (None,code)
    assert conn.execute(text('select code from hr.labor_roles where tenant_id=:t and id=:i'),{'t':TENANT,'i':position}).scalar_one() is None
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo.create_role(TENANT,payload,'coded-position','payload-b','actor',code=code)
def save(store,kind,id_,division='division-a',payload=None,key=None,actor=None,client=None):
    cls=schemas.PositionDivisionCommand if kind=='position' else schemas.WorkerDivisionCommand
    payload=payload if payload is not None else ({'expected_revision':0,'hourly_cost':'0'} if kind=='position' else {'expected_revision':0})
    if kind == 'position' and payload.get('status', 'active') == 'active':
        payload = {'hourly_cost_currency_code': 'MXN' if division == 'division-a' else 'USD', **payload}
    return store.save(actor or access(),kind,id_,division,cls(**payload),key or 'test-'+uuid4().hex,'test-correlation',client or NoCosting())

def test_postgres_position_tariff_scope_idempotency_and_history(local_store):
    from decimal import Decimal
    store,conn,area,position,worker=local_store
    key='test-'+uuid4().hex;payload={'expected_revision':0,'hourly_cost':'0'}
    first=save(store,'position',position,payload=payload,key=key)
    assert first==save(store,'position',position,payload=payload,key=key)
    save(store,'position',position,'division-b',{'expected_revision':0,'hourly_cost':'123.456789'})
    assert store.assignments(access(),'position',position,25,0)['meta']['total']==2
    limited=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],))
    assert store.assignments(limited,'position',position,25,0)['meta']['total']==1
    assert store.assignments(replace(limited,divisions=()),'position',position,25,0)['data']==[]
    with pytest.raises(ErclaveError):store.assignments(replace(access(),tenant_id='foreign'),'position',position,25,0)
    with pytest.raises(ErclaveError) as exc:save(store,'position',position,payload={**payload,'hourly_cost':'1'},key=key)
    assert exc.value.code=='idempotency_key_reused'
    with pytest.raises(ErclaveError) as exc:save(store,'position',position,payload=payload)
    assert exc.value.code=='assignment_revision_conflict'
    assert store.eligible(access(),'position','division-b','production','%',20,0)['data'][0]['hourly_cost']==Decimal('123.456789')
    assert store.eligible(access(),'position','division-a','maintenance','',20,0)['data']==[]
    assert store.eligible(access(),'position','division-a','all','__',20,0)['data']==[]
    assert conn.execute(text('select hourly_cost from hr.labor_roles where tenant_id=:t and id=:i'),{'t':TENANT,'i':position}).scalar()==90
    assert conn.execute(text("select count(*) from hr.audit_events where tenant_id=:t and entity_id=:i and action='organization_assignment.position'"),{'t':TENANT,'i':position}).scalar()==2

def test_postgres_center_failure_rollback_deactivation_and_area(local_store):
    store,conn,area,position,worker=local_store
    class Center:
        def center(self,*args):return {'id':'cc','code':'CC-01','name':'Synthetic'}
    value=save(store,'position',position,payload={'expected_revision':0,'hourly_cost':'12.50','cost_center_ref_id':'cc'},client=Center())
    class Down:
        def center(self,*args):raise ErclaveError('assignment_authority_unavailable','Unavailable',503)
    with pytest.raises(ErclaveError):save(store,'position',position,payload={'expected_revision':1,'hourly_cost':'13','cost_center_ref_id':'cc'},client=Down())
    assert store.assignments(access(),'position',position,25,0)['data'][0]['revision']==1
    with pytest.raises(ErclaveError) as exc:save(store,'position',position,payload={'expected_revision':1,'status':'inactive','hourly_cost':'13','cost_center_ref_id':'cc'})
    assert exc.value.code=='hr_assignment_history_locked'
    disabled=save(store,'position',position,payload={'expected_revision':1,'status':'inactive','hourly_cost':'12.50','cost_center_ref_id':'cc'},client=Down())
    assert disabled['cost_center_snapshot']==value['cost_center_snapshot']
    conn.execute(text("update hr.labor_areas set status='inactive' where tenant_id=:t and id=:i"),{'t':TENANT,'i':area})
    with pytest.raises(ErclaveError) as exc:save(store,'position',position,payload={'expected_revision':2,'hourly_cost':'12.5'})
    assert exc.value.code=='hr_assignment_area_unavailable'

def test_postgres_worker_requires_current_enabled_position_and_minimizes_identity(local_store):
    store,conn,area,position,worker=local_store
    with pytest.raises(ErclaveError) as exc:save(store,'worker',worker)
    assert exc.value.code=='hr_assignment_position_unavailable'
    save(store,'position',position);first=save(store,'worker',worker)
    assert first['labor_position_id']==position
    eligible=store.eligible(access(),'worker','division-a','production','Synthetic',20,0)['data']
    assert eligible[0]['id']==worker
    assert store.eligible(access(),'worker','division-a','all','',20,0,resource_id=worker)['data'][0]['id']==worker
    assert store.eligible(access(),'worker','division-a','all','',20,0,resource_id='missing')['data']==[]
    assert not {'curp','rfc','nss','hourly_cost','personal_email'} & eligible[0].keys()
    assert store.eligible(access(),'worker','division-a','maintenance','',20,0)['data']==[]
    audit=conn.execute(text("select payload from hr.audit_events where tenant_id=:t and entity_id=:i and action='organization_assignment.worker'"),{'t':TENANT,'i':worker}).scalar()
    assert not any(field in str(audit) for field in ('curp','rfc','nss','first_names'))
    new_position='role_'+uuid4().hex[:26]
    conn.execute(text("insert into hr.labor_roles(id,tenant_id,labor_area_id,position,recipe_name,intervenes_in_production) values(:i,:t,:a,'New position','New position',true)"),{'i':new_position,'t':TENANT,'a':area})
    save(store,'position',new_position)
    conn.execute(text('update hr.workers set labor_position_id=:p where tenant_id=:t and id=:i'),{'p':new_position,'t':TENANT,'i':worker})
    assert store.eligible(access(),'worker','division-a','all','',20,0)['data']==[]
    updated=save(store,'worker',worker,payload={'expected_revision':1})
    assert updated['labor_position_id']==new_position
    assert store.eligible(access(),'worker','division-a','all','',20,0)['data'][0]['id']==worker
    save(store,'position',new_position,payload={'expected_revision':1,'hourly_cost':'0','status':'inactive'})
    assert store.eligible(access(),'worker','division-a','all','',20,0)['data']==[]
    save(store,'worker',worker,payload={'expected_revision':2,'status':'inactive'})
    assert store.assignments(access(),'worker',worker,25,0)['data'][0]['status']=='inactive'

def test_postgres_assignment_eligibility_changes_and_downgrade_guard(local_store):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,area,position,worker=local_store
    save(store,'position',position);save(store,'worker',worker)
    conn.execute(text("update hr.workers set status='terminated' where tenant_id=:t and id=:i"),{'t':TENANT,'i':worker})
    assert store.eligible(access(),'worker','division-a','all','',20,0)['data']==[]
    with pytest.raises(ErclaveError) as exc:save(store,'worker',worker,payload={'expected_revision':1})
    assert exc.value.code=='assignment_resource_inactive'
    with pytest.raises(ErclaveError):save(store,'worker',worker,'division-b',actor=replace(access(),all_divisions=False,divisions=(DIVISIONS[0],)))
    path=ROOT.parents[1]/'alembic/versions/20260927_0043_hr_dimensions.py'
    spec=importlib.util.spec_from_file_location('hr_dimension_migration',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='HR assignment history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    assert store.assignments(access(),'worker',worker,25,0)['meta']['total']==1

@pytest.mark.parametrize('rate', ['-1','NaN','Infinity','1000000000000','0.0000001'])
def test_tariff_rejects_invalid_precision_and_non_finite_values(rate):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):schemas.PositionDivisionCommand(expected_revision=0,hourly_cost=rate)

def test_api_contract_permissions_validation_and_cors():
    class Client:
        data=context()
        def session(self,*args):return self.data
    class Fake:
        def assignments(self,*args):return {'data':[],'meta':{'total':0,'limit':25,'offset':0}}
        def eligible(self,*args):return {'data':[],'meta':{'total':0,'limit':20,'offset':0}}
        def save(self,a,kind,id_,division,payload,*args):
            row={kind+'_id':id_,'division_ref_id':division,'revision':1,'status':payload.status}
            return {**row,'hourly_cost':str(payload.hourly_cost),'cost_center_ref_id':payload.cost_center_ref_id} if kind=='position' else {**row,'labor_position_id':'role'}
    authority=Client();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic','Idempotency-Key':'test-assignment'}
        assert http.options('/v1/hr/positions/p/division-assignments/d',headers={'Origin':'http://127.0.0.1:4173','Access-Control-Request-Method':'PUT','Access-Control-Request-Headers':'content-type,x-tenant-id,x-correlation-id,idempotency-key,authorization'}).status_code==200
        assert http.get('/v1/hr/organization/divisions',headers=headers).status_code==200
        for kind in ('position','worker'):
            path=f'/v1/hr/{kind}s/resource/division-assignments'
            payload={'expected_revision':0,**({'hourly_cost':'0'} if kind=='position' else {})}
            assert http.get(path,headers=headers).status_code==200
            assert http.get('/v1/hr/division-'+kind+'s?division_id=division-a',headers=headers).status_code==200
            assert http.put(path+'/division-a',headers=headers,json=payload).status_code==200
            assert http.put(path+'/division-a',headers=headers,json={**payload,'unknown':'secret'}).status_code==422
            assert http.put(path+'/division-a',headers={k:v for k,v in headers.items() if k!='Idempotency-Key'},json=payload).status_code==400
            authority.data['permissions']=['hr.'+kind+'.read']
            assert http.put(path+'/division-a',headers=headers,json=payload).status_code==403
            assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code==401
            authority.data=context()
        response=http.put('/v1/hr/positions/p/division-assignments/d',headers=headers,json={'expected_revision':0,'hourly_cost':'secret'})
        assert response.status_code==422 and 'secret' not in response.text
        assert response.json()['error']['details']['issues'][0]['field']=='hourly_cost'
    finally:app.dependency_overrides.clear()


@pytest.mark.parametrize('societies', [(), ({'id':'society-a'},), ({'id':'society-a','base_currency':'usd'},), ({'id':'foreign','base_currency':'MXN'},)])
def test_tariff_authority_fails_closed_without_current_society_currency(societies):
    with pytest.raises(ErclaveError) as exc:
        Store.tariff_context(replace(access(), societies=societies), 'division-a')
    assert exc.value.code == 'assignment_authority_unavailable'


def test_tariff_context_never_uses_foreign_or_revoked_division():
    assert Store.tariff_context(access(), 'division-b') == ('society-b', 'USD')
    with pytest.raises(ErclaveError) as exc:
        Store.tariff_context(replace(access(), divisions=(DIVISIONS[0],)), 'division-b')
    assert exc.value.code == 'assignment_division_denied'


class TariffConnection:
    def __init__(self, before=None):
        self.before = before
        self.writes = []
    def execute(self, statement, params):
        sql = str(statement)
        if sql.startswith('select id,status,labor_area_id'):
            self.row = {'id':'role','status':'active','labor_area_id':'area'}
        elif sql.startswith('select * from hr.position_division_assignments'):
            self.row = self.before
        elif sql.startswith('select status from hr.labor_areas'):
            self.row = 'active'
        else:
            self.writes.append((sql, params))
            self.row = None
        return self
    def mappings(self): return self
    def first(self): return self.row
    def scalar(self): return self.row
    @contextmanager
    def begin(self): yield self

class TariffRepository:
    def __init__(self, before=None, replay=None):
        self.engine = TariffConnection(before)
        self.replay = replay
        self.audits = []
    def _claim(self, *args): return self.replay
    def _audit(self, *args): self.audits.append(args[-1])
    def _done(self, *args): pass

@pytest.mark.parametrize('currency,code', [(None,'hr_tariff_currency_required'), ('USD','hr_tariff_currency_mismatch')])
def test_tariff_confirmation_rejects_missing_or_foreign_currency_before_writing(currency, code):
    repo = TariffRepository()
    payload = schemas.PositionDivisionCommand(expected_revision=0, hourly_cost='12.345678', hourly_cost_currency_code=currency)
    with pytest.raises(ErclaveError) as exc:
        Store(repo).save(access(), 'position', 'role', 'division-a', payload, 'confirm-tariff', 'test', NoCosting())
    assert exc.value.code == code
    assert exc.value.details['field'] == 'hourly_cost_currency_code'
    assert not repo.engine.writes and not repo.audits


def test_tariff_confirmation_preserves_decimal_and_records_authority_and_audit():
    from decimal import Decimal
    repo = TariffRepository()
    payload = schemas.PositionDivisionCommand(expected_revision=0, hourly_cost='12.345678', hourly_cost_currency_code='MXN')
    result = Store(repo).save(access(), 'position', 'role', 'division-a', payload, 'confirm-tariff', 'test', NoCosting())
    assert result['hourly_cost'] == '12.345678'
    assert result['hourly_cost_currency_code'] == 'MXN'
    assert result['hourly_cost_society_ref_id'] == 'society-a'
    assert result['hourly_cost_confirmed_at']
    assert repo.engine.writes[0][1]['hourly_cost'] == Decimal('12.345678')
    assert repo.audits[0]['after'] == result


def test_old_idempotent_reply_remains_unconfirmed_and_authorization_still_applies():
    old = {'position_id':'role','division_ref_id':'division-a','hourly_cost':'12','status':'active','revision':1}
    repo = TariffRepository(replay=old)
    command = schemas.PositionDivisionCommand(expected_revision=0, hourly_cost='12')
    assert Store(repo).save(access(), 'position','role','division-a',command,'old-command','test',NoCosting()) == old
    with pytest.raises(ErclaveError):
        Store(repo).save(replace(access(),divisions=()),'position','role','division-a',command,'old-command','test',NoCosting())
    assert not repo.engine.writes


def test_deactivation_preserves_confirmed_and_unconfirmed_tariff_history():
    from datetime import datetime, timezone
    for confirmed in (False, True):
        before = {'position_id':'role','division_ref_id':'division-a','hourly_cost':'12','status':'active','revision':1,
                  'hourly_cost_currency_code':'MXN' if confirmed else None,
                  'hourly_cost_society_ref_id':'society-a' if confirmed else None,
                  'hourly_cost_confirmed_at':datetime(2026,10,7,tzinfo=timezone.utc) if confirmed else None}
        repo = TariffRepository(before)
        command = schemas.PositionDivisionCommand(expected_revision=1,hourly_cost='12',status='inactive')
        result = Store(repo).save(replace(access(),societies=()),'position','role','division-a',command,'deactivate','test',NoCosting())
        assert result['hourly_cost_currency_code'] == before['hourly_cost_currency_code']
        assert result['hourly_cost_society_ref_id'] == before['hourly_cost_society_ref_id']
        assert result['status'] == 'inactive'


def test_postgres_division_capacity_keeps_shared_worker_identity_and_confirmed_tariff(local_store):
    from decimal import Decimal
    store,conn,area,position,worker = local_store
    for division in ('division-a','division-b'):
        save(store,'position',position,division,payload={'expected_revision':0,'hourly_cost':'120'})
        save(store,'worker',worker,division)
    first = store.division_production_capacity(access(),'division-a')
    second = store.division_production_capacity(access(),'division-b')
    a = first['data'][0]; b = second['data'][0]
    assert a['eligible_worker_ids'] == b['eligible_worker_ids'] == [worker]
    assert a['capacity_pool_key'] == b['capacity_pool_key'] == position
    assert a['active_worker_count'] == b['active_worker_count'] == 1
    assert a['available_minutes'] == a['minutes_per_worker']
    assert a['hourly_cost_currency_code'] == 'MXN' and b['hourly_cost_currency_code'] == 'USD'
    assert a['cost_per_minute'] == Decimal('2')
    assert first['meta'] == {'capacity_scope':'shared_workers','commitments_included':False}
    assert not {'curp','rfc','nss','full_name'} & a.keys()
    # A currency/society change never silently relabels confirmed money.
    changed = replace(access(), societies=({'id':'society-a','base_currency':'EUR'},{'id':'society-b','base_currency':'USD'}))
    assert store.division_production_capacity(changed,'division-a')['data'] == []
    assert store.eligible(changed,'position','division-a','production','',25,0)['data'] == []
    conn.execute(text('update hr.position_division_assignments set hourly_cost_currency_code=null,hourly_cost_society_ref_id=null,hourly_cost_confirmed_at=null where tenant_id=:t and position_id=:p and division_ref_id=:d'),{'t':TENANT,'p':position,'d':'division-a'})
    assert store.division_production_capacity(access(),'division-a')['data'] == []
    assert store.assignments(access(),'position',position,25,0,'division-a')['data'][0]['hourly_cost_currency_code'] is None
    assert store.eligible(access(),'worker','division-a','production','',25,0)['data'][0]['id'] == worker
    conn.execute(text("update hr.workers set status='inactive' where tenant_id=:t and id=:w"),{'t':TENANT,'w':worker})
    assert store.division_production_capacity(access(),'division-b')['data'][0]['eligible_worker_ids'] == []
    assert store.division_production_capacity(access(),'division-b')['data'][0]['available_minutes'] == 0

def test_postgres_maintenance_worker_lookup_requires_confirmed_current_tariff(local_store):
    from decimal import Decimal
    store,conn,area,position,worker = local_store
    conn.execute(text('update hr.labor_roles set intervenes_in_maintenance=true where tenant_id=:t and id=:p'), {'t':TENANT,'p':position})
    save(store,'position',position,payload={'expected_revision':0,'hourly_cost':'12.345678'})
    save(store,'worker',worker)
    rows=store.eligible(access(),'worker','division-a','maintenance','Synthetic',20,0,worker)['data']
    assert len(rows)==1
    row=rows[0]
    assert row['id']==worker and row['hourly_cost']==Decimal('12.345678')
    assert row['hourly_cost_currency_code']=='MXN' and row['hourly_cost_society_ref_id']=='society-a'
    assert row['worker_assignment_revision']==row['position_assignment_revision']==1
    assert row['minutes_per_worker']>0 and row['hourly_cost_confirmed_at'] is not None
    assert not {'curp','rfc','nss'} & row.keys()
    changed=replace(access(),societies=({'id':'society-a','base_currency':'EUR'},{'id':'society-b','base_currency':'USD'}))
    assert store.eligible(changed,'worker','division-a','maintenance','',20,0,worker)['data']==[]
    conn.execute(text('update hr.position_division_assignments set hourly_cost_currency_code=null,hourly_cost_society_ref_id=null,hourly_cost_confirmed_at=null where tenant_id=:t and position_id=:p and division_ref_id=:d'),{'t':TENANT,'p':position,'d':'division-a'})
    assert store.eligible(access(),'worker','division-a','maintenance','',20,0,worker)['data']==[]


def test_postgres_tariff_constraint_and_downgrade_preserve_confirmation_audit(local_store, monkeypatch):
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    store,conn,area,position,worker = local_store
    save(store,'position',position)
    with pytest.raises(DBAPIError, match='ck_hr_position_assignment_currency'):
        with conn.begin_nested():
            conn.execute(text('update hr.position_division_assignments set hourly_cost_currency_code=null where tenant_id=:t and position_id=:p'),{'t':TENANT,'p':position})
    path=ROOT.parents[1]/'alembic/versions/20261007_0051_resource_tariff_currency.py'
    spec=importlib.util.spec_from_file_location('hr_tariff_migration',path)
    migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    monkeypatch.setattr(migration, 'op', Operations(MigrationContext.configure(conn)))
    with pytest.raises(DBAPIError, match='Confirmed tariff currency history exists'):
        with conn.begin_nested(): migration.downgrade()
    # Even if current row is absent, historical confirmation must block erasure.
    conn.execute(text('delete from hr.position_division_assignments where tenant_id=:t and position_id=:p'),{'t':TENANT,'p':position})
    with pytest.raises(DBAPIError, match='Confirmed tariff currency history exists'):
        with conn.begin_nested(): migration.downgrade()


def test_division_capacity_api_requires_current_authority_and_minimizes_response():
    class Client:
        data = context()
        def session(self,*args): return self.data
    class Fake:
        def division_production_capacity(self, access, division):
            access.division(division)
            return {'data':[], 'meta':{'capacity_scope':'shared_workers','commitments_included':False}}
    authority=Client();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app)
        headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic'}
        path='/v1/hr/division-production-capacity?division_id=division-a'
        assert http.get(path,headers=headers).json() == {'data':[],'meta':{'capacity_scope':'shared_workers','commitments_included':False}}
        assert http.get('/v1/hr/division-production-capacity',headers=headers).status_code == 422
        assert http.get(path,headers={'X-Tenant-Id':TENANT}).status_code == 401
        authority.data={**context(),'permissions':[]}
        assert http.get(path,headers=headers).status_code == 403
        authority.data={**context(),'permissions':['production.order.validate']}
        assert http.get(path,headers=headers).status_code == 403
        authority.data['active_modules'].append('production')
        assert http.get(path,headers=headers).status_code == 200
        authority.data['scope']['divisions']=[]
        assert http.get(path,headers=headers).status_code == 403
        authority.data={**context(),'tenant':{'id':'foreign','status':'active'}}
        assert http.get(path,headers=headers).status_code == 403
    finally: app.dependency_overrides.clear()


def test_postgres_pre_currency_idempotency_hash_replays_without_reinterpreting_money(local_store):
    import hashlib,json
    store,conn,area,position,worker=local_store
    key='legacy-'+uuid4().hex
    data={'expected_revision':0,'status':'active','hourly_cost':'12','cost_center_ref_id':None}
    digest=hashlib.sha256(json.dumps({'actor':access().actor_id,'payload':data},sort_keys=True).encode()).hexdigest()
    old={'position_id':position,'division_ref_id':'division-a','hourly_cost':'12','status':'active','revision':1,'cost_center_ref_id':None,'cost_center_snapshot':None}
    conn.execute(text('insert into hr.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash,response_payload) values(:id,:t,:o,:k,:h,cast(:p as jsonb))'),{'id':'ide_'+uuid4().hex[:26],'t':TENANT,'o':f'org_assignment.position:{position}:division-a','k':key,'h':digest,'p':json.dumps(old)})
    result=store.save(access(),'position',position,'division-a',schemas.PositionDivisionCommand(expected_revision=0,hourly_cost='12'),key,'test',NoCosting())
    assert result==old and 'hourly_cost_currency_code' not in result
    assert store.assignments(access(),'position',position,25,0)['data']==[]


@pytest.mark.parametrize('permission', ['production.order.validate','production.order.release','production.order.start','production.order.resume'])
def test_production_worker_lookup_requires_productive_purpose_and_active_modules(permission):
    class Client:
        data = {**context(), 'permissions':[permission], 'active_modules':['admin','hr','production']}
        def session(self,*args): return self.data
    class Fake:
        def eligible(self, access, kind, division, purpose, q, limit, offset, resource_id):
            access.division(division)
            assert kind == 'worker' and purpose == 'production'
            return {'data':[], 'meta':{'total':0,'limit':limit,'offset':offset}}
    authority=Client(); app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app); headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic'}
        path='/v1/hr/division-workers?division_id=division-a'
        assert http.get(path+'&purpose=production',headers=headers).status_code == 200
        assert http.get(path,headers=headers).status_code == 403
        assert http.get(path+'&purpose=maintenance',headers=headers).status_code == 403
        assert http.get(path+'&purpose=production',headers={'X-Tenant-Id':TENANT}).status_code == 401
        authority.data['active_modules']=['admin','hr']
        assert http.get(path+'&purpose=production',headers=headers).status_code == 403
        authority.data['active_modules']=['admin','hr','production']
        authority.data['scope']={**authority.data['scope'],'divisions':[]}
        assert http.get(path+'&purpose=production',headers=headers).status_code == 403
    finally: app.dependency_overrides.clear()

@pytest.mark.parametrize('permission', ['maintenance.order.assign','maintenance.order.start','maintenance.order.resume','maintenance.order.reopen','maintenance.time.create'])
def test_maintenance_worker_lookup_requires_maintenance_purpose_and_active_modules(permission):
    class Client:
        data={**context(),'permissions':[permission],'active_modules':['admin','hr','maintenance']}
        def session(self,*args):return self.data
    class Fake:
        def eligible(self,access,kind,division,purpose,q,limit,offset,resource_id):
            access.division(division)
            assert kind=='worker' and purpose=='maintenance'
            return {'data':[],'meta':{'total':0,'limit':limit,'offset':offset}}
    authority=Client();app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:authority
    app.dependency_overrides[api.store]=lambda:Fake()
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic'}
        path='/v1/hr/division-workers?division_id=division-a&purpose=maintenance'
        assert http.get(path,headers=headers).status_code==200
        assert http.get(path.replace('maintenance','production'),headers=headers).status_code==403
        authority.data['active_modules']=['admin','hr']
        assert http.get(path,headers=headers).status_code==403
        authority.data['active_modules']=['admin','hr','maintenance']
        authority.data['scope']={**authority.data['scope'],'divisions':[],'all_divisions':False}
        assert http.get(path,headers=headers).status_code==403
    finally:app.dependency_overrides.clear()

def test_sales_permission_cannot_query_maintenance_worker_tariff():
    class Client:
        data={**context(),'permissions':['sales.quote.update'],'active_modules':['admin','hr','sales','maintenance']}
        def session(self,*args):return self.data
    app=main.app
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase')
    app.dependency_overrides[get_organization_client]=lambda:Client()
    try:
        response=TestClient(main.app).get('/v1/hr/division-workers?division_id=division-a&purpose=maintenance',headers={'X-Tenant-Id':TENANT,'Authorization':'Bearer synthetic'})
        assert response.status_code==403
    finally:app.dependency_overrides.clear()
