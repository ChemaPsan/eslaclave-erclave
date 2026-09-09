"""Guarded Local tests: only task-owned synthetic records in the allowed tenant."""
import importlib
import json
import os
import sys
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.pool import NullPool
from erclave_common.errors import ErclaveError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repositories=importlib.import_module('app.repositories')
schemas=importlib.import_module('app.schemas')
api=importlib.import_module('app.api')
authorities=importlib.import_module('app.authorities')
TENANT='ten_739ee59d765d5e14818674800d'

@pytest.fixture
def material():
    url=os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not url:pytest.skip('ERCLAVE_TEST_DATABASE_URL required')
    parsed=urlparse(url.replace('postgresql+psycopg','postgresql',1))
    assert parsed.hostname=='127.0.0.1' and parsed.port==5434 and parsed.path=='/erclave_local'
    repo=repositories.MaintenanceRepository(url);repo.engine.dispose();repo.engine=create_engine(url,poolclass=NullPool)
    prefix='recovery-'+uuid4().hex[:16];actor=prefix;oid=None;rid=None
    try:
        order=repo.create_order(TENANT,schemas.OrderCreate(code=prefix,target_type='facility',priority='medium',title='Recovery test',description='Synthetic',location='Local'),{'machine_code_snapshot':None,'machine_name_snapshot':None,'source_production_order_code_snapshot':None},prefix+'-order','order',actor);oid=order['id']
        repo.transition(TENANT,oid,schemas.TransitionRequest(transition='request'),None,prefix+'-request','request',actor)
        worker={'id':'hrw_recovery_test','full_name':'Recovery test'}
        repo.transition(TENANT,oid,schemas.TransitionRequest(transition='assign',assigned_worker_id=worker['id']),worker,prefix+'-assign','assign',actor)
        payload=schemas.MaterialRequestCreate(warehouse_id='wh_recovery_test',lines=[schemas.MaterialLine(item_id='item_a',quantity=1.125,unit_code='H87'),schemas.MaterialLine(item_id='item_b',quantity=2,unit_code='H87')])
        row,_=repo.prepare_material_request(TENANT,oid,payload,{'warehouse_name':'Test','items':[{'code':'A','name':'A'},{'code':'B','name':'B'}]},prefix+'-parts','parts',actor);rid=row['id']
        repo.complete_material_request(TENANT,rid,prefix+'-parts',[],'insufficient_available_stock',actor)
        yield repo,oid,rid,prefix,SimpleNamespace(actor_id=actor)
    finally:
        with repo.engine.begin() as c:
            if rid:
                c.execute(text('delete from maintenance.material_request_lines where tenant_id=:t and material_request_id=:r'),{'t':TENANT,'r':rid})
                c.execute(text('delete from maintenance.material_requests where tenant_id=:t and id=:r'),{'t':TENANT,'r':rid})
            if oid:c.execute(text('delete from maintenance.orders where tenant_id=:t and id=:o'),{'t':TENANT,'o':oid})
            c.execute(text('delete from maintenance.audit_events where tenant_id=:t and actor_id=:a'),{'t':TENANT,'a':actor})
            c.execute(text('delete from maintenance.idempotency_records where tenant_id=:t and idempotency_key like :k'),{'t':TENANT,'k':prefix+'%'})
        repo.engine.dispose()

def test_interrupted_reconciliation_resumes_same_key_with_real_decimal_client(material,monkeypatch):
    repo,oid,rid,prefix,access=material
    client=authorities.MaintenanceAuthorityClient(SimpleNamespace(hr_service_url='http://127.0.0.1:8006',inventory_service_url='http://127.0.0.1:8004',production_service_url='http://127.0.0.1:8002',authorization_timeout_seconds=5))
    reservations={};calls=[]
    def inventory(request,timeout):
        assert request.full_url=='http://127.0.0.1:8004/v1/inventory/reservation-requests'
        assert request.get_header('X-tenant-id')==TENANT
        body=json.loads(request.data);assert isinstance(body['quantity'],(int,float))
        key=request.get_header('Idempotency-key');calls.append(key)
        reservations.setdefault(key,{'id':'rsv_'+str(len(reservations)),'unit_cost_snapshot':3})
        return BytesIO(json.dumps({'data':reservations[key]}).encode())
    monkeypatch.setattr(authorities.request,'urlopen',inventory)
    original=repo.complete_material_reconciliation
    def crash(*args,**kwargs):raise RuntimeError('process interrupted after Inventory confirmed')
    monkeypatch.setattr(repo,'complete_material_reconciliation',crash)
    with pytest.raises(RuntimeError,match='interrupted'):
        api.reconcile_material_request(rid,TENANT,None,prefix+'-retry',repo,client,access)
    assert repo.get_material_request(TENANT,rid)['status']=='processing'
    assert len(reservations)==2
    monkeypatch.setattr(repo,'complete_material_reconciliation',original)
    result=api.reconcile_material_request(rid,TENANT,None,prefix+'-retry',repo,client,access).data
    assert result['status']=='reserved' and result['pending_operation'] is None
    assert len(reservations)==2 and len(calls)==4 and calls[:2]==calls[2:]
    assert result['lines'][0]['quantity']==Decimal('1.125')
    assert all(not l['inventory_movement_id'] for l in result['lines'])
    api.reconcile_material_request(rid,TENANT,None,prefix+'-retry',repo,client,access)
    api.reconcile_material_request(rid,TENANT,None,prefix+'-new-key',repo,client,access)
    assert len(calls)==4
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        with repo.material_command_lock(TENANT,rid):repo.prepare_material_reconciliation(TENANT,rid,prefix+'-retry','different-hash',access.actor_id)
    with repo.material_command_lock('other-tenant',rid):assert repo.prepare_material_reconciliation('other-tenant',rid,prefix+'-foreign','hash',access.actor_id)==(None,None)

def test_creation_and_request_locks_block_competing_recovery_and_issue(material):
    repo,oid,rid,prefix,access=material
    with repo.material_creation_lock(TENANT,oid):
        with pytest.raises(ValueError,match='command_in_progress'):
            with repo.material_command_lock(TENANT,rid):pytest.fail('must not enter')
    with repo.material_command_lock(TENANT,rid):
        with pytest.raises(ValueError,match='command_in_progress'):
            with repo.material_creation_lock(TENANT,oid):pytest.fail('must not enter')
        with pytest.raises(ValueError,match='command_in_progress'):
            with repo.material_command_lock(TENANT,rid):pytest.fail('must not enter')
    with repo.material_command_lock(TENANT,rid):pass

def test_partial_recovery_only_retries_missing_lines_and_keeps_failures_recoverable(material):
    repo,oid,rid,prefix,access=material
    class Inventory:
        fail=True
        calls=[]
        def reserve(self,t,o,r,line,w,auth,key):
            self.calls.append(line['item_id'])
            if line['item_id']=='item_b' and self.fail:raise ErclaveError('insufficient_available_stock','Unavailable',status_code=409)
            return {'id':'res_'+line['item_id'],'unit_cost_snapshot':1}
    client=Inventory()
    result=api.reconcile_material_request(rid,TENANT,None,prefix+'-first',repo,client,access).data
    assert result['status']=='needs_reconciliation' and result['integration_error']=='insufficient_available_stock'
    client.fail=False
    result=api.reconcile_material_request(rid,TENANT,None,prefix+'-second',repo,client,access).data
    assert result['status']=='reserved' and client.calls==['item_a','item_b','item_b']
    with repo.material_command_lock(TENANT,rid):repo.prepare_warehouse_issue(TENANT,rid,access.actor_id)
    with pytest.raises(ErclaveError) as rejected:api.reconcile_material_request(rid,TENANT,None,prefix+'-issue-block',repo,client,access)
    assert rejected.value.code=='material_request_not_reconcilable'

def test_interrupted_cancellation_resumes_without_issuing(material):
    repo,oid,rid,prefix,access=material
    repo.complete_material_request(TENANT,rid,prefix+'-parts',[{'id':'res_a'},{'id':'res_b'}],actor=access.actor_id)
    with repo.material_command_lock(TENANT,rid):repo.prepare_material_cancellation(TENANT,rid,prefix+'-cancel','cancel',access.actor_id)
    class Inventory:
        released=[]
        def release_reservation(self,t,reservation,auth,key):self.released.append(reservation)
    client=Inventory()
    result=api.reconcile_material_request(rid,TENANT,None,prefix+'-recover-cancel',repo,client,access).data
    assert result['status']=='cancelled' and client.released==['res_a','res_b']
    api.reconcile_material_request(rid,TENANT,None,prefix+'-again',repo,client,access)
    assert client.released==['res_a','res_b']
