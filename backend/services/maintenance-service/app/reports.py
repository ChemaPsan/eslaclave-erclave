from datetime import date

from sqlalchemy import text

from erclave_common.csv_reports import REPORT_MAX_ROWS, ReportColumn, ReportResult
from erclave_common.errors import ErclaveError

C=ReportColumn
REPORT_PERMISSIONS={"orders":"maintenance.order.read","downtime":"maintenance.order.read","spare-parts":"maintenance.material_request.read","labor-times":"maintenance.time.read"}

def _query(repository,sql,params):
    bounded_params={**params,"_report_limit":REPORT_MAX_ROWS+1}
    with repository.engine.connect() as connection:return [dict(x) for x in connection.execute(text(f"select * from ({sql}) report_rows limit :_report_limit"),bounded_params).mappings()]

def _where(filters,mapping,params,alias="x"):
    where=[f"{alias}.tenant_id=:tenant_id"]
    for key,expr in mapping.items():
        if filters.get(key) not in (None,""):where.append(expr);params[key]=filters[key]
    return where

def build_report(repository,tenant_id,report_code,filters):
    if report_code not in REPORT_PERMISSIONS:raise ErclaveError("report_not_found","Maintenance report does not exist.",status_code=404)
    params={"tenant_id":tenant_id};stamp=date.today().isoformat()
    if report_code=="orders":
        where=_where(filters,{"status":"x.status=:status","priority":"x.priority=:priority","responsible_worker_id":"x.assigned_worker_ref_id=:responsible_worker_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to"},params)
        rows=_query(repository,f"select x.code,x.title,x.target_type,x.machine_code_snapshot machine_code,x.machine_name_snapshot machine_name,x.location,x.priority,x.status,x.assigned_worker_name_snapshot responsible_worker,x.integration_status,x.requested_at,x.started_at,x.resolved_at,x.closed_at,x.created_at from maintenance.orders x where {' and '.join(where)} order by x.created_at desc",params)
        columns=[C("code","Orden","Order"),C("title","Título","Title"),C("target_type","Objetivo","Target"),C("machine_code","Máquina","Machine"),C("machine_name","Nombre de máquina","Machine name"),C("location","Ubicación","Location"),C("priority","Prioridad","Priority"),C("status","Estatus","Status"),C("responsible_worker","Responsable","Responsible"),C("integration_status","Integración","Integration"),C("requested_at","Solicitada","Requested"),C("started_at","Iniciada","Started"),C("resolved_at","Resuelta","Resolved"),C("closed_at","Cerrada","Closed"),C("created_at","Creada","Created")]
    elif report_code=="downtime":
        where=_where(filters,{"target_type":"x.target_type=:target_type","q":"(x.code ilike '%'||:q||'%' or coalesce(x.machine_name_snapshot,'') ilike '%'||:q||'%')","date_from":"coalesce(x.started_at,x.requested_at,x.created_at)::date>=:date_from","date_to":"coalesce(x.started_at,x.requested_at,x.created_at)::date<=:date_to"},params)
        where.append("x.production_machine_ref_id is not null")
        rows=_query(repository,f"select x.code,x.machine_code_snapshot machine_code,x.machine_name_snapshot machine_name,x.status,x.priority,coalesce(x.started_at,x.requested_at,x.created_at) outage_start,coalesce(x.resolved_at,x.cancelled_at,x.closed_at,now()) outage_end,round(extract(epoch from (coalesce(x.resolved_at,x.cancelled_at,x.closed_at,now())-coalesce(x.started_at,x.requested_at,x.created_at)))/60) downtime_minutes,x.source_production_order_code_snapshot production_order,x.integration_status from maintenance.orders x where {' and '.join(where)} order by outage_start desc",params)
        columns=[C("code","Orden","Order"),C("machine_code","Máquina","Machine"),C("machine_name","Nombre de máquina","Machine name"),C("status","Estatus","Status"),C("priority","Prioridad","Priority"),C("outage_start","Inicio de paro","Downtime start"),C("outage_end","Fin de paro","Downtime end"),C("downtime_minutes","Minutos de paro","Downtime minutes"),C("production_order","Orden de producción","Production order"),C("integration_status","Integración","Integration")]
    elif report_code=="spare-parts":
        where=_where(filters,{"status":"x.status=:status","warehouse_id":"x.warehouse_ref_id=:warehouse_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to"},params)
        rows=_query(repository,f"""select o.code order_code,x.warehouse_name_snapshot warehouse_name,x.status request_status,l.line_number,l.item_code_snapshot item_code,l.item_name_snapshot item_name,l.quantity,l.unit_code,l.unit_cost_snapshot,(l.quantity*coalesce(l.unit_cost_snapshot,0)) line_cost,l.line_status,x.created_at
          from maintenance.material_requests x join maintenance.orders o on o.id=x.order_id and o.tenant_id=x.tenant_id join maintenance.material_request_lines l on l.material_request_id=x.id and l.tenant_id=x.tenant_id where {' and '.join(where)} order by x.created_at desc,o.code,l.line_number""",params)
        columns=[C("order_code","Orden","Order"),C("warehouse_name","Almacén","Warehouse"),C("request_status","Estatus de solicitud","Request status"),C("line_number","Partida","Line"),C("item_code","Refacción","Spare part"),C("item_name","Nombre","Name"),C("quantity","Cantidad","Quantity"),C("unit_code","Unidad","Unit"),C("unit_cost_snapshot","Costo unitario","Unit cost"),C("line_cost","Costo total","Total cost"),C("line_status","Estatus de partida","Line status"),C("created_at","Solicitada","Requested")]
    else:
        where=_where(filters,{"worker_id":"x.worker_ref_id=:worker_id","date_from":"x.started_at::date>=:date_from","date_to":"x.started_at::date<=:date_to","status":"o.status=:status"},params)
        rows=_query(repository,f"select o.code order_code,o.title,o.status order_status,x.worker_name_snapshot worker_name,x.started_at,x.ended_at,x.minutes,x.notes,x.created_at from maintenance.time_entries x join maintenance.orders o on o.id=x.order_id and o.tenant_id=x.tenant_id where {' and '.join(where)} order by x.started_at desc",params)
        columns=[C("order_code","Orden","Order"),C("title","Título","Title"),C("order_status","Estatus de orden","Order status"),C("worker_name","Trabajador","Worker"),C("started_at","Inicio","Start"),C("ended_at","Fin","End"),C("minutes","Minutos","Minutes"),C("notes","Notas","Notes"),C("created_at","Capturado","Captured")]
    return ReportResult(f"maintenance-{report_code}-{stamp}.csv",columns,rows)
