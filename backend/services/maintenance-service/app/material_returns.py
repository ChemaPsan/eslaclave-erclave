from decimal import Decimal
from sqlalchemy import text


class MaintenanceMaterialReturns:
    def _return_resource(self,c,t,p,require_terminal=True):
        row=c.execute(text("""select l.id,o.id order_id,o.code source_code,o.status,l.quantity actual_quantity,
            coalesce((select sum(a.quantity) from maintenance.material_return_adjustments a where a.tenant_id=l.tenant_id and a.resource_id=l.id),0) returned_quantity
            from maintenance.material_request_lines l join maintenance.material_requests r on r.tenant_id=l.tenant_id and r.id=l.material_request_id
            join maintenance.orders o on o.tenant_id=r.tenant_id and o.id=r.order_id
            where l.tenant_id=:t and o.id=:order and l.reservation_ref_id=:reservation and l.inventory_movement_ref_id=:movement and l.line_status='issued' for update of o,l"""),{'t':t,'order':p['source_id'],'reservation':p['reservation_id'],'movement':p['original_movement_id']}).mappings().first()
        if not row:raise ValueError('material_return_source_invalid')
        if require_terminal and row['status'] not in {'resolved','closed','cancelled'}:raise ValueError('material_return_terminal_order_required')
        if Decimal(str(p['quantity']))>row['actual_quantity']-row['returned_quantity']:raise ValueError('material_return_quantity_exceeded')
        return row

    def validate_material_return(self,t,p):
        with self.engine.begin() as c:return dict(self._return_resource(c,t,p))

    def reconcile_material_return(self,t,p,actor):
        if p['source_type']!='maintenance_order' or p['status'] not in {'received_pending_reconciliation','completed'} or not p.get('movement_id'):raise ValueError('material_return_receipt_required')
        with self.engine.begin() as c:
            c.execute(text('select id from maintenance.orders where tenant_id=:t and id=:id for update'),{'t':t,'id':p['source_id']}).first()
            if c.execute(text('select 1 from maintenance.material_return_adjustments where tenant_id=:t and return_id=:id'),{'t':t,'id':p['id']}).first():return {'id':p['id'],'status':'completed'}
            # Receipt is already authoritative in Inventory. A concurrent reopen
            # must not prevent the owner from recording that physical return.
            resource=self._return_resource(c,t,p,require_terminal=False)
            c.execute(text("""insert into maintenance.material_return_adjustments(tenant_id,return_id,order_id,resource_id,original_movement_id,movement_id,quantity,unit_cost,actor_id)
                values(:t,:id,:order,:resource,:original,:movement,:q,:cost,:actor)"""),{'t':t,'id':p['id'],'order':p['source_id'],'resource':resource['id'],'original':p['original_movement_id'],'movement':p['movement_id'],'q':Decimal(str(p['quantity'])),'cost':Decimal(str(p.get('unit_cost') or 0)),'actor':actor})
            self._audit(c,t,actor,'maintenance.material_return','order',p['source_id'],{'return_id':p['id'],'quantity':p['quantity'],'movement_id':p['movement_id']})
            return {'id':p['id'],'status':'completed'}

    def returnable_materials(self,t,limit=25,offset=0):
        with self.engine.connect() as c:
            return [dict(row) for row in c.execute(text("""select l.inventory_movement_ref_id id,o.code,l.item_code_snapshot item_code,l.item_name_snapshot item_name,l.unit_code unit,
                l.quantity-coalesce((select sum(a.quantity) from maintenance.material_return_adjustments a where a.tenant_id=l.tenant_id and a.resource_id=l.id),0) quantity
                from maintenance.material_request_lines l join maintenance.material_requests r on r.tenant_id=l.tenant_id and r.id=l.material_request_id
                join maintenance.orders o on o.tenant_id=r.tenant_id and o.id=r.order_id
                where o.tenant_id=:t and o.status in ('resolved','closed','cancelled') and l.line_status='issued'
                and l.quantity>coalesce((select sum(a.quantity) from maintenance.material_return_adjustments a where a.tenant_id=l.tenant_id and a.resource_id=l.id),0)
                order by o.created_at,o.id,l.id limit :limit offset :offset"""),{'t':t,'limit':limit,'offset':offset}).mappings()]
