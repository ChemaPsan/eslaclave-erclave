"""Inventory-owned handoffs: a dispatch is not a destination receipt."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import text
from .schemas import MovementCreate, SourceRef, TransferRead


class InventoryHandoffs:
    def _transfer(self,c,t,id,lock=False):
        if lock:
            c.execute(text("select id from inventory.transfers where tenant_id=:t and id=:id for update"),{"t":t,"id":id}).first()
        row=c.execute(text("""select tr.id,tr.status,tr.destination_warehouse_id,tr.received_quantity,tr.returned_quantity,
            m.id outgoing_movement_id,m.movement_code code,m.inventory_item_id,m.warehouse_id origin_warehouse_id,
            m.quantity,m.unit,m.unit_cost,i.code item_code,i.name item_name,w.name origin_name,d.name destination_name,tr.created_at
            from inventory.transfers tr join inventory.movements m on m.tenant_id=tr.tenant_id and m.id=tr.outgoing_movement_id
            join inventory.items i on i.tenant_id=m.tenant_id and i.id=m.inventory_item_id
            join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id
            join inventory.warehouses d on d.tenant_id=tr.tenant_id and d.id=tr.destination_warehouse_id
            where tr.tenant_id=:t and tr.id=:id"""),{"t":t,"id":id}).mappings().first()
        return TransferRead.model_validate(dict(row)) if row else None

    def list_transfers(self,t,limit=25,offset=0):
        with self.engine.connect() as c:
            ids=c.execute(text("select id from inventory.transfers where tenant_id=:t and status not in ('received','returned') order by created_at,id limit :limit offset :offset"),{"t":t,"limit":limit,"offset":offset}).scalars().all()
            return [self._transfer(c,t,id) for id in ids]

    def transition_transfer(self,t,id,action,p,key,digest,actor):
        operation=f"transfer.{action}"
        with self.engine.begin() as c:
            replay=self._claim(c,t,operation,key,digest)
            if replay:return TransferRead.model_validate(replay)
            transfer=self._transfer(c,t,id,True)
            if not transfer:self._release(c,t,operation,key);return None
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
                movement=MovementCreate(movement_type="entry",inventory_item_id=transfer.inventory_item_id,warehouse_id=target,
                    quantity=float(quantity),unit=transfer.unit,unit_cost=float(transfer.unit_cost or 0),reason=p.reason,
                    source=SourceRef(type="transfer",id=id),occurred_at=datetime.now(timezone.utc))
                self._insert_movement(c,t,f"mov_{uuid4().hex[:26]}",f"TR-IN-{uuid4().hex[:10].upper()}",movement,"in",target,actor,id)
                column="received_quantity" if action=="receive" else "returned_quantity"
                c.execute(text(f"update inventory.transfers set {column}={column}+:q where tenant_id=:t and id=:id"),{"q":quantity,"t":t,"id":id})
                status=("received" if action=="receive" else "returned") if quantity==remaining else ("partially_received" if action=="receive" else "return_requested")
            c.execute(text("update inventory.transfers set status=:status,updated_at=now() where tenant_id=:t and id=:id"),{"status":status,"t":t,"id":id})
            value=self._transfer(c,t,id)
            self._audit(c,t,actor,operation,"transfer",id,p.model_dump(mode="json"))
            self._done(c,t,operation,key,value)
            return value
