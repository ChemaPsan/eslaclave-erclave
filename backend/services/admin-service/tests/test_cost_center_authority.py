from pathlib import Path
import sys
from uuid import uuid4
import pytest
from sqlalchemy import text,select
from erclave_common.errors import ErclaveError
from app.schemas import CodeSequenceNextRequest,CodeSequenceUpdateRequest,CodeSequenceAllocationRead
from app.main import app
from app.auth import AuthenticatedActor,get_authenticated_actor
from app.repositories import AdminRepository,get_admin_repository
from erclave_common.config import Settings,get_settings
from fastapi.testclient import TestClient
from test_admin_api import FakeAdminRepository,TENANT_ID
from app.seeds.permissions import derive_permission_seed,BASIC_COST_CENTER_PERMISSIONS
from test_organization_commands import store,TransactionEngine,TENANT,hierarchy
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'costing-service'))
from costing_app.repository import Repository
from costing_app.authority import Access
from costing_app.models import centers,receipts,audit

def test_only_basic_permissions_use_admin_entitlement():
    for code in BASIC_COST_CENTER_PERMISSIONS:
        seed=derive_permission_seed(code,'admin','test')
        assert seed.module_code=='admin' and seed.assignable_to_tenant_role
    assert derive_permission_seed('costing.analysis.read','costing','test').module_code=='costing'
    assert derive_permission_seed('accounting.journal.read','accounting','test').module_code=='accounting'

def test_postgres_cost_center_ownership_scope_idempotency_history(store):
    conn=store.test_connection
    for table in (audit,receipts,centers):conn.execute(table.delete().where(table.c.tenant_id==TENANT))
    _,_,division=hierarchy(store)
    repo=Repository(TransactionEngine(conn))
    from_admin=AdminRepository(TransactionEngine(conn))
    calls=[]
    class Codes:
        def code(self,tenant,authorization,actor,key):
            calls.append(key)
            return from_admin.allocate_business_code(tenant,'costing.cost_center',CodeSequenceNextRequest(),key,'cost-center-test').code
    authority=Codes();access=Access(TENANT,'actor',(division['id'],),False,(division['id'],))
    key='test-'+uuid4().hex;payload={'name':'Synthetic 100% center','division_ref_id':division['id']}
    first=repo.command(access,'create',payload,key,'test',authority)
    assert first==repo.command(access,'create',payload,key,'test',authority)
    assert len(calls)==1
    assert first['code'].startswith('CC-')
    with pytest.raises(ErclaveError) as exc:repo.command(access,'create',{**payload,'name':'Other'},key,'test',authority)
    assert exc.value.code=='idempotency_key_reused'
    assert repo.list(access,q='%')['meta']['total']==1
    assert repo.list(access,q='_')['meta']['total']==0
    assert repo.list(Access(TENANT,'actor',(),False,()))['data']==[]
    with pytest.raises(ErclaveError) as exc:repo.read(Access('foreign','actor',(),True,()),first['id'])
    assert exc.value.status_code==404
    with pytest.raises(ErclaveError):repo.read(Access(TENANT,'actor',(),False,()),first['id'])
    update={'name':'Renamed','expected_revision':1};k2='test-'+uuid4().hex
    changed=repo.command(access,'update',update,k2,'test',authority,id_=first['id'])
    assert changed['code']==first['code'] and changed['revision']==2
    assert changed==repo.command(access,'update',update,k2,'test',authority,id_=first['id'])
    with pytest.raises(ErclaveError) as exc:repo.command(access,'update',update,'test-'+uuid4().hex,'test',authority,id_=first['id'])
    assert exc.value.code=='cost_center_revision_conflict'
    inactive=repo.command(access,'deactivate',{'expected_revision':2},'test-'+uuid4().hex,'test',authority,id_=first['id'])
    assert inactive['status']=='inactive' and repo.list(access,status='active')['data']==[]
    assert repo.read(access,first['id'])['revision']==3
    historical=Access(TENANT,'actor',(),True,())
    with pytest.raises(ErclaveError):repo.command(historical,'activate',{'expected_revision':3},'test-'+uuid4().hex,'test',authority,id_=first['id'])
    assert repo.read(historical,first['id'])['status']=='inactive'
    assert conn.execute(select(audit.c.id).where(audit.c.tenant_id==TENANT)).all().__len__()==3
    seq=conn.execute(text("select id from admin.code_sequences where tenant_id=:tenant and document_type='costing.cost_center'"),{'tenant':TENANT}).scalar_one()
    with pytest.raises(ErclaveError) as exc:from_admin.update_code_sequence(TENANT,seq,CodeSequenceUpdateRequest(mode='manual'),'test-'+uuid4().hex,'test')
    assert exc.value.code=='cost_center_managed_code_required'
    before=conn.execute(select(centers.c.id).where(centers.c.tenant_id==TENANT)).all()
    class Broken:
        def code(self,*args):raise ErclaveError('cost_center_authority_unavailable','unavailable',503)
    with pytest.raises(ErclaveError):repo.command(access,'create',payload,'test-'+uuid4().hex,'test',Broken())
    assert conn.execute(select(centers.c.id).where(centers.c.tenant_id==TENANT)).all()==before


def test_dedicated_numbering_permission_identity_and_flag():
    class Fake(FakeAdminRepository):
        session_permissions=['costing.cost_center.create']
        inactive=False
        def get_session_context(self,*args):
            context=super().get_session_context(*args)
            if self.inactive:context.user.status='inactive'
            return context
        def allocate_business_code(self,tenant,document_type,*args):
            assert document_type=='costing.cost_center'
            return CodeSequenceAllocationRead(document_type=document_type,mode='managed',code='CC-000001',sequence_number=1)
    repo=Fake()
    app.dependency_overrides[get_admin_repository]=lambda:repo
    app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase',cost_center_catalog_enabled=True)
    app.dependency_overrides[get_authenticated_actor]=lambda:AuthenticatedActor(uid='local-test',email='admin.qa@erclave.local')
    try:
        http=TestClient(app);headers={'X-Tenant-Id':TENANT_ID,'Idempotency-Key':'test-cost-center'}
        path='/v1/cost-center-codes/next'
        response=http.post(path,headers=headers,json={})
        assert response.status_code==200,response.text
        repo.inactive=True
        assert http.post(path,headers=headers,json={}).status_code==403
        repo.inactive=False;repo.session_permissions=['admin.setting.update']
        assert http.post(path,headers=headers,json={}).status_code==403
        repo.session_permissions=['production.order.release']
        assert http.post('/v1/catalogs/code-sequences/costing.cost_center/next',headers=headers,json={}).status_code==422
        repo.session_permissions=['costing.cost_center.create']
        app.dependency_overrides[get_settings]=lambda:Settings(auth_mode='firebase',cost_center_catalog_enabled=False)
        assert http.post(path,headers=headers,json={}).status_code==403
    finally:app.dependency_overrides.clear()


def test_postgres_downgrade_preserves_center_history(store):
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    conn=store.test_connection
    conn.execute(audit.insert().values(tenant_id=TENANT,id='test-'+uuid4().hex[:26],actor_id='actor',action='test',entity_id='test',after_state={},correlation_id='test',idempotency_key='test'))
    path=Path(__file__).resolve().parents[3]/'alembic/versions/20260927_0040_cost_centers.py'
    spec=importlib.util.spec_from_file_location('costing_migration_guard',path)
    migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    with pytest.raises(DBAPIError,match='Cost center history exists'):
        with conn.begin_nested():
            with Operations.context(MigrationContext.configure(conn)):migration.downgrade()
    assert conn.execute(text("select to_regclass('costing.audit_events')")).scalar()
