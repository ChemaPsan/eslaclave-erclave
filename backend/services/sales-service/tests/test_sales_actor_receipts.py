"""Actor-bound receipts and interrupted intents; all DB fixtures roll back."""
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from test_sales_organization import local_store, scoped_quote, scoped_order, repos, quote_schemas, TENANT


@pytest.mark.parametrize('operation', ['customer.create','customer.update','quote.create','quote.update','quote.quoted','quote.approved','quote.cancelled','order.create','order.cancel','delivery.create','delivery.confirm','delivery.cancel','order.fulfillment:own','service_order.plan:own','service_order.assign:own','service_order.time.create:own','service_order.cost.create:own','service_order.evidence.create:own','service_order.start:own'])
def test_postgres_receipt_does_not_cross_actors(local_store, operation):
    store, conn, _ = local_store
    repo=store.repository;key='actor-'+uuid4().hex
    assert repo._claim(conn,TENANT,operation,key,'hash','original') is None
    repo._finish(conn,TENANT,operation,key,SimpleNamespace(model_dump=lambda **kw: {'id':'own-receipt'}))
    assert repo._claim(conn,TENANT,operation,key,'hash','original')=={'id':'own-receipt'}
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(conn,TENANT,operation,key,'hash','different')
    assert repo._claim(conn,TENANT,operation,key,'hash','original')=={'id':'own-receipt'}


def test_postgres_legacy_receipt_uses_real_sales_audit_timestamp(local_store):
    store,conn,id_=local_store;repo=store.repository;key='legacy-'+uuid4().hex;operation='quote.approved'
    assert repo._claim(conn,TENANT,operation,key,'legacy-hash') is None
    repo._audit(conn,TENANT,'original',operation,'quote',id_,{})
    repo._finish(conn,TENANT,operation,key,SimpleNamespace(model_dump=lambda **kw:{'id':id_}))
    assert repo._claim(conn,TENANT,operation,key,'legacy-hash','original')=={'id':id_}
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(conn,TENANT,operation,key,'legacy-hash','different')


def test_postgres_fulfillment_pending_recovery_same_actor_and_unknown_legacy_closed(scoped_order):
    store,conn,_,_,_,_,order=scoped_order;repo=store.repository;line=order.lines[0]
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='pending',fulfillment_status='pending' where tenant_id=:t and id=:i"),{'t':TENANT,'i':line.id})
    payload=quote_schemas.SalesOrderFulfillmentRequest(lines=[{'order_line_id':line.id,'mode':'production'}])
    first=repo.prepare_order_fulfillment(TENANT,order.id,payload,'own-key','hash','MXN',1,actor_id='original')
    repo.mark_fulfillment_reconciliation(TENANT,order.id)
    same=repo.prepare_order_fulfillment(TENANT,order.id,payload,'own-key','hash','MXN',1,actor_id='original')
    assert same[0].id==first[0].id and same[1]=='own-key'
    with pytest.raises(ValueError,match='sales_order_fulfillment_in_progress'):
        repo.prepare_order_fulfillment(TENANT,order.id,payload,'own-key','hash','MXN',1,actor_id='different')
    stored=conn.execute(text('select fulfillment_hash from sales.orders where tenant_id=:t and id=:i'),{'t':TENANT,'i':order.id}).scalar_one()
    assert stored==repo._actor_hash('hash','original')
    conn.execute(text('update sales.orders set fulfillment_hash=:h where tenant_id=:t and id=:i'),{'h':'hash','t':TENANT,'i':order.id})
    with pytest.raises(ValueError,match='sales_order_fulfillment_in_progress'):
        repo.prepare_order_fulfillment(TENANT,order.id,payload,'own-key','hash','MXN',1,actor_id='original')
    assert conn.execute(text('select fulfillment_hash from sales.orders where tenant_id=:t and id=:i'),{'t':TENANT,'i':order.id}).scalar_one()=='hash'


def test_postgres_cancel_pending_recovery_same_actor_only(scoped_order):
    store,conn,_,_,_,_,order=scoped_order;repo=store.repository
    repo.prepare_cancel_order(TENANT,order.id,'cancel-key','hash',actor_id='original')
    repo.mark_cancellation_reconciliation(TENANT,order.id)
    assert repo.prepare_cancel_order(TENANT,order.id,'cancel-key','hash',actor_id='original')[0].id==order.id
    with pytest.raises(ValueError,match='sales_order_cancellation_in_progress'):
        repo.prepare_cancel_order(TENANT,order.id,'cancel-key','hash',actor_id='different')


def test_postgres_delivery_intent_recovery_does_not_cross_actors(scoped_order):
    store,conn,_,_,_,_,order=scoped_order;repo=store.repository;line=order.lines[0]
    conn.execute(text("update sales.orders set cost_currency='MXN',cost_exchange_rate=1 where tenant_id=:t and id=:i"),{'t':TENANT,'i':order.id})
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='pending',fulfillment_status='pending' where tenant_id=:t and id=:i"),{'t':TENANT,'i':line.id})
    repo.configure_order_fulfillment(TENANT,order.id,[{'order_line_id':line.id,'mode':'stock','inventory_item_id':'own-item','inventory_item_code':'OWN','inventory_item_name':'Synthetic','reservations':[{'id':'own-res-'+uuid4().hex[:20],'warehouse_id':'own-warehouse','quantity':str(line.ordered_quantity),'unit_cost_snapshot':'4'}]}],'stock-key','stock-hash','original')
    payload=quote_schemas.DeliveryCreateRequest(code='OWN-'+uuid4().hex[:20],order_id=order.id,scheduled_date='2026-10-18',lines=[{'order_line_id':line.id,'quantity':str(line.ordered_quantity)}])
    delivery=repo.create_delivery(TENANT,payload,'delivery-key','delivery-hash','original')
    first=repo.prepare_delivery_confirmation(TENANT,delivery.id,'confirm-key','confirm-hash',actor_id='original')
    same=repo.prepare_delivery_confirmation(TENANT,delivery.id,'confirm-key','confirm-hash',actor_id='original')
    assert same[0].id==first[0].id and same[1]==first[1]
    with pytest.raises(ValueError,match='delivery_confirmation_in_progress'):
        repo.prepare_delivery_confirmation(TENANT,delivery.id,'confirm-key','confirm-hash',actor_id='different')
    assert conn.execute(text('select confirmation_hash from sales.deliveries where tenant_id=:t and id=:i'),{'t':TENANT,'i':delivery.id}).scalar_one()==repo._actor_hash('confirm-hash','original')


def test_postgres_manufacturing_intent_recovery_binds_actor_and_keeps_legacy_pending(scoped_order):
    store,conn,_,_,_,_,order=scoped_order;repo=store.repository;line=order.lines[0]
    conn.execute(text("update sales.order_lines set product_service_type='product',fulfillment_mode='production',fulfillment_status='production_requested',production_request_ref_id=:r where tenant_id=:t and id=:i"),{'t':TENANT,'i':line.id,'r':'own-request-'+uuid4().hex[:20]})
    args=(TENANT,order.id,line.id,'own-warehouse',{'id':'own-item'},{'production_order_id':'own-production'},'own-key','hash')
    record=repo.prepare_production_reconciliation(*args,actor_id='original')
    assert record['request_hash']==repo._actor_hash('hash','original')
    assert repo.prepare_production_reconciliation(*args,actor_id='original')['command_key']=='own-key'
    with pytest.raises(ErclaveError) as exc:repo.prepare_production_reconciliation(*args,actor_id='different')
    assert exc.value.code=='idempotency_key_reused' and exc.value.status_code==409
    conn.execute(text('update sales.production_reconciliations set request_hash=:h where tenant_id=:t and order_line_id=:i'),{'h':'hash','t':TENANT,'i':line.id})
    with pytest.raises(ErclaveError) as exc:repo.prepare_production_reconciliation(*args,actor_id='original')
    assert exc.value.code=='idempotency_key_reused'


class Audits:
    def __init__(self,actors):self.actors=actors
    def execute(self,*args):return SimpleNamespace(scalars=lambda:SimpleNamespace(all=lambda:self.actors))


@pytest.mark.parametrize('actors,actor,allowed',[(['original'],'original',True),(['original'],'other',False),([], 'original',False),(['original','other'],'original',False)])
def test_legacy_receipt_authorship_must_be_unambiguous(actors,actor,allowed):
    repo=repos.SalesRepository(None);row={'request_hash':'legacy','created_at':datetime.now(timezone.utc)}
    if allowed:repo._validate_receipt(Audits(actors),TENANT,'quote.approved',row,'legacy',actor)
    else:
        with pytest.raises(ValueError,match='idempotency_key_reused'):repo._validate_receipt(Audits(actors),TENANT,'quote.approved',row,'legacy',actor)
