"""Local demo tenant only; remove exclusively this test's owned documents."""
import importlib,os,sys
from pathlib import Path
from datetime import date,datetime,timezone
from uuid import uuid4
from decimal import Decimal
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from dataclasses import replace
import pytest
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from erclave_common.operational_context import OperationalContext
from erclave_common.organization_client import OrganizationAccess
from sqlalchemy.engine import make_url

DATABASE_URL=os.getenv('ERCLAVE_TEST_DATABASE_URL','')
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason='Local PostgreSQL is required')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repos=importlib.import_module('app.repositories');schemas=importlib.import_module('app.schemas');api=importlib.import_module('app.api')
receipt_context=importlib.import_module('app.receipt_context')
reports=importlib.import_module('app.reports')
CONTEXT=OperationalContext(division_ref_id='division-cc14-test',society_ref_id='society-cc14-test',division_code='TEST',division_name='Synthetic Division',cost_currency='MXN')

def snapshots(order,rate=None):
    return {line['id']:receipt_context.cost_snapshot(CONTEXT,order['currency'],line['unit_price'],rate) for line in order['lines'] if line['line_type']=='inventory_item'}

def organization_access(tenant,actor):
    return OrganizationAccess(tenant,actor,('inventory.movement.create',),({'id':CONTEXT.division_ref_id,'society_id':CONTEXT.society_ref_id,'code':'TEST','name':'Synthetic Division'},),False,False)


@pytest.fixture
def purchasing_handoff(request):
    tenant=os.getenv('ERCLAVE_TEST_TENANT_ID','ten_739ee59d765d5e14818674800d')
    assert tenant=='ten_739ee59d765d5e14818674800d'
    url=make_url(DATABASE_URL)
    assert url.host in {'127.0.0.1','localhost','::1'} and url.port==5434 and url.database=='erclave_local' and not url.query
    config=getattr(request,'param',{})
    repo=repos.PurchasingRepository(DATABASE_URL);suffix=uuid4().hex[:14];prefix='handoff-'+suffix
    requester='usr_req_'+suffix;buyer='usr_buy_'+suffix;warehouse='usr_wh_'+suffix
    supplier=req=order=None
    try:
        supplier=repo.create_supplier(tenant,schemas.SupplierWrite(code='SUP-'+suffix,commercial_name='Proveedor sintético',legal_name='Proveedor sintético SA',tax_id='XQZ010101'+suffix[:3].upper(),tax_regime='601',billing_email='test@example.com',fiscal_postal_code='01234',currency='MXN',payment_terms='cash'),prefix+'-supplier','supplier',buyer)
        with repo.engine.begin() as c:
            assert c.execute(text('select id from admin.tenants')).scalars().all()==[tenant]
            c.execute(text("insert into purchasing.supplier_division_assignments(tenant_id,supplier_id,division_ref_id,society_ref_id,status,revision) values(:t,:id,:d,:s,'active',1)"),{'t':tenant,'id':supplier['id'],'d':CONTEXT.division_ref_id,'s':CONTEXT.society_ref_id})
        lines=[schemas.PurchaseLineInput(line_type='inventory_item',inventory_item_id='itm_'+suffix,description='Material sintético',quantity=2,unit_code='H87'),schemas.PurchaseLineInput(line_type='service',description='Servicio sintético',quantity=1,unit_code='E48')]
        req=repo.create_requisition(tenant,schemas.RequisitionWrite(code='REQ-'+suffix,required_date=date.today(),lines=lines),prefix+'-req','req',requester)
        repo.transition_requisition(tenant,req['id'],'submitted',None,prefix+'-submit','submit',requester)
        repo.transition_requisition(tenant,req['id'],'approved',None,prefix+'-approve','approve',buyer)
        order=repo.create_order(tenant,schemas.PurchaseOrderWrite(code='PO-'+suffix,requisition_id=req['id'],supplier_id=supplier['id'],currency=config.get('currency','MXN'),payment_terms='cash',lines=[l.model_copy(update={'unit_price':Decimal(config.get('price','10'))}) for l in lines]),prefix+'-order','order',buyer)
        order=repo.issue_order(tenant,order['id'],prefix+'-issue','issue',buyer)
        yield repo,tenant,order,requester,buyer,warehouse,prefix
    finally:
        with repo.engine.begin() as c:
            if order:
                c.execute(text('delete from purchasing.purchase_receipts where tenant_id=:t and purchase_order_id=:id'),{'t':tenant,'id':order['id']})
                c.execute(text('delete from purchasing.purchase_orders where tenant_id=:t and id=:id'),{'t':tenant,'id':order['id']})
            if req:c.execute(text('delete from purchasing.requisitions where tenant_id=:t and id=:id'),{'t':tenant,'id':req['id']})
            if supplier:
                c.execute(text('delete from purchasing.supplier_division_assignments where tenant_id=:t and supplier_id=:id'),{'t':tenant,'id':supplier['id']})
                c.execute(text('delete from purchasing.suppliers where tenant_id=:t and id=:id'),{'t':tenant,'id':supplier['id']})
            c.execute(text('delete from purchasing.audit_events where tenant_id=:t and actor_id=any(:actors)'),{'t':tenant,'actors':[requester,buyer,warehouse]})
            c.execute(text('delete from purchasing.idempotency_records where tenant_id=:t and idempotency_key like :prefix'),{'t':tenant,'prefix':prefix+'%'})
        repo.engine.dispose()


def test_mixed_receipt_requires_warehouse_and_original_requester(purchasing_handoff):
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    payload=schemas.ReceiptWrite(code=key,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=l['id'],quantity=l['quantity'],warehouse_id='wh_test' if l['line_type']=='inventory_item' else None) for l in order['lines']])
    receipt,_=repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer,snapshots(order))
    assert receipt['status']=='pending_confirmation'
    assert repo.get_order(t,order['id'])['status']=='issued'
    assert repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer)[1] is None
    assert any(r['id']==receipt['id'] for r in repo.list_pending_receipts(t,'inventory_item',limit=100))
    assert any(r['id']==receipt['id'] for r in repo.list_pending_receipts(t,'service',requester,100))
    assert not repo.list_pending_receipts(t,'service',buyer,100)
    assert not repo.list_pending_receipts('other-tenant','inventory_item')
    with pytest.raises(ValueError,match='over_receipt'):repo.prepare_receipt(t,payload.model_copy(update={'code':key+'-duplicate'}),key+'-over','over',buyer)
    with pytest.raises(ErclaveError,match='original requester'):repo.require_service_requester(t,receipt['id'],buyer)
    class Warehouse:
        calls=0
        def organization_access(self,*args):return organization_access(t,warehouse)
        def receive(self,*args):
            self.calls+=1
            return {'id':'mov_'+key[-14:]}
    authority=Warehouse()
    commercial_access=api.AuthorizedContext(t,buyer,'purchasing.receipt.reconcile',frozenset({'purchasing.receipt.reconcile'}))
    with pytest.raises(ErclaveError) as denied:api.reconcile_receipt(receipt['id'],t,None,key+'-commercial',repo,authority,commercial_access)
    assert denied.value.code=='purchase_warehouse_receipt_required' and authority.calls==0
    warehouse_access=api.AuthorizedContext(t,warehouse,'inventory.movement.create',frozenset({'inventory.movement.create'}))
    value=api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-receive',repo,authority,warehouse_access).data
    assert value['status']=='pending_confirmation' and authority.calls==1
    assert repo.get_order(t,order['id'])['status']=='partially_received'
    api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-receive',repo,authority,warehouse_access)
    assert authority.calls==1
    requester_access=api.AuthorizedContext(t,requester,'purchasing.requisition.create',frozenset({'purchasing.requisition.create'}))
    value=api.confirm_receipt_lines(receipt['id'],'service',t,None,key+'-accept',repo,authority,requester_access).data
    assert value['status']=='completed' and repo.get_order(t,order['id'])['status']=='received'
    assert authority.calls==1
    with repo.engine.connect() as c:
        actors=c.execute(text('select confirmed_by_actor_id from purchasing.purchase_receipt_lines where tenant_id=:t and receipt_id=:id'),{'t':t,'id':receipt['id']}).scalars().all()
        assert set(actors)=={warehouse,requester}


def test_failed_physical_receipt_can_retry_without_accepting_services(purchasing_handoff):
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    payload=schemas.ReceiptWrite(code=key,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=l['id'],quantity=l['quantity'],warehouse_id='wh_test' if l['line_type']=='inventory_item' else None) for l in order['lines']])
    receipt,_=repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer,snapshots(order))
    class FailingWarehouse:
        fail=True
        def organization_access(self,*args):return organization_access(t,warehouse)
        def receive(self,*args):
            if self.fail:raise ErclaveError('inventory_unavailable','Retry',503)
            return {'id':'mov_'+key[-14:]}
    authority=FailingWarehouse();access=api.AuthorizedContext(t,warehouse,'inventory.movement.create')
    value=api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-receive',repo,authority,access).data
    assert value['status']=='needs_reconciliation'
    assert repo.get_order(t,order['id'])['status']=='issued'
    authority.fail=False
    value=api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-retry',repo,authority,access).data
    assert value['status']=='pending_confirmation'
    assert repo.get_order(t,order['id'])['status']=='partially_received'


@pytest.mark.parametrize('purchasing_handoff',[{'currency':'USD','price':'4.12'}],indirect=True)
def test_cc14_durable_proof_precision_replay_recovery_and_callback_lock(purchasing_handoff):
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    physical=next(line for line in order['lines'] if line['line_type']=='inventory_item')
    payload=schemas.ReceiptWrite(code=key,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),cost_exchange_rate='20',lines=[schemas.ReceiptLineInput(order_line_id=physical['id'],quantity=physical['quantity'],warehouse_id='wh_test')])
    frozen=snapshots(order,Decimal('20'))
    receipt,plan=repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer,frozen)
    assert receipt['lines'][0]['inventory_context_snapshot']['unit_cost']=='82.400000'
    replay,replay_plan=repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer,{})
    assert replay_plan is None and replay['lines'][0]['inventory_context_snapshot']==frozen[physical['id']]
    assert repo.receipt_replay(t,key+'-receipt','receipt')['id']==receipt['id']
    with pytest.raises(ValueError,match='idempotency_key_reused'):repo.receipt_replay(t,key+'-receipt','different')

    class CallbackWarehouse:
        calls=0
        def organization_access(self,*args):return organization_access(t,warehouse)
        def receive(self,tenant,line,receipt_id,order_id,authorization,idempotency_key):
            self.calls+=1
            # Different connection while Purchasing holds the session advisory lock.
            # A row/advisory lock in proof would deadlock this callback.
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(receipt_context.receipt_proof,repo,self,t,receipt_id,line['receipt_line_id'],authorization,warehouse)
                proof=future.result(timeout=5)
            assert proof['receipt_line_id']==line['receipt_line_id']
            assert proof['original_currency']=='USD' and proof['original_unit_cost']=='4.12'
            assert proof['unit_cost']=='82.400000' and proof['cost_exchange_rate']=='20'
            assert proof['inventory_idempotency_key']==idempotency_key
            if self.calls==1:raise ErclaveError('inventory_unavailable','Simulated response loss',503)
            return {'id':'mov_'+key[-14:]}
    authority=CallbackWarehouse();access=api.AuthorizedContext(t,warehouse,'inventory.movement.create')
    failed=api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-receive',repo,authority,access).data
    assert failed['status']=='needs_reconciliation'
    assert repo.get_order(t,order['id'])['lines'][0]['received_quantity']==0
    completed=api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-retry',repo,authority,access).data
    assert completed['status']=='completed'
    assert repo.get_order(t,order['id'])['lines'][0]['received_quantity']==physical['quantity']
    api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-retry',repo,authority,access)
    assert authority.calls==2
    # Missing/foreign receipt lines cannot obtain evidence in the authorized tenant.
    with pytest.raises(ErclaveError) as exc:receipt_context.receipt_proof(repo,authority,t,receipt['id'],'other-line',None,warehouse)
    assert exc.value.code=='receipt_not_found'


def test_cc14_concurrent_receipts_cannot_overallocate_demo_order(purchasing_handoff):
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    physical=next(line for line in order['lines'] if line['line_type']=='inventory_item')
    barrier=Barrier(2)
    frozen=snapshots(order)
    def claim(index):
        competitor=repos.PurchasingRepository(DATABASE_URL)
        payload=schemas.ReceiptWrite(code=key+str(index),purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=physical['id'],quantity=physical['quantity'],warehouse_id='wh_test')])
        barrier.wait(timeout=5)
        try:return competitor.prepare_receipt(t,payload,key+'-race-'+str(index),'race'+str(index),buyer,frozen)[0]['id']
        except ValueError as exc:return str(exc)
        finally:competitor.engine.dispose()
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(claim,[1,2]))
    assert sum(value.startswith('rcp_') for value in results)==1
    assert results.count('over_receipt')==1


def test_cc14_revoked_scope_blocks_lists_confirm_and_replays_before_writes(purchasing_handoff):
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    physical=next(line for line in order['lines'] if line['line_type']=='inventory_item')
    payload=schemas.ReceiptWrite(code=key,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=physical['id'],quantity='1',warehouse_id='wh_test')])
    receipt,_=repo.prepare_receipt(t,payload,key+'-receipt',api.digest(payload),buyer,snapshots(order))
    class ScopedAuthority:
        granted=False
        calls=0
        def organization_access(self,*args):
            granted=organization_access(t,warehouse)
            return granted if self.granted else replace(granted,divisions=())
        def receive(self,*args):
            self.calls+=1
            return {'id':'mov_'+key[-14:]}
    authority=ScopedAuthority()
    warehouse_access=api.AuthorizedContext(t,warehouse,'inventory.movement.create')
    reader=api.AuthorizedContext(t,warehouse,'inventory.movement.read')
    creator=api.AuthorizedContext(t,buyer,'purchasing.receipt.create')
    assert receipt['id'] not in {row['id'] for row in api.receipts(t,repo,reader,None,authority).data}
    assert receipt['id'] not in {row['id'] for row in api.warehouse_receipts(100,0,t,repo,reader,None,authority).data}
    with pytest.raises(ErclaveError) as exc:api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-confirm',repo,authority,warehouse_access)
    assert exc.value.code=='assignment_division_denied'
    with pytest.raises(ErclaveError) as exc:api.create_receipt(payload,t,None,key+'-receipt',repo,authority,creator)
    assert exc.value.code=='assignment_division_denied'
    assert authority.calls==0
    with repo.engine.connect() as c:
        assert c.execute(text("select count(*) from purchasing.idempotency_records where tenant_id=:t and idempotency_key=:k"),{'t':t,'k':key+'-confirm'}).scalar_one()==0
        assert c.execute(text('select reconciliation_attempts from purchasing.purchase_receipts where tenant_id=:t and id=:id'),{'t':t,'id':receipt['id']}).scalar_one()==0
    authority.granted=True
    assert receipt['id'] in {row['id'] for row in api.warehouse_receipts(100,0,t,repo,reader,None,authority).data}
    api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-confirm',repo,authority,warehouse_access)
    assert authority.calls==1
    authority.granted=False
    with pytest.raises(ErclaveError) as exc:api.confirm_receipt_lines(receipt['id'],'inventory_item',t,None,key+'-confirm',repo,authority,warehouse_access)
    assert exc.value.code=='assignment_division_denied'
    assert authority.calls==1
    assert receipt['id'] not in {row['id'] for row in repo.list_receipts(t,allowed_divisions=[])}


def test_cc14_scope_filter_precedes_pagination_and_hides_legacy_physical_receipts(purchasing_handoff):
    import json
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    physical=next(line for line in order['lines'] if line['line_type']=='inventory_item')
    receipts=[]
    for index in range(2):
        payload=schemas.ReceiptWrite(code=key+str(index),purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=physical['id'],quantity='1',warehouse_id='wh_test')])
        receipt,_=repo.prepare_receipt(t,payload,key+'-receipt-'+str(index),'receipt'+str(index),buyer,snapshots(order))
        receipts.append(receipt)
    foreign=receipts[0]['lines'][0]['inventory_context_snapshot']
    foreign['organization_context']['division_ref_id']='division-foreign'
    with repo.engine.begin() as c:c.execute(text('update purchasing.purchase_receipt_lines set inventory_context_snapshot=cast(:s as jsonb) where tenant_id=:t and receipt_id=:id'),{'s':json.dumps(foreign),'t':t,'id':receipts[0]['id']})
    filtered=repo.list_pending_receipts(t,'inventory_item',limit=1,offset=0,allowed_divisions=[CONTEXT.division_ref_id])
    assert len(filtered)==1 and filtered[0]['id']==receipts[1]['id']
    with repo.engine.begin() as c:c.execute(text('update purchasing.purchase_receipt_lines set inventory_context_snapshot=null where tenant_id=:t and receipt_id=:id'),{'t':t,'id':receipts[1]['id']})
    assert not repo.list_pending_receipts(t,'inventory_item',allowed_divisions=[CONTEXT.division_ref_id])
    assert receipts[1]['id'] in {row['id'] for row in repo.list_pending_receipts(t,'inventory_item',allowed_divisions=None,limit=100)}
    report=reports.build_report(repo,t,'receipts',{'allowed_divisions':[CONTEXT.division_ref_id]})
    assert not report.rows
