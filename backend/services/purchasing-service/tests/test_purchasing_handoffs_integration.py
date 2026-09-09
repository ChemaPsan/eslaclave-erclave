"""Local demo tenant only; remove exclusively this test's owned documents."""
import importlib,os,sys
from pathlib import Path
from datetime import date,datetime,timezone
from uuid import uuid4
from decimal import Decimal
import pytest
from sqlalchemy import text
from erclave_common.errors import ErclaveError

DATABASE_URL=os.getenv('ERCLAVE_TEST_DATABASE_URL','')
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason='Local PostgreSQL is required')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repos=importlib.import_module('app.repositories');schemas=importlib.import_module('app.schemas');api=importlib.import_module('app.api')


@pytest.fixture
def purchasing_handoff():
    tenant=os.getenv('ERCLAVE_TEST_TENANT_ID','ten_739ee59d765d5e14818674800d')
    assert tenant=='ten_739ee59d765d5e14818674800d'
    repo=repos.PurchasingRepository(DATABASE_URL);suffix=uuid4().hex[:14];prefix='handoff-'+suffix
    requester='usr_req_'+suffix;buyer='usr_buy_'+suffix;warehouse='usr_wh_'+suffix
    supplier=req=order=None
    try:
        supplier=repo.create_supplier(tenant,schemas.SupplierWrite(code='SUP-'+suffix,commercial_name='Proveedor sintético',legal_name='Proveedor sintético SA',tax_id='XQZ010101'+suffix[:3].upper(),tax_regime='601',billing_email='test@example.com',fiscal_postal_code='01234',currency='MXN',payment_terms='cash'),prefix+'-supplier','supplier',buyer)
        lines=[schemas.PurchaseLineInput(line_type='inventory_item',inventory_item_id='itm_'+suffix,description='Material sintético',quantity=2,unit_code='H87'),schemas.PurchaseLineInput(line_type='service',description='Servicio sintético',quantity=1,unit_code='E48')]
        req=repo.create_requisition(tenant,schemas.RequisitionWrite(code='REQ-'+suffix,required_date=date.today(),lines=lines),prefix+'-req','req',requester)
        repo.transition_requisition(tenant,req['id'],'submitted',None,prefix+'-submit','submit',requester)
        repo.transition_requisition(tenant,req['id'],'approved',None,prefix+'-approve','approve',buyer)
        order=repo.create_order(tenant,schemas.PurchaseOrderWrite(code='PO-'+suffix,requisition_id=req['id'],supplier_id=supplier['id'],currency='MXN',payment_terms='cash',lines=[l.model_copy(update={'unit_price':Decimal('10')}) for l in lines]),prefix+'-order','order',buyer)
        order=repo.issue_order(tenant,order['id'],prefix+'-issue','issue',buyer)
        yield repo,tenant,order,requester,buyer,warehouse,prefix
    finally:
        with repo.engine.begin() as c:
            if order:
                c.execute(text('delete from purchasing.purchase_receipts where tenant_id=:t and purchase_order_id=:id'),{'t':tenant,'id':order['id']})
                c.execute(text('delete from purchasing.purchase_orders where tenant_id=:t and id=:id'),{'t':tenant,'id':order['id']})
            if req:c.execute(text('delete from purchasing.requisitions where tenant_id=:t and id=:id'),{'t':tenant,'id':req['id']})
            if supplier:c.execute(text('delete from purchasing.suppliers where tenant_id=:t and id=:id'),{'t':tenant,'id':supplier['id']})
            c.execute(text('delete from purchasing.audit_events where tenant_id=:t and actor_id=any(:actors)'),{'t':tenant,'actors':[requester,buyer,warehouse]})
            c.execute(text('delete from purchasing.idempotency_records where tenant_id=:t and idempotency_key like :prefix'),{'t':tenant,'prefix':prefix+'%'})
        repo.engine.dispose()


def test_mixed_receipt_requires_warehouse_and_original_requester(purchasing_handoff):
    repo,t,order,requester,buyer,warehouse,key=purchasing_handoff
    payload=schemas.ReceiptWrite(code=key,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=l['id'],quantity=l['quantity'],warehouse_id='wh_test' if l['line_type']=='inventory_item' else None) for l in order['lines']])
    receipt,_=repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer)
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
    receipt,_=repo.prepare_receipt(t,payload,key+'-receipt','receipt',buyer)
    class FailingWarehouse:
        fail=True
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
