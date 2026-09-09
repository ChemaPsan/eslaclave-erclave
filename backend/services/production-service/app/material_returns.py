from decimal import Decimal
from sqlalchemy import text


class ProductionMaterialReturns:
    def _return_resource(self,c,t,p):
        row=c.execute(text("""select r.id,r.production_order_id order_id,o.code source_code,o.status,r.actual_quantity,
            coalesce((select sum(a.quantity) from production.material_return_adjustments a where a.tenant_id=r.tenant_id and a.resource_id=r.id),0) returned_quantity
            from production.production_order_resources r join production.production_orders o on o.tenant_id=r.tenant_id and o.id=r.production_order_id
            join production.production_order_resource_reservations rr on rr.tenant_id=r.tenant_id and rr.production_order_resource_id=r.id
            where r.tenant_id=:t and o.id=:order and rr.reservation_ref_id=:reservation and r.resource_type='material' for update of o,r"""),{"t":t,"order":p['source_id'],"reservation":p['reservation_id']}).mappings().first()
        if not row:raise ValueError('material_return_source_invalid')
        if row['status'] not in {'completed','cancelled'}:raise ValueError('material_return_terminal_order_required')
        if Decimal(str(p['quantity']))>Decimal(row['actual_quantity'] or 0)-row['returned_quantity']:raise ValueError('material_return_quantity_exceeded')
        return row

    def validate_material_return(self,t,p):
        with self.engine.begin() as c:return dict(self._return_resource(c,t,p))

    def reconcile_material_return(self,t,p,actor):
        if p['source_type']!='production_order' or p['status'] not in {'received_pending_reconciliation','completed'} or not p.get('movement_id'):raise ValueError('material_return_receipt_required')
        with self.engine.begin() as c:
            # Serializes distinct returns for the same order as well as replayed callbacks.
            c.execute(text('select id from production.production_orders where tenant_id=:t and id=:id for update'),{'t':t,'id':p['source_id']}).first()
            if c.execute(text('select 1 from production.material_return_adjustments where tenant_id=:t and return_id=:id'),{'t':t,'id':p['id']}).first():return {'id':p['id'],'status':'completed'}
            resource=self._return_resource(c,t,p)
            quantity=Decimal(str(p['quantity']));unit_cost=Decimal(str(p.get('unit_cost') or 0))
            c.execute(text("""insert into production.material_return_adjustments(tenant_id,return_id,order_id,resource_id,original_movement_id,movement_id,quantity,unit_cost,actor_id)
                values(:t,:id,:order,:resource,:original,:movement,:q,:cost,:actor)"""),{'t':t,'id':p['id'],'order':p['source_id'],'resource':resource['id'],'original':p['original_movement_id'],'movement':p['movement_id'],'q':quantity,'cost':unit_cost,'actor':actor})
            c.execute(text('update production.production_order_resources set actual_cost=greatest(coalesce(actual_cost,0)-:cost,0) where tenant_id=:t and id=:id'),{'cost':quantity*unit_cost,'t':t,'id':resource['id']})
            c.execute(text('update production.production_orders set actual_cost=(select coalesce(sum(coalesce(actual_cost,planned_cost)),0) from production.production_order_resources where tenant_id=:t and production_order_id=:id),updated_at=now() where tenant_id=:t and id=:id'),{'t':t,'id':p['source_id']})
            self._audit(c,t,actor,'order.material_return','production_order',p['source_id'],None,{'return_id':p['id'],'quantity':str(quantity),'movement_id':p['movement_id']},'return-'+p['id'])
            return {'id':p['id'],'status':'completed'}

    def returnable_materials(self,t,limit=25,offset=0):
        with self.engine.connect() as c:
            return [dict(row) for row in c.execute(text("""select v.value->>'id' id,o.code,r.resource_code item_code,r.resource_name_snapshot item_name,r.unit,
                (v.value->>'quantity')::numeric-coalesce((select sum(a.quantity) from production.material_return_adjustments a where a.tenant_id=o.tenant_id and a.original_movement_id=v.value->>'id'),0) quantity
                from production.material_issues i join production.production_orders o on o.tenant_id=i.tenant_id and o.id=i.production_order_id
                cross join lateral jsonb_each(i.movements) v
                join production.production_order_resource_reservations rr on rr.tenant_id=o.tenant_id and rr.reservation_ref_id=v.key
                join production.production_order_resources r on r.tenant_id=rr.tenant_id and r.id=rr.production_order_resource_id
                where o.tenant_id=:t and o.status in ('completed','cancelled')
                and (v.value->>'quantity')::numeric>coalesce((select sum(a.quantity) from production.material_return_adjustments a where a.tenant_id=o.tenant_id and a.original_movement_id=v.value->>'id'),0)
                order by o.created_at,o.id,r.id,v.key limit :limit offset :offset"""),{'t':t,'limit':limit,'offset':offset}).mappings()]
