from datetime import date

from sqlalchemy import text

from erclave_common.csv_reports import REPORT_MAX_ROWS, ReportColumn, ReportResult
from erclave_common.errors import ErclaveError

C=ReportColumn
REPORT_PERMISSIONS={"suppliers":"purchasing.supplier.read","requisitions":"purchasing.requisition.read","orders":"purchasing.order.read","receipts":"purchasing.receipt.read"}

def _query(repository,sql,params):
    bounded_params={**params,"_report_limit":REPORT_MAX_ROWS+1}
    with repository.engine.connect() as connection:return [dict(x) for x in connection.execute(text(f"select * from ({sql}) report_rows limit :_report_limit"),bounded_params).mappings()]

def _where(filters,mapping,params):
    where=["x.tenant_id=:tenant_id"]
    for key,expr in mapping.items():
        if filters.get(key) not in (None,""):where.append(expr);params[key]=filters[key]
    return where

def build_report(repository,tenant_id,report_code,filters):
    if report_code not in REPORT_PERMISSIONS:raise ErclaveError("report_not_found","Purchasing report does not exist.",status_code=404)
    params={"tenant_id":tenant_id};stamp=date.today().isoformat()
    if report_code=="suppliers":
        where=_where(filters,{"status":"x.status=:status","currency":"x.currency=:currency","q":"(x.code ilike '%'||:q||'%' or x.commercial_name ilike '%'||:q||'%')"},params)
        rows=_query(repository,f"select x.code,x.commercial_name,x.currency,x.payment_terms,x.lead_time_days,x.status,x.created_at,x.updated_at from purchasing.suppliers x where {' and '.join(where)} order by x.commercial_name",params)
        columns=[C("code","Código","Code"),C("commercial_name","Proveedor","Supplier"),C("currency","Moneda","Currency"),C("payment_terms","Condiciones de pago","Payment terms"),C("lead_time_days","Plazo (días)","Lead time (days)"),C("status","Estatus","Status"),C("created_at","Creado","Created"),C("updated_at","Actualizado","Updated")]
    elif report_code=="requisitions":
        where=_where(filters,{"status":"x.status=:status","priority":"x.priority=:priority","date_from":"x.required_date>=:date_from","date_to":"x.required_date<=:date_to"},params)
        rows=_query(repository,f"""select x.code,x.status,x.required_date,x.priority,x.source_type,x.source_id,count(l.id) line_count,coalesce(sum(l.quantity),0) total_quantity,x.submitted_at,x.approved_at,x.created_at
          from purchasing.requisitions x left join purchasing.requisition_lines l on l.requisition_id=x.id and l.tenant_id=x.tenant_id where {' and '.join(where)} group by x.id order by x.required_date desc,x.created_at desc""",params)
        columns=[C("code","Requisición","Requisition"),C("status","Estatus","Status"),C("required_date","Fecha requerida","Required date"),C("priority","Prioridad","Priority"),C("source_type","Origen","Source"),C("source_id","Referencia","Reference"),C("line_count","Partidas","Lines"),C("total_quantity","Cantidad total","Total quantity"),C("submitted_at","Enviada","Submitted"),C("approved_at","Aprobada","Approved"),C("created_at","Creada","Created")]
    elif report_code=="orders":
        where=_where(filters,{"status":"x.status=:status","supplier_id":"x.supplier_id=:supplier_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to"},params)
        rows=_query(repository,f"""select x.code,x.supplier_code_snapshot supplier_code,x.supplier_name_snapshot supplier_name,x.status,x.currency,x.payment_terms,x.subtotal,count(l.id) line_count,coalesce(sum(l.received_quantity),0) received_quantity,x.issued_at,x.created_at
          from purchasing.purchase_orders x left join purchasing.purchase_order_lines l on l.purchase_order_id=x.id and l.tenant_id=x.tenant_id where {' and '.join(where)} group by x.id order by x.created_at desc""",params)
        columns=[C("code","Orden de compra","Purchase order"),C("supplier_code","Proveedor","Supplier"),C("supplier_name","Nombre del proveedor","Supplier name"),C("status","Estatus","Status"),C("currency","Moneda","Currency"),C("payment_terms","Condiciones de pago","Payment terms"),C("subtotal","Subtotal","Subtotal"),C("line_count","Partidas","Lines"),C("received_quantity","Cantidad recibida","Received quantity"),C("issued_at","Emitida","Issued"),C("created_at","Creada","Created")]
    else:
        where=_where(filters,{"status":"x.status=:status","supplier_id":"po.supplier_id=:supplier_id","date_from":"x.received_at::date>=:date_from","date_to":"x.received_at::date<=:date_to","line_type":"pol.line_type=:line_type"},params)
        rows=_query(repository,f"""select x.code,po.code order_code,po.supplier_code_snapshot supplier_code,po.supplier_name_snapshot supplier_name,x.status,x.supplier_document_reference,x.received_at,count(distinct rl.id) line_count,coalesce(sum(rl.quantity),0) received_quantity,count(distinct rl.id) filter(where rl.reconciliation_status!='completed') pending_reconciliations,x.created_at
          from purchasing.purchase_receipts x join purchasing.purchase_orders po on po.id=x.purchase_order_id and po.tenant_id=x.tenant_id left join purchasing.purchase_receipt_lines rl on rl.receipt_id=x.id and rl.tenant_id=x.tenant_id left join purchasing.purchase_order_lines pol on pol.id=rl.order_line_id and pol.tenant_id=x.tenant_id where {' and '.join(where)} group by x.id,po.id order by x.received_at desc""",params)
        columns=[C("code","Recepción","Receipt"),C("order_code","Orden de compra","Purchase order"),C("supplier_code","Proveedor","Supplier"),C("supplier_name","Nombre del proveedor","Supplier name"),C("status","Estatus","Status"),C("supplier_document_reference","Documento del proveedor","Supplier document"),C("received_at","Recibida","Received"),C("line_count","Partidas","Lines"),C("received_quantity","Cantidad recibida","Received quantity"),C("pending_reconciliations","Conciliaciones pendientes","Pending reconciliations"),C("created_at","Creada","Created")]
    return ReportResult(f"purchasing-{report_code}-{stamp}.csv",columns,rows)
