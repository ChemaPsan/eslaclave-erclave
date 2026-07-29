import base64, binascii, json
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy import create_engine
from erclave_common.config import get_settings
from .schemas import WarehouseRead, ItemRead, MovementRead, BalanceRead, Page

class InventoryRepository:
    def __init__(self,engine): self.engine=engine
    def _claim(self,c,t,o,k,h):
        row=c.execute(text("select request_hash,response_payload from inventory.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k for update"),{"t":t,"o":o,"k":k}).mappings().first()
        if row:
            if row["request_hash"] != h: raise ValueError("idempotency_key_reused")
            return row["response_payload"]
        c.execute(text("insert into inventory.idempotency_records(id,tenant_id,operation,idempotency_key,request_hash) values(:id,:t,:o,:k,:h)"),{"id":f"ide_{uuid4().hex[:26]}","t":t,"o":o,"k":k,"h":h}); return None
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
    def list_items(self,t,q=None):
        params={"t":t}; where="tenant_id=:t"
        if q: where+=" and (code ilike :q or name ilike :q or category ilike :q)"; params["q"]=f"%{q}%"
        with self.engine.connect() as c: rows=c.execute(text(f"select id,code,name,type,category,base_unit,inventory_policy,suggested_warehouse_id,minimum_stock,maximum_stock,status,description from inventory.items where {where} order by code"),params).mappings()
        return [ItemRead.model_validate(dict(x)) for x in rows]
    def _item(self,c,t,i):
        row=c.execute(text("select id,code,name,type,category,base_unit,inventory_policy,suggested_warehouse_id,minimum_stock,maximum_stock,status,description from inventory.items where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first(); return ItemRead.model_validate(dict(row)) if row else None
    def get_item(self,t,i):
        with self.engine.connect() as c: return self._item(c,t,i)
    def create_item(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"item.create",k,h)
            if replay:return ItemRead.model_validate(replay)
            if p.suggested_warehouse_id and not self._warehouse(c,t,p.suggested_warehouse_id):self._release(c,t,"item.create",k);return None
            i=f"itm_{uuid4().hex[:26]}"; row=c.execute(text("insert into inventory.items(id,tenant_id,code,name,type,category,base_unit,inventory_policy,suggested_warehouse_id,minimum_stock,maximum_stock,description) values(:i,:t,lower(:code),:name,:type,:category,:base_unit,:inventory_policy,:suggested_warehouse_id,:minimum_stock,:maximum_stock,:description) on conflict(tenant_id,code) do nothing returning id"),{"i":i,"t":t,**p.model_dump()}).first()
            if not row:self._release(c,t,"item.create",k);return None
            value=self._item(c,t,i); self._audit(c,t,a,"item.create","item",i,p.model_dump()); self._done(c,t,"item.create",k,value); return value
    def update_item(self,t,i,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"item.update",k,h)
            if replay:return ItemRead.model_validate(replay)
            if not self._item(c,t,i):self._release(c,t,"item.update",k);return None
            data=p.model_dump(exclude_none=True)
            if "suggested_warehouse_id" in data and not self._warehouse(c,t,data["suggested_warehouse_id"]):
                self._release(c,t,"item.update",k); raise ValueError("suggested_warehouse_invalid")
            if data:
                sets=", ".join(f"{name}=:{name}" for name in data); c.execute(text(f"update inventory.items set {sets},updated_at=now() where tenant_id=:t and id=:i"),{"t":t,"i":i,**data})
            value=self._item(c,t,i); self._audit(c,t,a,"item.update","item",i,data); self._done(c,t,"item.update",k,value); return value
    def _balance(self,c,t,item,warehouse,unit):
        return float(c.execute(text("select coalesce(sum(case when direction='in' then quantity else -quantity end),0) from inventory.movements where tenant_id=:t and inventory_item_id=:item and warehouse_id=:wh and unit=:unit and status='recorded'"),{"t":t,"item":item,"wh":warehouse,"unit":unit}).scalar_one())
    def _movement(self,c,t,i):
        row=c.execute(text("select id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,status,occurred_at from inventory.movements where tenant_id=:t and id=:i"),{"t":t,"i":i}).mappings().first(); return MovementRead.model_validate(dict(row)) if row else None
    def create_movement(self,t,p,k,h,a):
        with self.engine.begin() as c:
            replay=self._claim(c,t,"movement.create",k,h)
            if replay:return MovementRead.model_validate(replay)
            if not self._item(c,t,p.inventory_item_id) or not self._warehouse(c,t,p.warehouse_id):self._release(c,t,"movement.create",k);return None
            if p.destination_warehouse_id and not self._warehouse(c,t,p.destination_warehouse_id):self._release(c,t,"movement.create",k);return None
            outgoing=p.movement_type in ("exit","negative_adjustment","transfer")
            if outgoing and self._balance(c,t,p.inventory_item_id,p.warehouse_id,p.unit) < p.quantity: raise ValueError("insufficient_stock")
            group=f"trf_{uuid4().hex[:26]}" if p.movement_type=="transfer" else None; i=f"mov_{uuid4().hex[:26]}"; code=f"MOV-{uuid4().hex[:10].upper()}"
            self._insert_movement(c,t,i,code,p,"out" if outgoing else "in",p.warehouse_id,a,group)
            if group:
                self._insert_movement(c,t,f"mov_{uuid4().hex[:26]}",f"{code}-IN",p,"in",p.destination_warehouse_id,a,group)
            value=self._movement(c,t,i); self._audit(c,t,a,"movement.create","movement",i,p.model_dump(mode="json")); self._done(c,t,"movement.create",k,value); return value
    def _insert_movement(self,c,t,i,code,p,direction,warehouse,a,group=None,reversal=None):
        c.execute(text("insert into inventory.movements(id,tenant_id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,actor_id,occurred_at) values(:i,:t,:code,:mt,:item,:wh,:direction,:qty,:unit,:cost,:reason,:st,:sid,:group,:reversal,:actor,:at)"),{"i":i,"t":t,"code":code,"mt":p.movement_type,"item":p.inventory_item_id,"wh":warehouse,"direction":direction,"qty":p.quantity,"unit":p.unit,"cost":p.unit_cost,"reason":p.reason,"st":p.source.type,"sid":p.source.id,"group":group,"reversal":reversal,"actor":a,"at":p.occurred_at})
    def list_movements(self,t,item=None,warehouse=None):
        filters=["tenant_id=:t"]; params={"t":t}
        if item:filters.append("inventory_item_id=:item");params["item"]=item
        if warehouse:filters.append("warehouse_id=:wh");params["wh"]=warehouse
        with self.engine.connect() as c: rows=c.execute(text("select id,movement_code,movement_type,inventory_item_id,warehouse_id,direction,quantity,unit,unit_cost,reason,source_type,source_id,transfer_group_id,reversal_of_id,status,occurred_at from inventory.movements where "+" and ".join(filters)+" order by occurred_at desc"),params).mappings()
        return [MovementRead.model_validate(dict(x)) for x in rows]
    def list_balances(self,t,**options):
        limit=options.get("limit",50); order=options.get("sort","item_code")
        order_columns={"item_code":"lower(item_code)","item_name":"lower(item_name)","on_hand_asc":"on_hand_quantity","on_hand_desc":"on_hand_quantity"}
        direction="desc" if order=="on_hand_desc" else "asc"; primary=order_columns[order]
        params={"t":t,"limit":limit+1}; filters=[]; base_filters=["m.tenant_id=:t","m.status='recorded'"]
        for option,column in (("inventory_item_id","m.inventory_item_id"),("warehouse_id","m.warehouse_id"),("category","i.category"),("item_type","i.type"),("item_status","i.status"),("inventory_policy","i.inventory_policy"),("unit","m.unit")):
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
        sql=f"""with balance_rows as (
          select m.inventory_item_id,i.code item_code,i.name item_name,i.type item_type,i.category,i.status item_status,i.inventory_policy,
                 m.warehouse_id,w.code warehouse_code,w.name warehouse_name,m.unit,
                 sum(case when m.direction='in' then m.quantity else -m.quantity end) on_hand_quantity,
                 i.minimum_stock,i.maximum_stock,max(m.occurred_at) last_movement_at
          from inventory.movements m
          join inventory.items i on i.tenant_id=m.tenant_id and i.id=m.inventory_item_id
          join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id
          where {" and ".join(base_filters)}
          group by m.inventory_item_id,i.code,i.name,i.type,i.category,i.status,i.inventory_policy,m.warehouse_id,w.code,w.name,m.unit,i.minimum_stock,i.maximum_stock
        ), enriched as (
          select *,0::numeric reserved_quantity,on_hand_quantity available_quantity,
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
            original=self._movement(c,t,i)
            if not original:self._release(c,t,"movement.reverse",k);return None
            if original.status!="recorded":raise ValueError("movement_already_reversed")
            originals=[original]
            if original.transfer_group_id:
                rows=c.execute(text("select id from inventory.movements where tenant_id=:t and transfer_group_id=:g and status='recorded' order by id for update"),{"t":t,"g":original.transfer_group_id}).scalars().all()
                originals=[self._movement(c,t,row_id) for row_id in rows]
            for entry in originals:
                if entry.direction=="in" and self._balance(c,t,entry.inventory_item_id,entry.warehouse_id,entry.unit)<entry.quantity:raise ValueError("insufficient_stock_for_reversal")
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
