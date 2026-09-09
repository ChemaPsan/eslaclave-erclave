from __future__ import annotations

from datetime import date

from sqlalchemy import text

from erclave_common.csv_reports import REPORT_MAX_ROWS, ReportColumn, ReportResult
from erclave_common.errors import ErclaveError

C = ReportColumn
REPORT_PERMISSIONS = {
    "warehouses": "inventory.warehouse.read",
    "items": "inventory.item.read",
    "balances": "inventory.balance.read",
    "kardex": "inventory.kardex.read",
    "critical-reservations": "inventory.balance.read",
}


def _query(repository, sql, params):
    bounded_params={**params,"_report_limit":REPORT_MAX_ROWS+1}
    with repository.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(f"select * from ({sql}) report_rows limit :_report_limit"), bounded_params).mappings()]


def _clauses(filters, mapping, params, alias="x"):
    clauses = [f"{alias}.tenant_id=:tenant_id"]
    for key, expression in mapping.items():
        if filters.get(key) not in (None, ""):
            clauses.append(expression)
            params[key] = filters[key]
    return clauses


def _balance_sql(extra_where=""):
    return f"""with locations as (
      select tenant_id,inventory_item_id,warehouse_id,unit from inventory.movements where tenant_id=:tenant_id and status in ('recorded','reversed')
      union select tenant_id,inventory_item_id,warehouse_id,unit from inventory.reservations where tenant_id=:tenant_id and status='active' and (expires_at is null or expires_at>now())
      union select tenant_id,id,suggested_warehouse_id,base_unit from inventory.items where tenant_id=:tenant_id and suggested_warehouse_id is not null
    ), reserved as (
      select tenant_id,inventory_item_id,warehouse_id,unit,sum(quantity) reserved_quantity
      from inventory.reservations where tenant_id=:tenant_id and status='active' and (expires_at is null or expires_at>now())
      group by tenant_id,inventory_item_id,warehouse_id,unit
    ), balances as (
      select l.tenant_id,l.inventory_item_id,i.code item_code,i.name item_name,i.type item_type,i.category,i.status item_status,
        l.warehouse_id,w.code warehouse_code,w.name warehouse_name,l.unit,
        coalesce(sum(case when m.direction='in' then m.quantity when m.direction='out' then -m.quantity else 0 end),0) on_hand_quantity,
        coalesce(sum(case when m.direction='in' then m.quantity*coalesce(m.unit_cost,0) when m.direction='out' then -m.quantity*coalesce(m.unit_cost,0) else 0 end),0) inventory_value,
        coalesce(r.reserved_quantity,0) reserved_quantity,i.minimum_stock,i.maximum_stock,max(m.occurred_at) last_movement_at
      from locations l join inventory.items i on i.tenant_id=l.tenant_id and i.id=l.inventory_item_id
      join inventory.warehouses w on w.tenant_id=l.tenant_id and w.id=l.warehouse_id
      left join inventory.movements m on m.tenant_id=l.tenant_id and m.inventory_item_id=l.inventory_item_id and m.warehouse_id=l.warehouse_id and m.unit=l.unit and m.status in ('recorded','reversed')
      left join reserved r on r.tenant_id=l.tenant_id and r.inventory_item_id=l.inventory_item_id and r.warehouse_id=l.warehouse_id and r.unit=l.unit
      where l.tenant_id=:tenant_id
      group by l.tenant_id,l.inventory_item_id,i.code,i.name,i.type,i.category,i.status,l.warehouse_id,w.code,w.name,l.unit,r.reserved_quantity,i.minimum_stock,i.maximum_stock
    ), x as (
      select *,on_hand_quantity-reserved_quantity available_quantity,
        case when on_hand_quantity<0 then 'negative' when on_hand_quantity=0 then 'out_of_stock' when on_hand_quantity<minimum_stock then 'below_minimum' when maximum_stock is not null and on_hand_quantity>maximum_stock then 'above_maximum' else 'normal' end stock_status
      from balances
    ) select * from x where x.tenant_id=:tenant_id {extra_where} order by x.item_code,x.warehouse_code,x.unit"""


def build_report(repository, tenant_id, report_code, filters):
    if report_code not in REPORT_PERMISSIONS:
        raise ErclaveError("report_not_found", "Inventory report does not exist.", status_code=404)
    params = {"tenant_id": tenant_id}
    stamp = date.today().isoformat()
    if report_code == "warehouses":
        where = _clauses(filters,{"status":"x.status=:status","type":"x.type=:type","q":"(x.code ilike '%'||:q||'%' or x.name ilike '%'||:q||'%')"},params)
        rows=_query(repository,f"select x.code,x.name,x.type,x.status,x.business_center,x.location,x.owner,x.capacity,x.inventory_policy,x.zone,x.aisle,x.rack,x.level,x.position from inventory.warehouses x where {' and '.join(where)} order by x.code",params)
        columns=[C("code","Código","Code"),C("name","Almacén","Warehouse"),C("type","Tipo","Type"),C("status","Estatus","Status"),C("business_center","Centro de negocio","Business center"),C("location","Ubicación","Location"),C("owner","Responsable","Owner"),C("capacity","Capacidad","Capacity"),C("inventory_policy","Política","Policy"),C("zone","Zona","Zone"),C("aisle","Pasillo","Aisle"),C("rack","Rack","Rack"),C("level","Nivel","Level"),C("position","Posición","Position")]
    elif report_code == "items":
        where=_clauses(filters,{"status":"x.status=:status","type":"x.type=:type","category":"x.category=:category","q":"(x.code ilike '%'||:q||'%' or x.name ilike '%'||:q||'%')"},params)
        rows=_query(repository,f"select x.code,x.name,x.type,x.category,x.base_unit,x.inventory_policy,x.minimum_stock,x.maximum_stock,x.default_unit_cost,x.use_in_recipe,x.status,x.created_at from inventory.items x where {' and '.join(where)} order by x.code",params)
        columns=[C("code","Código","Code"),C("name","Artículo","Item"),C("type","Tipo","Type"),C("category","Categoría","Category"),C("base_unit","Unidad base","Base unit"),C("inventory_policy","Política","Policy"),C("minimum_stock","Mínimo","Minimum"),C("maximum_stock","Máximo","Maximum"),C("default_unit_cost","Costo unitario","Unit cost"),C("use_in_recipe","Usa en receta","Used in recipe"),C("status","Estatus","Status"),C("created_at","Creado","Created")]
    elif report_code == "kardex":
        where=_clauses(filters,{"warehouse_id":"x.warehouse_id=:warehouse_id","item_id":"x.inventory_item_id=:item_id","movement_type":"x.movement_type=:movement_type","date_from":"x.occurred_at::date>=:date_from","date_to":"x.occurred_at::date<=:date_to"},params)
        rows=_query(repository,f"""select x.movement_code,x.occurred_at,x.movement_type,i.code item_code,i.name item_name,w.code warehouse_code,w.name warehouse_name,x.direction,x.quantity,x.unit,x.unit_cost,x.status,x.reason,x.source_type,x.source_id
          from inventory.movements x join inventory.items i on i.id=x.inventory_item_id and i.tenant_id=x.tenant_id join inventory.warehouses w on w.id=x.warehouse_id and w.tenant_id=x.tenant_id where {' and '.join(where)} order by x.occurred_at desc,x.movement_code""",params)
        columns=[C("movement_code","Movimiento","Movement"),C("occurred_at","Fecha","Date"),C("movement_type","Tipo","Type"),C("item_code","Artículo","Item"),C("item_name","Nombre","Name"),C("warehouse_code","Almacén","Warehouse"),C("warehouse_name","Nombre de almacén","Warehouse name"),C("direction","Dirección","Direction"),C("quantity","Cantidad","Quantity"),C("unit","Unidad","Unit"),C("unit_cost","Costo unitario","Unit cost"),C("status","Estatus","Status"),C("reason","Motivo","Reason"),C("source_type","Origen","Source"),C("source_id","Referencia","Reference")]
    else:
        extra=[]
        for key,column in (("warehouse_id","warehouse_id"),("item_id","inventory_item_id"),("condition","stock_status")):
            if filters.get(key) not in (None,""):
                extra.append(f"and x.{column}=:{key}");params[key]=filters[key]
        if report_code=="critical-reservations":
            extra.append("and (x.available_quantity < 0 or x.reserved_quantity > x.on_hand_quantity)")
        rows=_query(repository,_balance_sql(" ".join(extra)),params)
        columns=[C("item_code","Artículo","Item"),C("item_name","Nombre","Name"),C("item_type","Tipo","Type"),C("category","Categoría","Category"),C("warehouse_code","Almacén","Warehouse"),C("warehouse_name","Nombre de almacén","Warehouse name"),C("unit","Unidad","Unit"),C("on_hand_quantity","Existencia","On hand"),C("reserved_quantity","Reservado","Reserved"),C("available_quantity","Disponible","Available"),C("inventory_value","Valor inventario","Inventory value"),C("minimum_stock","Mínimo","Minimum"),C("maximum_stock","Máximo","Maximum"),C("stock_status","Condición","Condition"),C("last_movement_at","Último movimiento","Last movement")]
    return ReportResult(f"inventory-{report_code}-{stamp}.csv",columns,rows)
