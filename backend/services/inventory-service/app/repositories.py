import base64, binascii, json
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy import create_engine
from erclave_common.config import get_settings
from .schemas import (
    AvailabilityAllocation, AvailabilityCheckRead, AvailabilityItemRead,
    BalanceRead, ItemRead, MovementRead, Page, ReservationRead, WarehouseRead,
    FinishedGoodsReceiptRead, FinishedGoodsReceiptSummaryRead, MovementCreate, SourceRef,
)

def reservation_consumption_state(reserved_quantity, consume_quantity):
    """Keep a positive reservation snapshot when the final balance is consumed."""
    reserved=float(reserved_quantity); remaining=reserved-float(consume_quantity)
    if remaining<=0:return reserved,"consumed",0.0
    return remaining,"active",remaining

class InventoryRepository:
    def __init__(self,engine): self.engine=engine
    def _claim(self,c,t,o,k,h):
        claimed=c.execute(text("""insert into inventory.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash)
            values(:id,:t,:o,:k,:h) on conflict(tenant_id,operation,idempotency_key) do nothing returning id"""),{"id":f"ide_{uuid4().hex[:26]}","t":t,"o":o,"k":k,"h":h}).first()
        if claimed:return None
        row=c.execute(text("select request_hash,response_payload from inventory.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k for update"),{"t":t,"o":o,"k":k}).mappings().one()
        if row["request_hash"] != h: raise ValueError("idempotency_key_reused")
        if row["response_payload"] is None:raise ValueError("idempotency_request_in_progress")
        return row["response_payload"]
    def _done(self,c,t,o,k,value): c.execute(text("update inventory.idempotency_records set response_payload=cast(:p as jsonb) where tenant_id=:t and operation=:o and idempotency_key=:k"),{"p":json.dumps(value.model_dump(mode="json")),"t":t,"o":o,"k":k})
    def _release(self,c,t,o,k): c.execute(text("delete from inventory.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k and response_payload is null"),{"t":t,"o":o,"k":k})
    def _audit(self,c,t,a,action,kind,eid,payload): c.execute(text("insert into inventory.audit_events(id,tenant_id,actor_id,action,entity_type,entity_id,payload) values(:id,:t,:a,:ac,:kind,:eid,cast(:p as jsonb))"),{"id":f"aud_{uuid4().hex[:26]}","t":t,"a":a,"ac":action,"kind":kind,"eid":eid,"p":json.dumps(payload)})
    def list_warehouses(self,t,q=None):
        params={"t":t}; where="tenant_id=:t"
        if q: where+=" and (code ilike :q or name ilike :q)"; params["q"]=f"%{q}%"
        with self.engine.connect() as c: rows=c.execute(text(f"select id,code,name,type,status,business_center,location,owner,capacity,inventory_policy,zone,aisle,rack,level,position,description from inventory.warehouses where {where} order by code"),params).mappings()
        return [WarehouseRead.model_validate(dict(x)) for x in rows]
    def _warehouse(self,c,t,i):
        row=c.execute(text("select id,code,name,type,status,business_center,location,owner,capacity,inventory_policy,zone,aisle,rack,level,position,description from inventory.warehouses where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first(); return WarehouseRead.model_validate(dict(row)) if row else None
    def create_warehouse(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"warehouse.create",k,h)
            if replay:return WarehouseRead.model_validate(replay)
            i=f"whs_{uuid4().hex[:26]}"; row=c.execute(text("insert into inventory.warehouses(id,tenant_id,code,name,type,business_center,location,owner,capacity,inventory_policy,zone,aisle,rack,level,position,description) values(:i,:t,lower(:code),:name,:type,:business_center,:location,:owner,:capacity,:inventory_policy,:zone,:aisle,:rack,:level,:position,:description) on conflict(tenant_id,code) do nothing returning id"),{"i":i,"t":t,**p.model_dump()}).first()
            if not row:self._release(c,t,"warehouse.create",k);return None
            value=self._warehouse(c,t,i); self._audit(c,t,a,"warehouse.create","warehouse",i,p.model_dump()); self._done(c,t,"warehouse.create",k,value); return value
    def update_warehouse(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"warehouse.update",k,h)
            if replay:return WarehouseRead.model_validate(replay)
            if not self._warehouse(c,t,i):self._release(c,t,"warehouse.update",k);return None
            data=p.model_dump(exclude_none=True)
            if data:
                sets=", ".join(f"{name}=:{name}" for name in data); c.execute(text(f"update inventory.warehouses set {sets},updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._warehouse(c,t,i); self._audit(c,t,a,"warehouse.update","warehouse",i,data); self._done(c,t,"warehouse.update",k,value); return value
    def list_items(self,t,q=None,use_in_recipe=None,status=None):
        params={"t":t}; where="tenant_id=:t"
        if q: where+=" and (code ilike :q or name ilike :q or category ilike :q)"; params["q"]=f"%{q}%"
        if use_in_recipe is not None: where+=" and use_in_recipe=:use_in_recipe"; params["use_in_recipe"]=use_in_recipe
        if status is not None: where+=" and status=:status"; params["status"]=status
        with self.engine.connect() as c: rows=c.execute(text(f"select id,code,name,type,category,base_unit,inventory_policy,suggested_warehouse_id,minimum_stock,maximum_stock,default_unit_cost,default_unit_cost default_unit_cost_per_base_unit,use_in_recipe,status,description from inventory.items where {where} order by code"),params).mappings()
        return [ItemRead.model_validate(dict(x)) for x in rows]
    def _item(self,c,t,i):
        row=c.execute(text("select id,code,name,type,category,base_unit,inventory_policy,suggested_warehouse_id,minimum_stock,maximum_stock,default_unit_cost,default_unit_cost default_unit_cost_per_base_unit,use_in_recipe,status,description from inventory.items where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first(); return ItemRead.model_validate(dict(row)) if row else None
    def get_item(self,t,i):
        with self.engine.connect() as c: return self._item(c,t,i)
    def create_item(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"item.create",k,h)
            if replay:return ItemRead.model_validate(replay)
            suggested=self._warehouse(c,t,p.suggested_warehouse_id) if p.suggested_warehouse_id else None
            if p.suggested_warehouse_id and (not suggested or suggested.status!="active"):self._release(c,t,"item.create",k);return None
            i=f"itm_{uuid4().hex[:26]}"; row=c.execute(text("insert into inventory.items(id,tenant_id,code,name,type,category,base_unit,inventory_policy,suggested_warehouse_id,minimum_stock,maximum_stock,default_unit_cost,use_in_recipe,description) values(:i,:t,lower(:code),:name,:type,:category,:base_unit,:inventory_policy,:suggested_warehouse_id,:minimum_stock,:maximum_stock,:default_unit_cost,:use_in_recipe,:description) on conflict(tenant_id,code) do nothing returning id"),{"i":i,"t":t,**p.model_dump()}).first()
            if not row:self._release(c,t,"item.create",k);return None
            value=self._item(c,t,i); self._audit(c,t,a,"item.create","item",i,p.model_dump()); self._done(c,t,"item.create",k,value); return value
    def update_item(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"item.update",k,h)
            if replay:return ItemRead.model_validate(replay)
            before=self._item(c,t,i)
            if not before:self._release(c,t,"item.update",k);return None
            data=p.model_dump(exclude_none=True)
            suggested=self._warehouse(c,t,data["suggested_warehouse_id"]) if "suggested_warehouse_id" in data else None
            if "suggested_warehouse_id" in data and (not suggested or suggested.status!="active"):
                self._release(c,t,"item.update",k); raise ValueError("suggested_warehouse_invalid")
            if "base_unit" in data and data["base_unit"] != before.base_unit:
                has_history=c.execute(text("""select 1 from inventory.movements where tenant_id=:t and inventory_item_id=:i
                    union all select 1 from inventory.reservations where tenant_id=:t and inventory_item_id=:i limit 1"""),{"t":t,"i":i}).first()
                if has_history:self._release(c,t,"item.update",k);raise ValueError("item_base_unit_locked_by_movements")
            minimum=float(data.get("minimum_stock",before.minimum_stock));maximum=data.get("maximum_stock",before.maximum_stock)
            if maximum is not None and float(maximum)<minimum:self._release(c,t,"item.update",k);raise ValueError("invalid_stock_limits")
            if data:
                sets=", ".join(f"{name}=:{name}" for name in data); c.execute(text(f"update inventory.items set {sets},updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._item(c,t,i); self._audit(c,t,a,"item.update","item",i,data); self._done(c,t,"item.update",k,value); return value
    def _balance(self,c,t,item,warehouse,unit):
        return float(c.execute(text("select coalesce(sum(case when direction='in' then quantity else -quantity end),0) from inventory.movements where tenant_id=:t and inventory_item_id=:item and warehouse_id=:wh and unit=:unit and status='recorded'"),{"t":t,"item":item,"wh":warehouse,"unit":unit}).scalar_one())
    def _resource_lock(self,c,t,item,warehouse):
        c.execute(text("select pg_advisory_xact_lock(hashtextextended(:lock_key,0))"),{"lock_key":f"inventory:{t}:{item}:{warehouse}"})
    def _reserved(self,c,t,item,warehouse,unit):
        return float(c.execute(text("select coalesce(sum(quantity),0) from inventory.reservations where tenant_id=:t and inventory_item_id=:item and warehouse_id=:wh and unit=:unit and status='active' and (expires_at is null or expires_at>now())"),{"t":t,"item":item,"wh":warehouse,"unit":unit}).scalar_one())
    def _average_cost(self,c,t,item,warehouse,unit,default_cost=0):
        row=c.execute(text("""select coalesce(sum(case when direction='in' then quantity else -quantity end),0) quantity,
            coalesce(sum(case when direction='in' then quantity*coalesce(unit_cost,0) else -quantity*coalesce(unit_cost,0) end),0) value
            from inventory.movements where tenant_id=:t and inventory_item_id=:item and warehouse_id=:wh and unit=:unit and status='recorded'"""),{"t":t,"item":item,"wh":warehouse,"unit":unit}).mappings().one()
        quantity=float(row["quantity"]);value=float(row["value"])
        return max(0,value/quantity) if quantity>0 else float(default_cost or 0)
    def _movement(self,c,t,i):
        row=c.execute(text("select id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,status,occurred_at from inventory.movements where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first(); return MovementRead.model_validate(dict(row)) if row else None
    def create_movement(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"movement.create",k,h)
            if replay:return MovementRead.model_validate(replay)
            item=self._item(c,t,p.inventory_item_id)
            warehouse=self._warehouse(c,t,p.warehouse_id)
            if not item or not warehouse:self._release(c,t,"movement.create",k);return None
            if item.status!="active" or warehouse.status!="active":self._release(c,t,"movement.create",k);raise ValueError("movement_reference_inactive")
            if item.base_unit != p.unit:self._release(c,t,"movement.create",k);raise ValueError("movement_unit_must_match_item_base_unit")
            destination=self._warehouse(c,t,p.destination_warehouse_id) if p.destination_warehouse_id else None
            if p.destination_warehouse_id and not destination:self._release(c,t,"movement.create",k);return None
            if destination and destination.status!="active":self._release(c,t,"movement.create",k);raise ValueError("movement_reference_inactive")
            outgoing=p.movement_type in ("exit","negative_adjustment","transfer")
            lock_warehouses=sorted({p.warehouse_id,*([p.destination_warehouse_id] if p.destination_warehouse_id else [])})
            for warehouse_id in lock_warehouses:self._resource_lock(c,t,p.inventory_item_id,warehouse_id)
            available=self._balance(c,t,p.inventory_item_id,p.warehouse_id,p.unit)-self._reserved(c,t,p.inventory_item_id,p.warehouse_id,p.unit)
            if outgoing and available < p.quantity: self._release(c,t,"movement.create",k);raise ValueError("insufficient_available_stock")
            unit_cost=float(p.unit_cost) if p.unit_cost is not None else (self._average_cost(c,t,p.inventory_item_id,p.warehouse_id,p.unit,item.default_unit_cost) if outgoing else float(item.default_unit_cost))
            group=f"trf_{uuid4().hex[:26]}" if p.movement_type=="transfer" else None; i=f"mov_{uuid4().hex[:26]}"; code=f"MOV-{uuid4().hex[:10].upper()}"
            self._insert_movement(c,t,i,code,p,"out" if outgoing else "in",p.warehouse_id,a,group,unit_cost=unit_cost)
            if group:
                self._insert_movement(c,t,f"mov_{uuid4().hex[:26]}",f"{code}-IN",p,"in",p.destination_warehouse_id,a,group,unit_cost=unit_cost)
            value=self._movement(c,t,i); self._audit(c,t,a,"movement.create","movement",i,p.model_dump(mode="json")); self._done(c,t,"movement.create",k,value); return value
    def _insert_movement(self,c,t,i,code,p,direction,warehouse,a,group=None,reversal=None,unit_cost=None):
        c.execute(text("insert into inventory.movements(id,tenant_id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,actor_id,occurred_at) values(:i,:t,:code,:mt,:item,:wh,:direction,:qty,:unit,:cost,:reason,:st,:sid,:group,:reversal,:actor,:at)"),{"i":i,"t":t,"code":code,"mt":p.movement_type,"item":p.inventory_item_id,"wh":warehouse,"direction":direction,"qty":p.quantity,"unit":p.unit,"cost":unit_cost if unit_cost is not None else p.unit_cost,"reason":p.reason,"st":p.source.type,"sid":p.source.id,"group":group,"reversal":reversal,"actor":a,"at":p.occurred_at})
    def list_movements(self,t,item=None,warehouse=None):
        filters=["tenant_id=:t"]; params={"t":t}
        if item:filters.append("inventory_item_id=:item");params["item"]=item
        if warehouse:filters.append("warehouse_id=:wh");params["wh"]=warehouse
        with self.engine.connect() as c: rows=c.execute(text("select id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,status,occurred_at from inventory.movements where "+" and ".join(filters)+" order by occurred_at desc"),params).mappings()
        return [MovementRead.model_validate(dict(x)) for x in rows]
    def list_finished_goods_receipts(self,t):
        with self.engine.connect() as c:
            rows=c.execute(text("""select source_id production_order_id,coalesce(sum(quantity),0) received_quantity,max(occurred_at) last_received_at
                from inventory.movements where tenant_id=:t and source_type='production_order_receipt' and direction='in' and status='recorded'
                group by source_id order by max(occurred_at) desc"""),{"t":t}).mappings()
        return [FinishedGoodsReceiptSummaryRead.model_validate(dict(row)) for row in rows]
    def create_finished_goods_receipt(self,t,p,order,product,k,h,a):
        operation="finished_goods_receipt.create"
        with self.engine.begin() as c:
            replay=self._claim(c,t,operation,k,h)
            if replay:return FinishedGoodsReceiptRead.model_validate(replay)
            c.execute(text("select pg_advisory_xact_lock(hashtextextended(:lock_key,0))"),{"lock_key":f"finished-goods-receipt:{t}:{order['id']}"})
            item=self._item(c,t,product["inventory_item_id"]);warehouse=self._warehouse(c,t,p.warehouse_id)
            if not item or not warehouse:self._release(c,t,operation,k);return None
            if item.status!="active" or item.type!="finishedGood" or warehouse.status!="active":self._release(c,t,operation,k);raise ValueError("finished_goods_receipt_reference_invalid")
            if item.base_unit!=order["unit"] or item.base_unit!=product["base_unit"]:self._release(c,t,operation,k);raise ValueError("finished_goods_receipt_unit_mismatch")
            received=float(c.execute(text("""select coalesce(sum(quantity),0) from inventory.movements
                where tenant_id=:t and source_type='production_order_receipt' and source_id=:order_id and direction='in' and status='recorded'"""),{"t":t,"order_id":order["id"]}).scalar_one())
            ordered=float(order["quantity"]);quantity=float(p.quantity)
            if received+quantity>ordered+0.000001:self._release(c,t,operation,k);raise ValueError("finished_goods_receipt_quantity_exceeded")
            total_cost=order.get("actual_cost") if order.get("actual_cost") is not None else order.get("planned_cost")
            unit_cost=float(total_cost or 0)/ordered if ordered else float(item.default_unit_cost)
            movement_payload=MovementCreate(movement_type="entry",inventory_item_id=item.id,warehouse_id=p.warehouse_id,quantity=quantity,unit=item.base_unit,unit_cost=unit_cost,reason=p.notes or f"Recepción de orden {order['code']}",source=SourceRef(type="production_order_receipt",id=order["id"]),occurred_at=p.received_at)
            movement_id=f"mov_{uuid4().hex[:26]}"; movement_code=f"MOV-{uuid4().hex[:10].upper()}"
            self._resource_lock(c,t,item.id,p.warehouse_id)
            self._insert_movement(c,t,movement_id,movement_code,movement_payload,"in",p.warehouse_id,a,unit_cost=unit_cost)
            movement=self._movement(c,t,movement_id);cumulative=received+quantity
            value=FinishedGoodsReceiptRead(production_order_id=order["id"],production_order_code=order["code"],product_service_id=product["id"],product_service_code=product["code"],product_service_name=product["name"],inventory_item_id=item.id,inventory_item_code=item.code,inventory_item_name=item.name,warehouse_id=p.warehouse_id,unit=item.base_unit,ordered_quantity=ordered,received_quantity=quantity,cumulative_received_quantity=cumulative,remaining_quantity=max(0,ordered-cumulative),movement=movement)
            self._audit(c,t,a,"finished_goods_receipt.create","production_order",order["id"],{"movement_id":movement.id,"quantity":quantity,"warehouse_id":p.warehouse_id})
            self._done(c,t,operation,k,value);return value
    def _availability_rows(self,c,t,item,unit):
        return c.execute(text("""with movement_totals as (
            select warehouse_id,
                coalesce(sum(case when direction='in' then quantity else -quantity end),0) on_hand,
                coalesce(sum(case when direction='in' then quantity*coalesce(unit_cost,0) else -quantity*coalesce(unit_cost,0) end),0) inventory_value
            from inventory.movements
            where tenant_id=:t and inventory_item_id=:item and unit=:unit and status='recorded'
            group by warehouse_id
        ), reservation_totals as (
            select warehouse_id,coalesce(sum(quantity),0) reserved
            from inventory.reservations
            where tenant_id=:t and inventory_item_id=:item and unit=:unit and status='active' and (expires_at is null or expires_at>now())
            group by warehouse_id
        ), locations as (
            select warehouse_id from movement_totals union select warehouse_id from reservation_totals
            union select suggested_warehouse_id from inventory.items where tenant_id=:t and id=:item and suggested_warehouse_id is not null
        )
        select l.warehouse_id,w.name warehouse_name,coalesce(m.on_hand,0) on_hand,coalesce(r.reserved,0) reserved,
            greatest(coalesce(m.on_hand,0)-coalesce(r.reserved,0),0) available,
            case when coalesce(m.on_hand,0)>0 then greatest(m.inventory_value/m.on_hand,0) else i.default_unit_cost end unit_cost
        from locations l join inventory.warehouses w on w.tenant_id=:t and w.id=l.warehouse_id
        join inventory.items i on i.tenant_id=:t and i.id=:item
        left join movement_totals m on m.warehouse_id=l.warehouse_id left join reservation_totals r on r.warehouse_id=l.warehouse_id
        where w.status='active' order by available desc,l.warehouse_id"""),{"t":t,"item":item,"unit":unit}).mappings().all()
    def check_availability(self,t,p):
        result=[]
        with self.engine.connect() as c:
            for requested in p.items:
                item=self._item(c,t,requested.inventory_item_id)
                if not item or item.status!="active" or not item.use_in_recipe or item.base_unit!=requested.unit:
                    result.append(AvailabilityItemRead(inventory_item_id=requested.inventory_item_id,item_code=item.code if item else requested.inventory_item_id,item_name=item.name if item else requested.inventory_item_id,unit=requested.unit,required_quantity=requested.quantity,on_hand_quantity=0,reserved_quantity=0,available_quantity=0,unit_cost=float(item.default_unit_cost) if item else 0,total_cost=0,ok=False,blocker_code="inventory_resource_invalid",allocations=[]));continue
                rows=self._availability_rows(c,t,item.id,requested.unit);remaining=float(requested.quantity);allocations=[]
                for row in rows:
                    take=min(remaining,float(row["available"]))
                    if take>0:allocations.append(AvailabilityAllocation(warehouse_id=row["warehouse_id"],warehouse_name=row["warehouse_name"],quantity=take,unit_cost=float(row["unit_cost"])))
                    remaining-=take
                    if remaining<=0:break
                on_hand=sum(float(row["on_hand"]) for row in rows);reserved=sum(float(row["reserved"]) for row in rows);available=sum(float(row["available"]) for row in rows)
                allocated=sum(x.quantity for x in allocations);cost=sum(x.quantity*x.unit_cost for x in allocations);fallback=float(item.default_unit_cost)
                if allocated<requested.quantity:cost+=(float(requested.quantity)-allocated)*fallback
                unit_cost=cost/float(requested.quantity)
                ok=remaining<=0
                result.append(AvailabilityItemRead(inventory_item_id=item.id,item_code=item.code,item_name=item.name,unit=item.base_unit,required_quantity=requested.quantity,on_hand_quantity=on_hand,reserved_quantity=reserved,available_quantity=available,unit_cost=unit_cost,total_cost=cost,ok=ok,blocker_code=None if ok else "insufficient_material",allocations=allocations))
        return AvailabilityCheckRead(source=p.source,available=all(item.ok for item in result),items=result)
    def _reservation(self,c,t,i):
        row=c.execute(text("""select id,inventory_item_id,warehouse_id,quantity,unit,unit_cost_snapshot,source_type,source_id,source_line_id,
            case when status='active' and expires_at is not null and expires_at<=now() then 'expired' else status end status,expires_at,created_at
            from inventory.reservations where tenant_id=:t and id=:i"""),{"t":t,"i":i}).mappings().first()
        return ReservationRead.model_validate(dict(row)) if row else None
    def create_reservation(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"reservation.create",k,h)
            if replay:
                replay_value=ReservationRead.model_validate(replay);current=self._reservation(c,t,replay_value.id)
                if current and current.status=="active":return current
                if not current or current.status=="consumed":raise ValueError("reservation_source_conflict")
            item=self._item(c,t,p.inventory_item_id);warehouse=self._warehouse(c,t,p.warehouse_id)
            production_source=p.source.type=="production_order"
            if not item or not warehouse or item.status!="active" or warehouse.status!="active" or (production_source and not item.use_in_recipe):self._release(c,t,"reservation.create",k);raise ValueError("reservation_reference_invalid")
            if item.base_unit!=p.unit:self._release(c,t,"reservation.create",k);raise ValueError("reservation_unit_mismatch")
            self._resource_lock(c,t,item.id,warehouse.id)
            available=self._balance(c,t,item.id,warehouse.id,p.unit)-self._reserved(c,t,item.id,warehouse.id,p.unit)
            if available<float(p.quantity):self._release(c,t,"reservation.create",k);raise ValueError("insufficient_available_stock")
            unit_cost=self._average_cost(c,t,item.id,warehouse.id,p.unit,item.default_unit_cost);i=f"rsv_{uuid4().hex[:26]}"
            if replay:
                c.execute(text("""update inventory.reservations set status='active',quantity=:quantity,unit_cost_snapshot=:cost,
                    expires_at=coalesce(:expires_at,now()+interval '24 hours'),updated_at=now() where tenant_id=:t and id=:i"""),{"quantity":p.quantity,"cost":unit_cost,"expires_at":p.expires_at,"t":t,"i":replay_value.id})
                value=self._reservation(c,t,replay_value.id);self._audit(c,t,a,"reservation.reactivate","reservation",value.id,p.model_dump(mode="json"));self._done(c,t,"reservation.create",k,value);return value
            row=c.execute(text("""insert into inventory.reservations(id,tenant_id,inventory_item_id,warehouse_id,quantity,unit,unit_cost_snapshot,source_type,source_id,source_line_id,status,expires_at,created_by)
                values(:i,:t,:item,:wh,:quantity,:unit,:cost,:source_type,:source_id,:line_id,'active',coalesce(:expires_at,now()+interval '24 hours'),:actor)
                on conflict(tenant_id,source_type,source_id,source_line_id,inventory_item_id,warehouse_id,unit) do nothing returning id"""),{"i":i,"t":t,"item":item.id,"wh":warehouse.id,"quantity":p.quantity,"unit":p.unit,"cost":unit_cost,"source_type":p.source.type,"source_id":p.source.id,"line_id":p.source.line_id or item.id,"expires_at":p.expires_at,"actor":a}).first()
            if not row:
                existing=c.execute(text("""select id,quantity,status from inventory.reservations where tenant_id=:t and source_type=:source_type and source_id=:source_id
                    and source_line_id=:line_id and inventory_item_id=:item and warehouse_id=:wh and unit=:unit for update"""),{"t":t,"source_type":p.source.type,"source_id":p.source.id,"line_id":p.source.line_id or item.id,"item":item.id,"wh":warehouse.id,"unit":p.unit}).mappings().one()
                if float(existing["quantity"])!=float(p.quantity) or existing["status"]=="consumed":self._release(c,t,"reservation.create",k);raise ValueError("reservation_source_conflict")
                if existing["status"]!="active":c.execute(text("update inventory.reservations set status='active',unit_cost_snapshot=:cost,expires_at=coalesce(:expires_at,now()+interval '24 hours'),updated_at=now() where tenant_id=:t and id=:i"),{"cost":unit_cost,"expires_at":p.expires_at,"t":t,"i":existing["id"]})
                value=self._reservation(c,t,existing["id"])
            else:value=self._reservation(c,t,i)
            self._audit(c,t,a,"reservation.create","reservation",value.id,p.model_dump(mode="json"));self._done(c,t,"reservation.create",k,value);return value
    def release_reservation(self,t,i,reason,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"reservation.release",k,h)
            if replay:return ReservationRead.model_validate(replay)
            c.execute(text("select id from inventory.reservations where tenant_id=:t and id=:i for update"),{"t":t,"i":i}).first()
            before=self._reservation(c,t,i)
            if not before:self._release(c,t,"reservation.release",k);return None
            if before.status=="active":c.execute(text("update inventory.reservations set status='released',updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i})
            value=self._reservation(c,t,i);self._audit(c,t,a,"reservation.release","reservation",i,{"reason":reason,"before":before.status,"after":value.status});self._done(c,t,"reservation.release",k,value);return value
    def consume_reservation(self,t,i,reason,k,h,a,quantity=None):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"reservation.consume",k,h)
            if replay:return MovementRead.model_validate(replay)
            c.execute(text("select id from inventory.reservations where tenant_id=:t and id=:i for update"),{"t":t,"i":i}).first()
            reservation=self._reservation(c,t,i)
            if not reservation:self._release(c,t,"reservation.consume",k);return None
            if reservation.status=="consumed":
                movement=c.execute(text("select id from inventory.movements where tenant_id=:t and source_type='reservation' and source_id=:i order by created_at limit 1"),{"t":t,"i":i}).scalar_one_or_none()
                if movement:
                    value=self._movement(c,t,movement);self._done(c,t,"reservation.consume",k,value);return value
            if reservation.status!="active":self._release(c,t,"reservation.consume",k);raise ValueError("reservation_not_active")
            consume_quantity=float(quantity) if quantity is not None else float(reservation.quantity)
            if consume_quantity>float(reservation.quantity):self._release(c,t,"reservation.consume",k);raise ValueError("reservation_quantity_exceeded")
            self._resource_lock(c,t,reservation.inventory_item_id,reservation.warehouse_id)
            if self._balance(c,t,reservation.inventory_item_id,reservation.warehouse_id,reservation.unit)<consume_quantity:self._release(c,t,"reservation.consume",k);raise ValueError("reserved_stock_missing")
            movement_id=f"mov_{uuid4().hex[:26]}";code=f"MOV-{uuid4().hex[:10].upper()}"
            c.execute(text("""insert into inventory.movements(id,tenant_id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,actor_id,occurred_at)
                values(:id,:t,:code,'exit',:item,:wh,'out',:quantity,:unit,:cost,:reason,'reservation',:source,:actor,now())"""),{"id":movement_id,"t":t,"code":code,"item":reservation.inventory_item_id,"wh":reservation.warehouse_id,"quantity":consume_quantity,"unit":reservation.unit,"cost":reservation.unit_cost_snapshot,"reason":reason,"source":reservation.id,"actor":a})
            stored_quantity,next_status,remaining=reservation_consumption_state(reservation.quantity,consume_quantity)
            c.execute(text("update inventory.reservations set quantity=:quantity,status=:status,updated_at=now() where tenant_id=:t and id=:i"),{"quantity":stored_quantity,"status":next_status,"t":t,"i":i});value=self._movement(c,t,movement_id)
            self._audit(c,t,a,"reservation.consume","reservation",i,{"movement_id":movement_id,"reason":reason,"quantity":consume_quantity,"remaining_quantity":remaining});self._done(c,t,"reservation.consume",k,value);return value
    def list_balances(self,t,**options):
        limit=options.get("limit",50); order=options.get("sort","item_code")
        order_columns={"item_code":"lower(item_code)","item_name":"lower(item_name)","on_hand_asc":"on_hand_quantity","on_hand_desc":"on_hand_quantity"}
        direction="desc" if order=="on_hand_desc" else "asc"; primary=order_columns[order]
        params={"t":t,"limit":limit+1}; filters=[]; base_filters=["c.tenant_id=:t"]
        for option,column in (("inventory_item_id","c.inventory_item_id"),("warehouse_id","c.warehouse_id"),("category","i.category"),("item_type","i.type"),("item_status","i.status"),("inventory_policy","i.inventory_policy"),("unit","c.unit")):
            value=options.get(option)
            if value is not None: base_filters.append(f"{column}=:{option}"); params[option]=value
        if options.get("stock_status") is not None:
            filters.append("stock_status=:stock_status"); params["stock_status"]=options["stock_status"]
        if options.get("q"):
            base_filters.append("(inventory.search_normalize(i.code||' '||i.name||' '||coalesce(i.category,'')) like '%'||inventory.search_normalize(:q)||'%' or inventory.search_normalize(w.code||' '||w.name) like '%'||inventory.search_normalize(:q)||'%')"); params["q"]=options["q"]
        cursor=options.get("cursor")
        if cursor:
            try:
                marker=json.loads(base64.urlsafe_b64decode(cursor.encode()+b"="*(-len(cursor)%4)))
                if marker.get("order")!=order: raise ValueError
                params.update({"cv":marker["value"],"ci":marker["item_id"],"cw":marker["warehouse_id"],"cu":marker["unit"]})
            except (KeyError,TypeError,ValueError,UnicodeError,binascii.Error,json.JSONDecodeError) as exc: raise ValueError("invalid_cursor") from exc
            comparator="<" if direction=="desc" else ">"
            filters.append(f"({primary},inventory_item_id,warehouse_id,unit) {comparator} (:cv,:ci,:cw,:cu)")
        where=(" where "+" and ".join(filters)) if filters else ""
        sql=f"""with item_locations as (
          select tenant_id,inventory_item_id,warehouse_id,unit
          from inventory.movements where tenant_id=:t and status='recorded'
          union
          select tenant_id,inventory_item_id,warehouse_id,unit
          from inventory.reservations where tenant_id=:t and status='active' and (expires_at is null or expires_at>now())
          union
          select tenant_id,id,suggested_warehouse_id,base_unit
          from inventory.items where tenant_id=:t and suggested_warehouse_id is not null
        ), reservation_rows as (
          select tenant_id,inventory_item_id,warehouse_id,unit,sum(quantity) reserved_quantity
          from inventory.reservations where tenant_id=:t and status='active' and (expires_at is null or expires_at>now())
          group by tenant_id,inventory_item_id,warehouse_id,unit
        ), balance_rows as (
          select c.inventory_item_id,i.code item_code,i.name item_name,i.type item_type,i.category,i.status item_status,i.inventory_policy,
                 c.warehouse_id,w.code warehouse_code,w.name warehouse_name,c.unit,
                 coalesce(sum(case when m.direction='in' then m.quantity when m.direction='out' then -m.quantity else 0 end),0) on_hand_quantity,
                 coalesce(sum(case when m.direction='in' then m.quantity*coalesce(m.unit_cost,0) when m.direction='out' then -m.quantity*coalesce(m.unit_cost,0) else 0 end),0) inventory_value,
                 coalesce(r.reserved_quantity,0) reserved_quantity,i.default_unit_cost,
                 i.minimum_stock,i.maximum_stock,max(m.occurred_at) last_movement_at
          from item_locations c
          join inventory.items i on i.tenant_id=c.tenant_id and i.id=c.inventory_item_id
          join inventory.warehouses w on w.tenant_id=c.tenant_id and w.id=c.warehouse_id
          left join inventory.movements m on m.tenant_id=c.tenant_id and m.inventory_item_id=c.inventory_item_id and m.warehouse_id=c.warehouse_id and m.unit=c.unit and m.status='recorded'
          left join reservation_rows r on r.tenant_id=c.tenant_id and r.inventory_item_id=c.inventory_item_id and r.warehouse_id=c.warehouse_id and r.unit=c.unit
          where {" and ".join(base_filters)}
          group by c.inventory_item_id,i.code,i.name,i.type,i.category,i.status,i.inventory_policy,c.warehouse_id,w.code,w.name,c.unit,r.reserved_quantity,i.default_unit_cost,i.minimum_stock,i.maximum_stock
        ), enriched as (
          select *,greatest(on_hand_quantity-reserved_quantity,0) available_quantity,
            case when on_hand_quantity>0 then greatest(inventory_value/on_hand_quantity,0) else default_unit_cost end average_unit_cost,
            case when on_hand_quantity<0 then 'negative' when on_hand_quantity=0 then 'out_of_stock'
                 when on_hand_quantity<minimum_stock then 'below_minimum'
                 when maximum_stock is not null and on_hand_quantity>maximum_stock then 'above_maximum' else 'normal' end stock_status
          from balance_rows
        ) select * from enriched{where} order by {primary} {direction},inventory_item_id {direction},warehouse_id {direction},unit {direction} limit :limit"""
        with self.engine.connect() as c: rows=[dict(x) for x in c.execute(text(sql),params).mappings()]
        has_more=len(rows)>limit; rows=rows[:limit]; next_cursor=None
        if has_more:
            last=rows[-1]; value=float(last["on_hand_quantity"]) if order.startswith("on_hand") else last["item_code" if order=="item_code" else "item_name"].lower()
            payload={"order":order,"value":value,"item_id":last["inventory_item_id"],"warehouse_id":last["warehouse_id"],"unit":last["unit"]}
            next_cursor=base64.urlsafe_b64encode(json.dumps(payload,separators=(",",":"),sort_keys=True).encode()).decode().rstrip("=")
        return [BalanceRead.model_validate(x) for x in rows],Page(limit=limit,next_cursor=next_cursor,has_more=has_more)
    def reverse_movement(self,t,i,reason,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"movement.reverse",k,h)
            if replay:return MovementRead.model_validate(replay)
            c.execute(text("select id from inventory.movements where tenant_id=:t and id=:i for update"),{"t":t,"i":i}).first()
            original=self._movement(c,t,i)
            if not original:self._release(c,t,"movement.reverse",k);return None
            if original.status!="recorded":raise ValueError("movement_already_reversed")
            originals=[original]
            if original.transfer_group_id:
                rows=c.execute(text("select id from inventory.movements where tenant_id=:t and transfer_group_id=:g and status='recorded' order by id for update"),{"t":t,"g":original.transfer_group_id}).scalars().all()
                originals=[self._movement(c,t,row_id) for row_id in rows]
            for entry in sorted(originals,key=lambda x:(x.inventory_item_id,x.warehouse_id)):
                self._resource_lock(c,t,entry.inventory_item_id,entry.warehouse_id)
            for entry in originals:
                if entry.direction=="in" and self._balance(c,t,entry.inventory_item_id,entry.warehouse_id,entry.unit)-self._reserved(c,t,entry.inventory_item_id,entry.warehouse_id,entry.unit)<entry.quantity:raise ValueError("insufficient_available_stock_for_reversal")
            first_reversal=None
            for entry in originals:
                rid=f"mov_{uuid4().hex[:26]}"; code=f"REV-{uuid4().hex[:10].upper()}"
                c.execute(text("insert into inventory.movements(id,tenant_id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,actor_id,occurred_at) values(:id,:t,:code,'reversal',:item,:wh,:direction,:qty,:unit,:cost,:reason,'movement',:source,:group,:source,:actor,now())"),{"id":rid,"t":t,"code":code,"item":entry.inventory_item_id,"wh":entry.warehouse_id,"direction":"out" if entry.direction=="in" else "in","qty":entry.quantity,"unit":entry.unit,"cost":entry.unit_cost,"reason":reason,"source":entry.id,"group":entry.transfer_group_id,"actor":a})
                c.execute(text("update inventory.movements set status='reversed' where tenant_id=:t and id=:i"),{"t":t,"i":entry.id})
                first_reversal=first_reversal or rid
            value=self._movement(c,t,first_reversal); self._audit(c,t,a,"movement.reverse","movement",i,{"reversal_id":first_reversal,"reason":reason,"reversed_count":len(originals)}); self._done(c,t,"movement.reverse",k,value); return value

_repository = None
def get_inventory_repository():
    global _repository
    if _repository is None:
        settings = get_settings()
        database_url = settings.inventory_database_url or settings.database_url
        if not database_url: raise RuntimeError("ERCLAVE_INVENTORY_DATABASE_URL or ERCLAVE_DATABASE_URL is required.")
        _repository = InventoryRepository(create_engine(database_url, pool_pre_ping=True))
    return _repository
