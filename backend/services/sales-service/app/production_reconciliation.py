"""Sales owns recovery of manufactured lines; Inventory owns their reservation."""
import json
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import text
from erclave_common.organization_client import deny
from .schemas import SalesOrderRead


class ProductionReconciliationRepository:
    def fulfillment_replay(self, tenant, order_id, key, digest):
        with self.engine.connect() as connection:
            row=connection.execute(text("select request_hash,response_payload from sales.idempotency_records where tenant_id=:t and operation=:op and idempotency_key=:k"),{'t':tenant,'op':f'order.fulfillment:{order_id}','k':key}).mappings().first()
            if row:
                if row['request_hash']!=digest:raise ValueError('idempotency_key_reused')
                if row['response_payload']:
                    return SalesOrderRead.model_validate(row['response_payload'])
        return None

    def production_intent(self,tenant,order_id,line_id):
        with self.engine.connect() as conn:
            plan=conn.execute(text('select fulfillment_plan from sales.orders where tenant_id=:t and id=:i'),{'t':tenant,'i':order_id}).scalar()
        return next((line for line in (plan or {}).get('lines',[]) if line['order_line_id']==line_id),None)

    def production_reconciliation(self,tenant,order_id,line_id):
        with self.engine.connect() as conn:
            row=conn.execute(text('select * from sales.production_reconciliations where tenant_id=:t and order_id=:o and order_line_id=:l'),{'t':tenant,'o':order_id,'l':line_id}).mappings().first()
            return dict(row) if row else None

    def prepare_production_reconciliation(self,tenant,order_id,line_id,warehouse,product,source,key,digest):
        with self.engine.begin() as conn:
            conn.execute(text('select id from sales.orders where tenant_id=:t and id=:o for update'),{'t':tenant,'o':order_id}).first()
            order=self._order(conn,tenant,order_id)
            if not order:deny('sales_order_not_found',404)
            if order.status in ('cancelled','delivered') or order.cancellation_state!='idle':deny('sales_order_not_fulfillable',409)
            line=next((line for line in order.lines if line.id==line_id),None)
            if not line or line.fulfillment_mode!='production' or not line.production_request_id:deny('production_request_source_conflict',409)
            existing=conn.execute(text('select * from sales.production_reconciliations where tenant_id=:t and order_line_id=:l for update'),{'t':tenant,'l':line_id}).mappings().first()
            if existing:
                if existing['request_hash']!=digest:deny('production_reconciliation_in_progress',409)
                return dict(existing)
            if line.fulfillment_status!='production_requested' or line.delivered_quantity:deny('sales_order_line_already_configured',409)
            amount=line.ordered_quantity-line.delivered_quantity
            values={'t':tenant,'o':order_id,'l':line_id,'request':line.production_request_id,'production':source['production_order_id'],'wh':warehouse,'item':product['id'],'qty':amount,'unit':line.unit,'key':key,'hash':digest,'snapshot':json.dumps(source,default=str)}
            conn.execute(text("insert into sales.production_reconciliations(tenant_id,order_id,order_line_id,request_id,production_order_id,warehouse_id,inventory_item_id,quantity,unit,command_key,request_hash,status,source_snapshot) values(:t,:o,:l,:request,:production,:wh,:item,:qty,:unit,:key,:hash,'processing',cast(:snapshot as jsonb))"),values)
            return {'order_id':order_id,'order_line_id':line_id,'request_id':line.production_request_id,'production_order_id':source['production_order_id'],'warehouse_id':warehouse,'inventory_item_id':product['id'],'quantity':amount,'unit':line.unit,'command_key':key,'request_hash':digest,'status':'processing','source_snapshot':source}

    def fail_production_reconciliation(self,tenant,line_id,error_code):
        with self.engine.begin() as conn:
            conn.execute(text("update sales.production_reconciliations set status='needs_reconciliation',error_code=:e,updated_at=now() where tenant_id=:t and order_line_id=:l and status!='completed'"),{'t':tenant,'l':line_id,'e':str(error_code)[:120]})

    def finish_production_reconciliation(self,tenant,order_id,line_id,reservation,product,digest,actor):
        with self.engine.begin() as conn:
            conn.execute(text('select id from sales.orders where tenant_id=:t and id=:o for update'),{'t':tenant,'o':order_id}).first()
            order=self._order(conn,tenant,order_id)
            if order.cancellation_state!='idle' or order.status=='cancelled':deny('sales_order_not_fulfillable',409)
            state=conn.execute(text('select * from sales.production_reconciliations where tenant_id=:t and order_id=:o and order_line_id=:l for update'),{'t':tenant,'o':order_id,'l':line_id}).mappings().one()
            if state['request_hash']!=digest:deny('production_reconciliation_in_progress',409)
            if state['status']=='completed':return order
            if (reservation.get('source_type')!='sales_order' or reservation.get('inventory_item_id')!=state['inventory_item_id'] or reservation.get('warehouse_id')!=state['warehouse_id'] or Decimal(str(reservation.get('quantity',0)))!=state['quantity'] or reservation.get('unit')!=state['unit'] or reservation.get('status')!='active' or reservation.get('source_id')!=order_id or reservation.get('source_line_id')!=line_id):deny('operational_context_mismatch',409)
            cost=reservation.get('original_unit_cost') if order.division_ref_id else reservation.get('unit_cost_snapshot')
            if cost is None:deny('operational_cost_currency_unavailable',409)
            conn.execute(text("insert into sales.order_line_reservations(id,tenant_id,order_line_id,reservation_ref_id,warehouse_ref_id,reserved_quantity,consumed_quantity,unit_cost_snapshot,status) values(:id,:t,:l,:r,:wh,:qty,0,:cost,'active') on conflict(tenant_id,reservation_ref_id) do nothing"),{'id':'slr_'+uuid4().hex[:26],'t':tenant,'l':line_id,'r':reservation['id'],'wh':state['warehouse_id'],'qty':state['quantity'],'cost':Decimal(str(cost))})
            conn.execute(text("update sales.order_lines set fulfillment_status='reserved',inventory_item_ref_id=:i,inventory_item_code_snapshot=:code,inventory_item_name_snapshot=:name,updated_at=now() where tenant_id=:t and id=:l"),{'t':tenant,'l':line_id,'i':state['inventory_item_id'],'code':product['code'],'name':product['name']})
            conn.execute(text("update sales.production_reconciliations set status='completed',reservation_ref_id=:r,error_code=null,updated_at=now() where tenant_id=:t and order_line_id=:l"),{'t':tenant,'l':line_id,'r':reservation['id']})
            states=conn.execute(text('select fulfillment_status from sales.order_lines where tenant_id=:t and order_id=:o'),{'t':tenant,'o':order_id}).scalars().all()
            target='delivered' if all(x=='delivered' for x in states) else 'partially_delivered' if any(x in ('delivered','partially_delivered') for x in states) else 'ready' if all(x in ('reserved','ready') for x in states) else 'fulfillment_pending'
            conn.execute(text('update sales.orders set status=:status,updated_at=now() where tenant_id=:t and id=:o'),{'t':tenant,'o':order_id,'status':target})
            self._audit(conn,tenant,actor,'order.production_reconciliation','sales_order',order_id,{'line_id':line_id,'request_id':state['request_id'],'production_order_id':state['production_order_id'],'reservation_id':reservation['id'],'quantity':state['quantity'],'original_unit_cost':cost})
            return self._order(conn,tenant,order_id)
