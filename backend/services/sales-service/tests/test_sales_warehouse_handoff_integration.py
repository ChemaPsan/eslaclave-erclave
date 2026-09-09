import importlib,os,sys
from pathlib import Path
from datetime import date,datetime,timedelta
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import create_engine,text
from erclave_common.errors import ErclaveError

DATABASE_URL=os.getenv('ERCLAVE_TEST_DATABASE_URL','')
pytestmark=pytest.mark.skipif(not DATABASE_URL,reason='Local PostgreSQL is required')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repos=importlib.import_module('app.repositories');schemas=importlib.import_module('app.schemas');api=importlib.import_module('app.api')


def test_sales_prepares_and_warehouse_dispatches_with_stable_retry_keys():
    t=os.getenv('ERCLAVE_TEST_TENANT_ID','ten_739ee59d765d5e14818674800d');assert t=='ten_739ee59d765d5e14818674800d'
    engine=create_engine(DATABASE_URL);repo=repos.SalesRepository(engine);suffix=uuid4().hex[:14];key='wh-'+suffix;actor='usr_'+suffix
    customer=quote=order=delivery=None
    try:
        worker=schemas.WorkerReference(id='hrw_'+suffix,employee_number='TEST',full_name='Responsable sintético',position_name='Ventas',labor_area_name='Ventas',status='active')
        customer=repo.create_customer(t,schemas.CustomerCreateRequest(code='CLI-'+suffix,commercial_name='Cliente sintético',customer_type='company',status='active',responsible_worker_id=worker.id,primary_contact={'name':'Contacto','email':suffix+'@example.com','phone':'5512345678'},payment_terms='cash',currency='MXN'),worker,key+'-customer','customer',actor)
        product=schemas.ProductReference(id='prd_'+suffix,code='PRD-'+suffix,name='Producto sintético',type='product',base_unit='H87',status='active',target_price=100,standard_cost=5,inventory_item_id='itm_'+suffix)
        quote=repo.create_quote(t,schemas.QuoteCreateRequest(code='COT-'+suffix,customer_id=customer.id,valid_until=date.today()+timedelta(days=3),lines=[{'product_service_id':product.id,'quantity':2,'unit':'H87','unit_price':100}]),customer,worker,[schemas.ResolvedQuoteLine(product=product,quantity=Decimal('2'),unit='H87',unit_price=Decimal('100'),discount_percentage=Decimal('0'))],key+'-quote','quote',actor)
        repo.transition_quote(t,quote.id,'quoted',key+'-submit','submit',actor)
        quote=repo.transition_quote(t,quote.id,'approved',key+'-approve','approve',actor)
        order=repo.create_order(t,schemas.SalesOrderCreateRequest(code='PED-'+suffix,quote_id=quote.id),quote,key+'-order','order',actor)
        configured=repo.configure_order_fulfillment(t,order.id,[{'order_line_id':order.lines[0].id,'mode':'stock','inventory_item_id':product.inventory_item_id,'reservations':[{'id':'rsv_'+suffix,'warehouse_id':'wh_'+suffix,'quantity':Decimal('2'),'unit_cost_snapshot':Decimal('5')}]}],key+'-fulfill','fulfill',actor)
        delivery=repo.create_delivery(t,schemas.DeliveryCreateRequest(code='DEL-'+suffix,order_id=order.id,scheduled_date=date.today(),lines=[{'order_line_id':order.lines[0].id,'quantity':2}]),key+'-delivery','delivery',actor)
        assert delivery.status=='draft' and repo.get_order(t,order.id).lines[0].delivered_quantity==0
        row=next(r for r in repo.list_warehouse_deliveries(t,100) if r['id']==delivery.id)
        assert row['lines'][0]['allocations']==[{'warehouse_id':'wh_'+suffix,'quantity':Decimal('2')}]
        assert not repo.list_warehouse_deliveries('other-tenant')
        class Inventory:
            fail=True
            keys=[]
            def consume_reservation(self,t,reservation,q,reason,authorization,key):
                self.keys.append(key)
                if self.fail:raise ErclaveError('inventory_unavailable','Retry',503)
                return {'id':'mov_'+suffix,'quantity':q,'unit_cost':5}
        inventory=Inventory();payload=schemas.ActionReasonRequest(reason='Entrega física verificada')
        commercial=api.AuthorizedContext(t,actor,'sales.delivery.confirm',frozenset({'sales.delivery.confirm'}))
        with pytest.raises(ErclaveError) as denied:api.confirm_delivery(delivery.id,payload,t,None,key+'-confirm',repo,inventory,commercial)
        assert denied.value.code=='sales_warehouse_dispatch_required' and inventory.keys==[]
        warehouse=api.AuthorizedContext(t,actor,'inventory.movement.create',frozenset({'inventory.movement.create'}))
        with pytest.raises(ErclaveError):api.confirm_delivery(delivery.id,payload,t,None,key+'-confirm',repo,inventory,warehouse)
        assert repo.get_delivery(t,delivery.id).confirmation_state=='needs_reconciliation'
        inventory.fail=False
        result=api.confirm_delivery(delivery.id,payload,t,None,key+'-retry',repo,inventory,warehouse).data
        assert result.status=='confirmed' and len(set(inventory.keys))==1
        api.confirm_delivery(delivery.id,payload,t,None,key+'-again',repo,inventory,warehouse)
        assert len(inventory.keys)==2
        assert repo.get_order(t,order.id).status=='delivered'
        assert repo.get_delivery(t,delivery.id).lines[0].actual_cost==10
    finally:
        with engine.begin() as c:
            if delivery:c.execute(text('delete from sales.deliveries where tenant_id=:t and id=:id'),{'t':t,'id':delivery.id})
            if order:c.execute(text('delete from sales.orders where tenant_id=:t and id=:id'),{'t':t,'id':order.id})
            if quote:c.execute(text('delete from sales.quotes where tenant_id=:t and id=:id'),{'t':t,'id':quote.id})
            if customer:c.execute(text('delete from sales.customers where tenant_id=:t and id=:id'),{'t':t,'id':customer.id})
            c.execute(text('delete from sales.audit_events where tenant_id=:t and actor_id=:actor'),{'t':t,'actor':actor})
            c.execute(text('delete from sales.idempotency_records where tenant_id=:t and idempotency_key like :key'),{'t':t,'key':key+'%'})
        engine.dispose()
