"""Real HTTP purchasing handoff; Local demo tenant, exact-owned fixture cleanup."""
import os
from datetime import datetime,timezone
from contextlib import contextmanager
from sqlalchemy import text
from smoke_production_warehouse_local import ROOT,fixture_module
from smoke_maintenance_local import call,firebase_token,require_local,LOCAL_APIS,TENANT

def main():
    database=next(line.split('=',1)[1].strip() for line in (ROOT/'backend/.env').read_text(encoding='utf-8').splitlines() if line.startswith('ERCLAVE_INVENTORY_DATABASE_URL='))
    require_local(database)
    os.environ['ERCLAVE_TEST_DATABASE_URL']=database;os.environ['ERCLAVE_TEST_TENANT_ID']=TENANT
    token=firebase_token();context=call(LOCAL_APIS['admin']+'/v1/session/context',token)
    assert context['tenant']['id']==TENANT
    actor=context['user']['id']
    inventory=fixture_module('handoff_inventory','backend/services/inventory-service/tests/test_inventory_repository_integration.py')
    purchasing=fixture_module('handoff_purchasing','backend/services/purchasing-service/tests/test_purchasing_handoffs_integration.py')
    with contextmanager(inventory.stocked_resource.__wrapped__)() as stock,contextmanager(purchasing.purchasing_handoff.__wrapped__)() as purchase:
        inv,t,item,warehouse,suffix,_,prefix=stock
        repo,t,order,requester,buyer,warehouse_actor,key=purchase
        receipt=None
        try:
            # The repository fixture uses a synthetic unit; HTTP validates the
            # actual Local catalog, so normalize only these owned fixture rows.
            with inv.engine.begin() as c:
                c.execute(text("update inventory.items set base_unit='H87' where tenant_id=:t and id=:i"),{'t':t,'i':item.id})
                c.execute(text("update inventory.movements set unit='H87' where tenant_id=:t and inventory_item_id=:i"),{'t':t,'i':item.id})
            item=item.model_copy(update={'base_unit':'H87'})
            with repo.engine.begin() as c:
                c.execute(text("update purchasing.purchase_order_lines set inventory_item_ref_id=:item,unit_code=:unit where tenant_id=:t and purchase_order_id=:o and line_type='inventory_item'"),{'item':item.id,'unit':item.base_unit,'t':t,'o':order['id']})
            url='http://127.0.0.1:8010/v1/purchasing'
            receipt=call(url+'/receipts',token,'POST',{'code':'REC-'+suffix,'purchase_order_id':order['id'],'received_at':datetime.now(timezone.utc).isoformat(),'lines':[{'order_line_id':line['id'],'quantity':float(line['quantity']),'warehouse_id':warehouse.id if line['line_type']=='inventory_item' else None} for line in order['lines']]},key+'-http-prepare')
            assert receipt['status']=='pending_confirmation'
            with inv.engine.connect() as c:assert inv._balance(c,t,item.id,warehouse.id,item.base_unit)==10
            confirmed=call(url+'/receipts/'+receipt['id']+'/reconcile',token,'POST',{},key+'-http-receive')
            assert confirmed['status']=='pending_confirmation',confirmed
            call(url+'/receipts/'+receipt['id']+'/reconcile',token,'POST',{},key+'-http-receive')
            with inv.engine.connect() as c:assert inv._balance(c,t,item.id,warehouse.id,item.base_unit)==12
            try:call(url+'/receipts/'+receipt['id']+'/accept-services',token,'POST',{},key+'-http-denied')
            except RuntimeError as exc:assert 'purchased_service_requester_required' in str(exc),str(exc)
            else:raise AssertionError('Non-requester accepted service')
            with repo.engine.begin() as c:c.execute(text('update purchasing.requisitions set requested_by_actor_id=:a where tenant_id=:t and id=(select requisition_id from purchasing.purchase_orders where tenant_id=:t and id=:o)'),{'t':t,'o':order['id'],'a':actor})
            accepted=call(url+'/receipts/'+receipt['id']+'/accept-services',token,'POST',{},key+'-http-accept')
            assert accepted['status']=='completed',accepted
            assert next(row for row in call(url+'/orders',token) if row['id']==order['id'])['status']=='received'
            print('PASS: HTTP preparation leaves stock unchanged; Warehouse receives once; non-requester rejected; requester accepts service and completes mixed receipt.')
        finally:
            with repo.engine.begin() as c:
                c.execute(text('delete from purchasing.audit_events where tenant_id=:t and entity_id=any(:ids)'),{'t':t,'ids':[order['id'],receipt['id'] if receipt else '']})
            with inv.engine.begin() as c:
                c.execute(text('delete from inventory.audit_events where tenant_id=:t and entity_id in (select id from inventory.movements where tenant_id=:t and inventory_item_id=:i)'),{'t':t,'i':item.id})
                if receipt:
                    for line in receipt['lines']:c.execute(text('delete from inventory.idempotency_records where tenant_id=:t and idempotency_key=:k'),{'t':t,'k':line['inventory_idempotency_key']})

if __name__=='__main__':main()
