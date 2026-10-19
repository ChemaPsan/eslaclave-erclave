"""CC-12 Local-only HTTP acceptance with exact owned fixture cleanup."""
from cc12_local_fixture import cc12_fixture,LOCAL_TENANT
from datetime import date,datetime,timezone
from decimal import Decimal
from urllib import request,error
import json


def main():
 with cc12_fixture() as f:
  x=f.ids
  def http(service,path,method='GET',payload=None,key=None,expected=(200,201)):
   ports={'sales':8008,'production':8002,'inventory':8004}
   headers={'Authorization':'Bearer '+f.token,'X-Tenant-Id':LOCAL_TENANT,'Content-Type':'application/json'}
   if key:headers['Idempotency-Key']=f.prefix+'-'+key
   req=request.Request('http://127.0.0.1:'+str(ports[service])+'/v1/'+service+path,headers=headers,method=method,data=json.dumps(payload).encode() if payload is not None else None)
   try:
    with request.urlopen(req,timeout=40) as response:status=response.status;body=json.loads(response.read())
   except error.HTTPError as e:status=e.code;body=json.loads(e.read())
   assert status in expected,(service,method,path,status,body)
   print(method,service+path,status,flush=True)
   return body.get('data',body)
  plan={'lines':[{'order_line_id':x['line'],'mode':'production','allocations':[]}],'cost_exchange_rate':'0.05'}
  order=http('sales','/orders/'+x['order']+'/fulfillment','POST',plan,'fulfill')
  order=http('sales','/orders/'+x['order'])
  request_id=order['lines'][0]['production_request_id']
  req=http('production','/order-requests/'+request_id)
  assert req['organization_context']['division_ref_id']==x['division']
  reconcile={'order_line_id':x['line'],'warehouse_id':x['warehouse']}
  http('sales','/orders/'+x['order']+'/production-reconciliations','POST',reconcile,'early',expected=(409,422))
  base={'division_ref_id':x['division'],'recipe_version_id':x['version'],'quantity':'2','unit':'H87','planned_start_date':str(date.today()),'planned_duration_days':1}
  validation=http('production','/order-requests/'+request_id+'/resource-validations','POST',base,'validate')
  assert validation['can_release'] and Decimal(validation['original_planned_cost'])==Decimal('60')
  create=dict(base,code=f.prefix+'-OP',responsible_worker_id=x['worker'],stage_assignments=[{'recipe_stage_id':x['stage'],'responsible_worker_id':x['worker']}])
  http('production','/order-requests/'+request_id+'/orders','POST',dict(create,quantity='3'),'tampered',expected=(409,422))
  po=http('production','/order-requests/'+request_id+'/orders','POST',create,'convert')
  replay=http('production','/order-requests/'+request_id+'/orders','POST',create,'convert')
  assert po['id']==replay['id'];pid=po['id'];f.owned.add(pid)
  http('production','/orders/'+pid+'/issue-materials','POST',{},'issue')
  http('production','/orders/'+pid+'/status','PATCH',{'status':'in_progress','reason':'CC12 synthetic acceptance'},'start')
  for resource in po['resources']:
   if resource['resource_type']!='material':
    http('production','/orders/'+pid+'/resources/'+resource['id'],'PATCH',{'actual_quantity':resource['planned_quantity']},'actual-'+resource['id'])
  for stage in po['stages']:
   http('production','/order-stages/'+stage['id'],'PATCH',{'status':'completed','progress_percent':100,'actual_minutes':20},'stage-'+stage['id'])
  done=http('production','/orders/'+pid+'/status','PATCH',{'status':'completed','reason':'CC12 synthetic completion'},'complete')
  assert Decimal(done['original_actual_cost'])==Decimal('60')
  http('sales','/orders/'+x['order']+'/production-reconciliations','POST',reconcile,'before-receipt',expected=(409,422))
  receipt={'production_order_id':pid,'warehouse_id':x['warehouse'],'quantity':2,'received_at':datetime.now(timezone.utc).isoformat(),'notes':'CC12 synthetic receipt'}
  received=http('inventory','/finished-goods-receipts','POST',receipt,'receipt')
  http('inventory','/finished-goods-receipts','POST',receipt,'receipt')
  status=http('sales','/orders/'+x['order']+'/production-status?line_id='+x['line'])
  print('STATUS',json.dumps(status),flush=True)
  reconciled=http('sales','/orders/'+x['order']+'/production-reconciliations','POST',reconcile,'reconcile')
  http('sales','/orders/'+x['order']+'/production-reconciliations','POST',reconcile,'reconcile')
  delivery=http('sales','/deliveries','POST',{'code':f.prefix+'-DEL','order_id':x['order'],'scheduled_date':str(date.today()),'lines':[{'order_line_id':x['line'],'quantity':2}]},'delivery')
  did=delivery['id'];f.owned.add(did)
  dispatch=http('sales','/deliveries/'+did+'/confirm','POST',{'reason':'CC12 synthetic dispatch'},'dispatch')
  http('sales','/deliveries/'+did+'/confirm','POST',{'reason':'CC12 synthetic dispatch'},'dispatch')
  print('DISPATCH',json.dumps(dispatch),flush=True)
  from sqlalchemy import text
  with f.engine.connect() as c:
   line=c.execute(text('select * from sales.delivery_lines where tenant_id=:t and delivery_id=:d'),{'t':LOCAL_TENANT,'d':did}).mappings().one()
   assert line['original_actual_cost']==Decimal('60') and line['actual_cost']==Decimal('3'),dict(line)
   movements=c.execute(text("select direction,sum(quantity) q from inventory.movements where tenant_id=:t and inventory_item_id=:i group by direction"),{'t':LOCAL_TENANT,'i':x['finished']}).all()
   assert dict(movements)=={'in':Decimal('2'),'out':Decimal('2')},movements
   assert c.execute(text('select count(*) from production.production_orders where tenant_id=:t and source_id=:o'),{'t':LOCAL_TENANT,'o':x['order']}).scalar()==1
   assert c.execute(text("select sum(quantity) from inventory.movements where tenant_id=:t and inventory_item_id=:i and direction='out'"),{'t':LOCAL_TENANT,'i':x['material']}).scalar()==Decimal('4')
  print('PASS CC12 real HTTP: Sales -> Production -> material consumption -> finished goods -> Sales reservation -> dispatch; 60MXN -> 3USD; replays do not duplicate stock',flush=True)

if __name__=='__main__':main()
