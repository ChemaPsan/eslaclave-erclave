"""Inventory-owned handoffs: a dispatch is not a destination receipt."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import text
from erclave_common.business_codes import derived_manual_code,allocate_movement_code
from .schemas import MovementCreate, SourceRef, TransferRead
from .reservation_context import validate_local_context, validate_cost_currency


class InventoryHandoffs:
    def _transfer(self,c,t,id,lock=False):
        if lock:
            c.execute(text("select id from inventory.transfers where tenant_id=:t and id=:id for update"),{"t":t,"id":id}).first()
        row=c.execute(text("""select tr.id,tr.status,tr.destination_warehouse_id,tr.received_quantity,tr.returned_quantity,
            m.id outgoing_movement_id,m.movement_code code,m.inventory_item_id,m.warehouse_id origin_warehouse_id,
            m.quantity,m.unit,m.unit_cost,m.organization_context,tr.destination_context,
            i.code item_code,i.name item_name,w.name origin_name,d.name destination_name,tr.created_at
            from inventory.transfers tr join inventory.movements m on m.tenant_id=tr.tenant_id and m.id=tr.outgoing_movement_id
            join inventory.items i on i.tenant_id=m.tenant_id and i.id=m.inventory_item_id
            join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id
            join inventory.warehouses d on d.tenant_id=tr.tenant_id and d.id=tr.destination_warehouse_id
            where tr.tenant_id=:t and tr.id=:id"""),{"t":t,"id":id}).mappings().first()
        return TransferRead.model_validate(dict(row)) if row else None

    def get_transfer(self,t,id):
        with self.engine.connect() as c:return self._transfer(c,t,id)

    def list_transfers(self,t,limit=25,offset=0,allowed_divisions=None):
        params={"t":t,"limit":limit,"offset":offset}
        scope=""
        if allowed_divisions is not None:
            scope=""" and coalesce(m.organization_context->>'division_ref_id',w.division_ref_id)=any(:divisions)
                and coalesce(tr.destination_context->>'division_ref_id',d.division_ref_id)=any(:divisions)"""
            params['divisions']=allowed_divisions
        with self.engine.connect() as c:
            ids=c.execute(text("""select tr.id from inventory.transfers tr
                join inventory.movements m on m.tenant_id=tr.tenant_id and m.id=tr.outgoing_movement_id
                join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id
                join inventory.warehouses d on d.tenant_id=tr.tenant_id and d.id=tr.destination_warehouse_id
                where tr.tenant_id=:t and tr.status not in ('received','returned')"""+scope+
                " order by tr.created_at,tr.id limit :limit offset :offset"),params).scalars().all()
            return [self._transfer(c,t,id) for id in ids]

    def transition_transfer(self,t,id,action,p,key,digest,actor,folio=None):
        operation=f"transfer.{action}"
        with self.engine.begin() as c:
            replay=self._claim(c,t,operation,key,digest,actor)
            if replay:return TransferRead.model_validate(replay)
            transfer=self._transfer(c,t,id,True)
            if not transfer:self._release(c,t,operation,key);return None
            origin_context=transfer.organization_context
            destination_context=transfer.destination_context
            if bool(origin_context)!=bool(destination_context):raise ValueError("operational_context_mismatch")
            if origin_context:
                if origin_context.society_ref_id!=destination_context.society_ref_id:raise ValueError("operational_context_mismatch")
                if not origin_context.cost_currency or origin_context.cost_currency!=destination_context.cost_currency:raise ValueError("operational_cost_currency_unavailable")
            remaining=transfer.quantity-transfer.received_quantity-transfer.returned_quantity
            if remaining<=0:raise ValueError("transfer_already_completed")
            target=transfer.origin_warehouse_id if action=="receive-return" else transfer.destination_warehouse_id
            if p.warehouse_id!=target:raise ValueError("transfer_receiving_warehouse_required")
            if action=="request-return":
                if transfer.status not in {"in_transit","partially_received"}:raise ValueError("transfer_return_already_requested")
                status="return_requested"
            else:
                if action=="receive" and transfer.status not in {"in_transit","partially_received"}:raise ValueError("transfer_return_in_progress")
                if action=="receive-return" and transfer.status!="return_requested":raise ValueError("transfer_return_request_required")
                quantity=p.quantity
                if quantity is None or quantity>remaining:raise ValueError("transfer_receipt_quantity_exceeded")
                warehouse=self._warehouse(c,t,target)
                if not warehouse or warehouse.status!="active":raise ValueError("movement_reference_inactive")
                self._resource_lock(c,t,transfer.inventory_item_id,target)
                context=origin_context if action=="receive-return" else destination_context
                cost=transfer.unit_cost
                if context and (cost is None or not cost.is_finite() or cost<0):raise ValueError("operational_cost_currency_unavailable")
                movement=MovementCreate(movement_type="entry",inventory_item_id=transfer.inventory_item_id,warehouse_id=target,
                    quantity=quantity,unit=transfer.unit,unit_cost=cost if cost is not None else Decimal(0),reason=p.reason,
                    source=SourceRef(type="transfer",id=id),occurred_at=datetime.now(timezone.utc))
                validate_local_context(c,t,movement,context)
                validate_cost_currency(c,t,transfer.inventory_item_id,target,context)
                code=allocate_movement_code(folio,t,operation,key,derived_manual_code("TRI",t,id,action,key))
                self._insert_movement(c,t,f"mov_{uuid4().hex[:26]}",code,movement,"in",target,actor,id,
                    unit_cost=cost if cost is not None else Decimal(0),organization_context=context)
                column="received_quantity" if action=="receive" else "returned_quantity"
                c.execute(text(f"update inventory.transfers set {column}={column}+:q where tenant_id=:t and id=:id"),{"q":quantity,"t":t,"id":id})
                status=("received" if action=="receive" else "returned") if quantity==remaining else ("partially_received" if action=="receive" else "return_requested")
            c.execute(text("update inventory.transfers set status=:status,updated_at=now() where tenant_id=:t and id=:id"),{"status":status,"t":t,"id":id})
            value=self._transfer(c,t,id)
            self._audit(c,t,actor,operation,"transfer",id,p.model_dump(mode="json"))
            self._done(c,t,operation,key,value)
            return value
