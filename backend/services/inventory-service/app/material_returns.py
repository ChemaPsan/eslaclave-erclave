from contextlib import contextmanager
from datetime import datetime,timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from erclave_common.business_codes import derived_manual_code,allocate_movement_code
from .schemas import MaterialReturnRead,MovementCreate,SourceRef
from .reservation_context import validate_local_context,validate_cost_currency


class InventoryMaterialReturns:
    def begin_material_return_command(self,t,id,action,key,digest,actor):
        operation='material_return.'+action
        with self.engine.begin() as c:
            replay=self._claim(c,t,operation,key,digest,actor,resume_pending=True)
            if replay:return MaterialReturnRead.model_validate(replay)
            self._audit(c,t,actor,operation+'.prepare','material_return',id,{'idempotency_key':key})
            return None

    def finish_material_return_command(self,t,action,key,value):
        # A dependency failure is an unfinished intent, not a final receipt: the
        # same authenticated actor must still be able to reconcile on retry.
        if value.status not in ('completed','cancelled'):return value
        with self.engine.begin() as c:self._done(c,t,'material_return.'+action,key,value)
        return value

    def replay_material_return_request(self,t,key,digest,actor=None):
        with self.engine.connect() as c:
            row=c.execute(text("select request_hash,response_payload,created_at from inventory.idempotency_records where tenant_id=:t and operation='material_return.request' and idempotency_key=:key"),{'t':t,'key':key}).mappings().first()
            if not row:return None
            self._validate_receipt(c,t,'material_return.request',key,row,digest,actor)
            return self._material_return(c,t,row['response_payload']['id']) if row['response_payload'] else None

    @contextmanager
    def return_command_lock(self,t,id):
        with self.engine.connect() as c:
            key=f"inventory-return:{t}:{id}"
            if not c.execute(text("select pg_try_advisory_lock(hashtextextended(:k,0))"),{"k":key}).scalar_one():
                raise ErclaveError("command_in_progress","Material return is being received.",status_code=409)
            c.commit()
            try:yield
            finally:c.execute(text("select pg_advisory_unlock(hashtextextended(:k,0))"),{"k":key});c.commit()

    def return_source(self,t,movement_id):
        with self.engine.connect() as c:
            row=c.execute(text("""select m.id original_movement_id,m.source_id reservation_id,r.source_type,r.source_id,
                m.quantity,m.unit_cost,m.organization_context,m.inventory_item_id,m.warehouse_id,m.unit
                from inventory.movements m join inventory.reservations r on r.tenant_id=m.tenant_id and r.id=m.source_id
                where m.tenant_id=:t and m.id=:id and m.direction='out' and m.source_type='reservation' and m.status='recorded'
                and r.source_type in ('production_order','maintenance_order')"""),{"t":t,"id":movement_id}).mappings().first()
            if not row:raise ValueError("material_return_source_invalid")
            return dict(row)

    def _material_return(self,c,t,id):
        row=c.execute(text("""select r.*,m.inventory_item_id,m.warehouse_id,m.unit,m.unit_cost,m.organization_context,i.code item_code,i.name item_name,w.name warehouse_name
            from inventory.material_returns r join inventory.movements m on m.tenant_id=r.tenant_id and m.id=r.original_movement_id
            join inventory.items i on i.tenant_id=m.tenant_id and i.id=m.inventory_item_id
            join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id where r.tenant_id=:t and r.id=:id"""),{"t":t,"id":id}).mappings().first()
        return MaterialReturnRead.model_validate(dict(row)) if row else None

    def get_material_return(self,t,id):
        with self.engine.connect() as c:return self._material_return(c,t,id)

    def list_material_returns(self,t,limit=25,offset=0,allowed_divisions=None):
        params={"t":t,"limit":limit,"offset":offset}
        scope=""
        if allowed_divisions is not None:
            scope=" and coalesce(m.organization_context->>'division_ref_id',w.division_ref_id)=any(:divisions)"
            params['divisions']=allowed_divisions
        with self.engine.connect() as c:
            ids=c.execute(text("""select r.id from inventory.material_returns r
                join inventory.movements m on m.tenant_id=r.tenant_id and m.id=r.original_movement_id
                join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id
                where r.tenant_id=:t and r.status in ('pending','received_pending_reconciliation')"""+scope+
                " order by r.created_at,r.id limit :limit offset :offset"),params).scalars().all()
            return [self._material_return(c,t,id) for id in ids]

    def request_material_return(self,t,p,source,source_code,key,digest,actor):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"material_return.request",key,digest,actor)
            if replay:return MaterialReturnRead.model_validate(replay)
            locked=c.execute(text("select id,quantity,direction,source_type,source_id from inventory.movements where tenant_id=:t and id=:id for update"),{"t":t,"id":p.original_movement_id}).mappings().first()
            original=self._movement(c,t,p.original_movement_id)
            if not locked or not original or original.status!='recorded' or locked['direction']!='out' or locked['source_type']!='reservation' or locked['source_id']!=source['reservation_id']:raise ValueError("material_return_source_invalid")
            if original.organization_context:
                if not original.organization_context.cost_currency or original.original_unit_cost is None:raise ValueError("operational_cost_currency_unavailable")
                validate_local_context(c,t,original,original.organization_context)
            prior=c.execute(text("select coalesce(sum(quantity),0) from inventory.material_returns where tenant_id=:t and original_movement_id=:id and status!='cancelled'"),{"t":t,"id":p.original_movement_id}).scalar_one()
            if p.quantity+prior>locked['quantity']:raise ValueError("material_return_quantity_exceeded")
            id=f"mrt_{uuid4().hex[:26]}"
            c.execute(text("""insert into inventory.material_returns(id,tenant_id,original_movement_id,source_type,source_id,source_code,reservation_id,quantity,reason,requested_by)
                values(:id,:t,:original,:type,:source,:code,:reservation,:q,:reason,:actor)"""),{"id":id,"t":t,"original":p.original_movement_id,"type":source["source_type"],"source":source["source_id"],"code":source_code,"reservation":source["reservation_id"],"q":p.quantity,"reason":p.reason,"actor":actor})
            value=self._material_return(c,t,id);self._done(c,t,"material_return.request",key,value)
            self._audit(c,t,actor,"material_return.request","material_return",id,p.model_dump(mode="json"));return value

    def receive_material_return(self,t,id,actor,folio=None):
        with self.engine.begin() as c:
            c.execute(text("select id from inventory.material_returns where tenant_id=:t and id=:id for update"),{"t":t,"id":id}).first()
            value=self._material_return(c,t,id)
            if not value:return None
            if value.status in {'received_pending_reconciliation','completed'}:return value
            if value.status!='pending':raise ValueError("material_return_not_receivable")
            warehouse=self._warehouse(c,t,value.warehouse_id)
            if not warehouse or warehouse.status!='active':raise ValueError("movement_reference_inactive")
            self._resource_lock(c,t,value.inventory_item_id,value.warehouse_id)
            context=value.organization_context
            cost=value.unit_cost
            if context and (not context.cost_currency or cost is None or not cost.is_finite() or cost<0):raise ValueError("operational_cost_currency_unavailable")
            movement=MovementCreate(movement_type="entry",inventory_item_id=value.inventory_item_id,warehouse_id=value.warehouse_id,
                quantity=value.quantity,unit=value.unit,unit_cost=cost if cost is not None else Decimal(0),reason=value.reason,
                source=SourceRef(type="material_return",id=id),occurred_at=datetime.now(timezone.utc))
            validate_local_context(c,t,movement,context)
            validate_cost_currency(c,t,value.inventory_item_id,value.warehouse_id,context)
            movement_id=f"mov_{uuid4().hex[:26]}"
            code=allocate_movement_code(folio,t,"material_return.receive",id,derived_manual_code("RET",t,id))
            self._insert_movement(c,t,movement_id,code,movement,"in",value.warehouse_id,actor,
                unit_cost=cost if cost is not None else Decimal(0),organization_context=context)
            c.execute(text("update inventory.material_returns set movement_id=:m,status='received_pending_reconciliation',received_by=:actor,received_at=now() where tenant_id=:t and id=:id"),{"t":t,"id":id,"m":movement_id,"actor":actor})
            self._audit(c,t,actor,"material_return.receive","material_return",id,{"movement_id":movement_id})
            return self._material_return(c,t,id)

    def finish_material_return(self,t,id,actor,error_code=None):
        with self.engine.begin() as c:
            c.execute(text("update inventory.material_returns set status=:status,error_code=:error where tenant_id=:t and id=:id and status='received_pending_reconciliation'"),{"status":"received_pending_reconciliation" if error_code else "completed","error":error_code,"t":t,"id":id})
            self._audit(c,t,actor,"material_return.reconcile","material_return",id,{"error_code":error_code})
            return self._material_return(c,t,id)

    def cancel_material_return(self,t,id,reason,actor):
        with self.engine.begin() as c:
            c.execute(text('select id from inventory.material_returns where tenant_id=:t and id=:id for update'),{'t':t,'id':id}).first()
            value=self._material_return(c,t,id)
            if not value:return None
            if value.status=='cancelled':return value
            if value.status!='pending':raise ValueError('material_return_not_cancellable')
            c.execute(text("update inventory.material_returns set status='cancelled' where tenant_id=:t and id=:id"),{'t':t,'id':id})
            self._audit(c,t,actor,'material_return.cancel','material_return',id,{'reason':reason})
            return self._material_return(c,t,id)
