"""CC16 Local demo tenant integration; owned fixtures rollback or clean up."""
import importlib,os,sys
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from erclave_common.organization_client import OrganizationAccess
from erclave_common.errors import ErclaveError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repos=importlib.import_module('app.repositories');schemas=importlib.import_module('app.schemas');api=importlib.import_module('app.api');dc=importlib.import_module('app.document_context');ic=importlib.import_module('app.inventory_context');reports=importlib.import_module('app.reports')
URL=os.getenv('ERCLAVE_TEST_DATABASE_URL','');TENANT='ten_739ee59d765d5e14818674800d'

def configuration():
    suffix=uuid4().hex[:14]
    division={'id':'cc16-div-'+suffix,'society_id':'cc16-soc-'+suffix,'code':'TEST','name':'Synthetic'}
    scope=OrganizationAccess(TENANT,'cc16-'+suffix,('maintenance.order.create',),(division,),False,False,societies=({'id':division['society_id'],'base_currency':'MXN'},))
    payload=schemas.OrderCreate(code='CC16-'+suffix,target_type='facility',title='Synthetic test',description='Synthetic test only',location='Local',division_ref_id=division['id'])
    context=dc.create_context(payload,scope)
    worker={'id':'worker-'+suffix,'full_name':'Synthetic technician','labor_position_id':'position-'+suffix,'position_name':'Maintenance','division_ref_id':division['id'],'society_ref_id':division['society_id'],'hourly_cost':'123.123456','hourly_cost_currency_code':'MXN','hourly_cost_confirmed_at':'2026-01-01T00:00:00Z','minutes_per_worker':480,'worker_assignment_revision':1,'position_assignment_revision':2}
    return SimpleNamespace(suffix=suffix,scope=scope,actor=scope.actor_id,payload=payload,context=context,worker=worker)

def make_order(f,code='one',dimensioned=True):
    snapshots={'machine_code_snapshot':None,'machine_name_snapshot':None,'source_production_order_code_snapshot':None}
    if dimensioned:snapshots['organization_context']=f.context
    return f.repo.create_order(TENANT,f.payload.model_copy(update={'code':f.payload.code+'-'+code}),snapshots,f.suffix+'-'+code,'create-'+code,f.actor,organization_access=f.scope if dimensioned else None)

def assign(f,order,dimensioned=True):
    for action in ('request','assign'):
        f.repo.transition(TENANT,order['id'],schemas.TransitionRequest(transition=action,assigned_worker_id=f.worker['id'] if action=='assign' else None),f.worker if action=='assign' else None,f.suffix+'-'+order['id']+'-'+action,action,f.actor,organization_access=f.scope if dimensioned else None)
    return f.repo.get_order(TENANT,order['id'])

def entry(f,start='2026-01-02T08:00:00Z',end='2026-01-02T09:00:00Z'):
    return schemas.TimeEntryCreate(worker_id=f.worker['id'],started_at=start,ended_at=end,expected_position_assignment_revision=2)

@pytest.fixture
def pg():
    if not URL:pytest.skip('Local PostgreSQL required')
    url=make_url(URL);assert url.host=='127.0.0.1' and url.port==5434 and url.database=='erclave_local' and not url.query
    f=configuration();repo=repos.MaintenanceRepository(URL);engine=repo.engine;f.repo=repo
    with engine.connect() as c:
        tx=c.begin()
        class Transaction:
            @contextmanager
            def connect(self):yield c
            @contextmanager
            def begin(self):yield c
        repo.engine=Transaction();f.c=c
        try:
            assert c.execute(text('select id from admin.tenants')).scalars().all()==[TENANT]
            yield f
        finally:tx.rollback()
    engine.dispose()

def test_order_context_inherits_source_and_machine_must_match():
    f=configuration()
    assert dc.create_context(f.payload,f.scope)==f.context
    source={'organization_context':f.context}
    assert dc.create_context(f.payload.model_copy(update={'division_ref_id':None}),f.scope,{'division_ref_id':f.context['division_ref_id']},source)==f.context
    with pytest.raises(ErclaveError):dc.create_context(f.payload,f.scope,{'division_ref_id':'foreign'},source)
    with pytest.raises(ErclaveError) as exc:dc.create_context(f.payload.model_copy(update={'division_ref_id':None}),f.scope)
    assert exc.value.code=='maintenance_document_context_required'

def test_time_exact_decimal_zero_rate_revision_and_timezone():
    f=configuration();p=entry(f,end='2026-01-02T08:01:01.500000Z')
    snapshot=dc.labor_snapshot(f.worker,f.context,p)
    assert snapshot['duration_seconds']=='61.5' and snapshot['labor_cost']=='2.103359'
    assert snapshot['position_code'] is None
    assert dc.labor_snapshot({**f.worker,'position_code':'PUE-000001'},f.context,p)['position_code']=='PUE-000001'
    assert dc.labor_snapshot({**f.worker,'hourly_cost':'0'},f.context,p)['labor_cost']=='0.000000'
    with pytest.raises(ErclaveError) as exc:dc.labor_snapshot({**f.worker,'position_assignment_revision':3},f.context,p)
    assert exc.value.code=='maintenance_worker_tariff_changed'
    with pytest.raises(ValueError,match='maintenance_time_timezone_required'):entry(f,start='2026-01-02T08:00:00')

def test_pg_context_snapshot_time_replay_scope_and_reports(pg):
    f=pg;f.worker={**f.worker,'position_code':'PUE-000001'};order=assign(f,make_order(f))
    assert order['organization_context']==f.context and order['assignments'][0]['worker_context_snapshot']==f.worker
    first=f.repo.create_time(TENANT,order['id'],entry(f),f.worker,f.suffix+'-time','time',f.actor,organization_access=f.scope)
    assert first['labor_cost_snapshot']['labor_cost']=='123.123456'
    assert first['labor_cost_snapshot']['position_code']=='PUE-000001'
    replay=f.repo.create_time(TENANT,order['id'],entry(f),{**f.worker,'hourly_cost':'999'},f.suffix+'-time','time',f.actor,organization_access=f.scope)
    assert replay['labor_cost_snapshot']==first['labor_cost_snapshot']
    denied=replace(f.scope,divisions=())
    with pytest.raises(ErclaveError):f.repo.create_time(TENANT,order['id'],entry(f),f.worker,f.suffix+'-time','time',f.actor,organization_access=denied)
    assert not f.repo.list_orders(TENANT,divisions=[])
    for report in reports.REPORT_PERMISSIONS:assert reports.build_report(f.repo,TENANT,report,{'divisions':[]}).rows==[]
    visible=reports.build_report(f.repo,TENANT,'labor-times',{'divisions':[f.context['division_ref_id']]}).rows
    row=next(row for row in visible if row['order_code']==order['code'])
    assert row['cost_currency']=='MXN' and row['labor_cost']=='123.123456'

def test_pg_global_worker_overlap_capacity_and_midnight_split(pg):
    f=pg;a=assign(f,make_order(f,'a'));b=assign(f,make_order(f,'b'))
    worker={**f.worker,'minutes_per_worker':60}
    f.repo.create_time(TENANT,a['id'],entry(f,end='2026-01-02T08:40:00Z'),worker,f.suffix+'-first','first',f.actor,organization_access=f.scope)
    with pytest.raises(ValueError,match='maintenance_time_overlap'):f.repo.create_time(TENANT,b['id'],entry(f,start='2026-01-02T08:20:00Z'),worker,f.suffix+'-overlap','overlap',f.actor,organization_access=f.scope)
    with pytest.raises(ErclaveError) as exc:f.repo.create_time(TENANT,b['id'],entry(f,start='2026-01-02T09:00:00Z',end='2026-01-02T09:30:00Z'),worker,f.suffix+'-capacity','capacity',f.actor,organization_access=f.scope)
    assert exc.value.code=='maintenance_worker_daily_capacity_exceeded'
    result=f.repo.create_time(TENANT,b['id'],entry(f,start='2026-01-03T23:30:00Z',end='2026-01-04T00:30:00Z'),worker,f.suffix+'-midnight','midnight',f.actor,organization_access=f.scope)
    assert result['labor_cost_snapshot']['duration_seconds']=='3600'

def test_pg_api_time_replay_tariff_revision_actor_and_revoked_scope(pg):
    f=pg;order=assign(f,make_order(f));calls=[]
    authority=SimpleNamespace(organization_access=lambda *args:f.scope,division_workers=lambda *args,**kwargs:calls.append(kwargs) or [f.worker])
    access=api.AuthorizedContext(TENANT,f.actor,'maintenance.time.create',frozenset({'maintenance.time.create'}))
    payload=entry(f)
    stale=payload.model_copy(update={'expected_position_assignment_revision':1})
    with pytest.raises(ErclaveError) as exc:api.create_time(order['id'],stale,TENANT,None,f.suffix+'-stale',f.repo,authority,access)
    assert exc.value.code=='maintenance_worker_tariff_changed'
    assert not f.repo.get_order(TENANT,order['id'])['time_entries']
    first=api.create_time(order['id'],payload,TENANT,None,f.suffix+'-api',f.repo,authority,access).data
    count=len(calls);authority.division_workers=lambda *args,**kwargs:pytest.fail('Replay must not reread or reprice RH')
    replay=api.create_time(order['id'],payload,TENANT,None,f.suffix+'-api',f.repo,authority,access).data
    assert replay['labor_cost_snapshot']==first['labor_cost_snapshot'] and len(calls)==count
    other=api.AuthorizedContext(TENANT,'other-'+f.actor,'maintenance.time.create',frozenset({'maintenance.time.create'}))
    with pytest.raises(ErclaveError) as exc:api.create_time(order['id'],payload,TENANT,None,f.suffix+'-api',f.repo,authority,other)
    assert exc.value.code=='idempotency_key_reused'
    authority.organization_access=lambda *args:replace(f.scope,divisions=())
    with pytest.raises(ErclaveError) as exc:api.create_time(order['id'],payload,TENANT,None,f.suffix+'-api',f.repo,authority,access)
    assert exc.value.code=='assignment_division_denied'
    assert len(f.repo.get_order(TENANT,order['id'])['time_entries'])==1

def test_pg_api_creation_replay_does_not_rederive_changed_society_currency(pg):
    f=pg;authority=SimpleNamespace(organization_access=lambda *args:f.scope,allocate_order_code=lambda *args:{'code':f.payload.code,'mode':'manual'})
    access=api.AuthorizedContext(TENANT,f.actor,'maintenance.order.create',frozenset({'maintenance.order.create'}))
    first=api.create_order(f.payload,TENANT,None,f.suffix+'-api',f.repo,authority,access).data
    authority.organization_access=lambda *args:replace(f.scope,societies=({'id':f.context['society_ref_id'],'base_currency':'CAD'},))
    replay=api.create_order(f.payload,TENANT,None,f.suffix+'-api',f.repo,authority,access).data
    assert replay['id']==first['id'] and replay['organization_context']['cost_currency']=='MXN'

def test_pg_new_material_request_replay_binds_actor_preserving_cc14_hashes(pg,monkeypatch):
    f=pg;order=assign(f,make_order(f));calls=[]
    authority=SimpleNamespace(organization_access=lambda *args:f.scope,warehouse=lambda *args:{'id':'warehouse-test','name':'Test','status':'active','type':'spare_parts','division_ref_id':f.context['division_ref_id']},item=lambda *args:{'id':'item-test','code':'ITEM','name':'Item','status':'active','base_unit':'H87'},reserve=lambda *args:calls.append(args) or {'id':'res-'+f.suffix,'unit_cost_snapshot':Decimal('1')})
    monkeypatch.setattr(ic,'organization_access',lambda *args:f.scope)
    payload=schemas.MaterialRequestCreate(warehouse_id='warehouse-test',lines=[{'item_id':'item-test','quantity':1,'unit_code':'H87'}])
    access=api.AuthorizedContext(TENANT,f.actor,'maintenance.material_request.create',frozenset({'maintenance.material_request.create'}))
    first=api.create_material_request_locked(order['id'],payload,TENANT,None,f.suffix+'-api-material',f.repo,authority,access).data
    replay=api.create_material_request_locked(order['id'],payload,TENANT,None,f.suffix+'-api-material',f.repo,authority,access).data
    assert replay['id']==first['id'] and len(calls)==1
    with pytest.raises(ErclaveError) as exc:api.create_material_request_locked(order['id'],payload,TENANT,None,f.suffix+'-api-material',f.repo,authority,api.AuthorizedContext(TENANT,'other-'+f.actor,'maintenance.material_request.create',frozenset({'maintenance.material_request.create'})))
    assert exc.value.code=='idempotency_key_reused' and len(calls)==1

def test_pg_legacy_read_cancel_only_and_no_new_material_context(pg):
    f=pg;order=make_order(f,dimensioned=False);full=replace(f.scope,all_divisions=True)
    with pytest.raises(ErclaveError):dc.authorize_order(order,f.scope,legacy=True)
    dc.authorize_order(order,full,legacy=True)
    with pytest.raises(ErclaveError) as exc:f.repo.update_order(TENANT,order['id'],schemas.OrderUpdate(title='Changed title'),f.suffix+'-edit','edit',f.actor,organization_access=full)
    assert exc.value.code=='maintenance_document_history_review_required'
    cancelled=f.repo.transition(TENANT,order['id'],schemas.TransitionRequest(transition='cancel',reason='Synthetic cancel'),None,f.suffix+'-cancel','cancel',f.actor,organization_access=full)
    assert cancelled['status']=='cancelled'

def test_pg_material_context_frozen_and_rejects_other_division(pg):
    f=pg;order=assign(f,make_order(f));authority=SimpleNamespace(organization_access=lambda *args:replace(f.scope,societies=({'id':f.context['society_ref_id'],'base_currency':'CAD'},)))
    assert ic.material_context({'division_ref_id':f.context['division_ref_id']},order,authority,TENANT,None,f.actor)==f.context
    with pytest.raises(ErclaveError):ic.material_context({'division_ref_id':'foreign'},order,authority,TENANT,None,f.actor)
    p=schemas.MaterialRequestCreate(warehouse_id='warehouse-test',lines=[{'item_id':'item-test','quantity':1,'unit_code':'H87'}])
    snapshots={'warehouse_name':'Test','items':[{'code':'ITEM','name':'Item'}],'organization_context':{**f.context,'division_ref_id':'foreign'}}
    with pytest.raises(ErclaveError):f.repo.prepare_material_request(TENANT,order['id'],p,snapshots,f.suffix+'-material','material',f.actor,organization_access=f.scope)

def test_pg_downgrade_blocks_history_before_schema_drop(pg,monkeypatch):
    from sqlalchemy.exc import DBAPIError
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    f=pg;make_order(f)
    path=Path(__file__).resolve().parents[3]/'alembic/versions/20261012_0059_maintenance_documents.py'
    spec=importlib.util.spec_from_file_location('cc16_history_proof',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    operations=Operations(MigrationContext.configure(f.c));monkeypatch.setattr(migration,'op',operations)
    for method in ('drop_index','drop_column','drop_constraint'):monkeypatch.setattr(operations,method,lambda *args,**kwargs:pytest.fail('history must block before drop'))
    with pytest.raises(DBAPIError,match='CC16 history exists'):
        with f.c.begin_nested():
            f.c.execute(text("set local lock_timeout='2s'"));migration.downgrade()
    assert f.c.execute(text("select 1 from information_schema.columns where table_schema='maintenance' and table_name='time_entries' and column_name='labor_cost_snapshot'")).scalar()==1

def test_pg_concurrent_worker_capacity_across_orders():
    if not URL:pytest.skip('Local PostgreSQL required')
    url=make_url(URL);assert url.host=='127.0.0.1' and url.port==5434 and url.database=='erclave_local' and not url.query
    f=configuration();f.repo=repos.MaintenanceRepository(URL);ids=[]
    try:
        with f.repo.engine.connect() as c:assert c.execute(text('select id from admin.tenants')).scalars().all()==[TENANT]
        for code in ('a','b'):
            order=make_order(f,code);ids.append(order['id']);assign(f,order)
        barrier=Barrier(2);worker={**f.worker,'minutes_per_worker':60}
        def capture(index):
            barrier.wait(timeout=10)
            try:
                p=entry(f,start=f'2026-01-02T{8+index:02d}:00:00Z',end=f'2026-01-02T{8+index:02d}:40:00Z')
                f.repo.create_time(TENANT,ids[index],p,worker,f.suffix+'-race-'+str(index),'race'+str(index),f.actor,organization_access=f.scope)
                return 'created'
            except ErclaveError as exc:return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(capture,[0,1]))
        assert sorted(results)==['created','maintenance_worker_daily_capacity_exceeded']
        with f.repo.engine.connect() as c:assert c.execute(text('select count(*) from maintenance.time_entries where tenant_id=:t and order_id=any(:ids)'),{'t':TENANT,'ids':ids}).scalar()==1
    finally:
        with f.repo.engine.begin() as c:
            for table in ('time_entries','assignments'):c.execute(text(f'delete from maintenance.{table} where tenant_id=:t and order_id=any(:ids)'),{'t':TENANT,'ids':ids})
            c.execute(text('delete from maintenance.orders where tenant_id=:t and id=any(:ids)'),{'t':TENANT,'ids':ids})
            c.execute(text('delete from maintenance.audit_events where tenant_id=:t and actor_id=:a'),{'t':TENANT,'a':f.actor})
            c.execute(text('delete from maintenance.idempotency_records where tenant_id=:t and idempotency_key like :prefix'),{'t':TENANT,'prefix':f.suffix+'%'})
        f.repo.engine.dispose()
