from datetime import date

from sqlalchemy import text

from erclave_common.csv_reports import REPORT_MAX_ROWS, ReportColumn, ReportResult
from erclave_common.errors import ErclaveError

C=ReportColumn
REPORT_PERMISSIONS={"customers":"sales.customer.read","quotes":"sales.quote.read","orders":"sales.order.read","deliveries":"sales.delivery.read","commercial-margin":"sales.order.read","service-orders":"sales.service_order.read"}

def _query(repository,sql,params):
    bounded_params={**params,"_report_limit":REPORT_MAX_ROWS+1}
    with repository.engine.connect() as connection:return [dict(x) for x in connection.execute(text(f"select * from ({sql}) report_rows limit :_report_limit"),bounded_params).mappings()]

def _where(filters,mapping,params):
    where=["x.tenant_id=:tenant_id"]
    for key,expr in mapping.items():
        if filters.get(key) not in (None,""):where.append(expr);params[key]=filters[key]
    return where

def build_report(repository,tenant_id,report_code,filters):
    if report_code not in REPORT_PERMISSIONS:raise ErclaveError("report_not_found","Sales report does not exist.",status_code=404)
    params={"tenant_id":tenant_id};stamp=date.today().isoformat()
    if report_code=="customers":
        where=_where(filters,{"status":"x.status=:status","responsible_worker_id":"x.responsible_worker_ref_id=:responsible_worker_id","q":"(x.code ilike '%'||:q||'%' or x.commercial_name ilike '%'||:q||'%')"},params)
        rows=_query(repository,f"select x.code,x.commercial_name,x.customer_type,x.status,x.responsible_worker_name,x.payment_terms,x.currency,x.credit_limit,x.created_at,x.updated_at from sales.customers x where {' and '.join(where)} order by x.commercial_name",params)
        columns=[C("code","Código","Code"),C("commercial_name","Cliente","Customer"),C("customer_type","Tipo","Type"),C("status","Estatus","Status"),C("responsible_worker_name","Responsable","Responsible"),C("payment_terms","Condiciones de pago","Payment terms"),C("currency","Moneda","Currency"),C("credit_limit","Límite de crédito","Credit limit"),C("created_at","Creado","Created"),C("updated_at","Actualizado","Updated")]
    elif report_code=="quotes":
        where=_where(filters,{"status":"x.status=:status","customer_id":"x.customer_id=:customer_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to"},params)
        rows=_query(repository,f"select x.code,x.customer_code_snapshot customer_code,x.customer_name_snapshot customer_name,x.responsible_worker_name,x.status,x.currency,x.valid_until,x.promised_delivery_date,x.subtotal,x.discount_total,x.total,x.estimated_cost,x.estimated_margin,x.created_at from sales.quotes x where {' and '.join(where)} order by x.created_at desc",params)
        columns=[C("code","Cotización","Quote"),C("customer_code","Cliente","Customer"),C("customer_name","Nombre del cliente","Customer name"),C("responsible_worker_name","Responsable","Responsible"),C("status","Estatus","Status"),C("currency","Moneda","Currency"),C("valid_until","Válida hasta","Valid until"),C("promised_delivery_date","Entrega prometida","Promised delivery"),C("subtotal","Subtotal","Subtotal"),C("discount_total","Descuento","Discount"),C("total","Total","Total"),C("estimated_cost","Costo estimado","Estimated cost"),C("estimated_margin","Margen estimado","Estimated margin"),C("created_at","Creada","Created")]
    elif report_code=="orders":
        where=_where(filters,{"status":"x.status=:status","customer_id":"x.customer_id=:customer_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to"},params)
        rows=_query(repository,f"select x.code,x.quote_code_snapshot quote_code,x.customer_code_snapshot customer_code,x.customer_name_snapshot customer_name,x.responsible_worker_name,x.status,x.fulfillment_state,x.currency,x.promised_delivery_date,x.total,x.estimated_cost,x.estimated_margin,x.actual_cost,x.actual_margin,x.created_at from sales.orders x where {' and '.join(where)} order by x.created_at desc",params)
        columns=[C("code","Pedido","Order"),C("quote_code","Cotización","Quote"),C("customer_code","Cliente","Customer"),C("customer_name","Nombre del cliente","Customer name"),C("responsible_worker_name","Responsable","Responsible"),C("status","Estatus","Status"),C("fulfillment_state","Surtimiento","Fulfillment"),C("currency","Moneda","Currency"),C("promised_delivery_date","Entrega prometida","Promised delivery"),C("total","Total","Total"),C("estimated_cost","Costo estimado","Estimated cost"),C("estimated_margin","Margen estimado","Estimated margin"),C("actual_cost","Costo real","Actual cost"),C("actual_margin","Margen real","Actual margin"),C("created_at","Creado","Created")]
    elif report_code=="deliveries":
        where=_where(filters,{"status":"x.status=:status","customer_id":"x.customer_id=:customer_id","date_from":"x.scheduled_date>=:date_from","date_to":"x.scheduled_date<=:date_to"},params)
        rows=_query(repository,f"""select x.code,x.order_code_snapshot order_code,x.customer_name_snapshot customer_name,x.status,x.scheduled_date,x.delivered_at,x.recipient_name,x.evidence_reference,x.confirmation_state,
          coalesce(sum(l.quantity),0) delivered_quantity,coalesce(sum(l.actual_cost),0) actual_cost,x.created_at from sales.deliveries x left join sales.delivery_lines l on l.delivery_id=x.id and l.tenant_id=x.tenant_id where {' and '.join(where)} group by x.id order by x.scheduled_date desc,x.created_at desc""",params)
        columns=[C("code","Entrega","Delivery"),C("order_code","Pedido","Order"),C("customer_name","Cliente","Customer"),C("status","Estatus","Status"),C("scheduled_date","Fecha programada","Scheduled date"),C("delivered_at","Entregada","Delivered"),C("recipient_name","Recibió","Recipient"),C("evidence_reference","Evidencia","Evidence"),C("confirmation_state","Confirmación","Confirmation"),C("delivered_quantity","Cantidad entregada","Delivered quantity"),C("actual_cost","Costo real","Actual cost"),C("created_at","Creada","Created")]
    elif report_code=="commercial-margin":
        where=_where(filters,{"customer_id":"x.customer_id=:customer_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to","product_service_id":"exists(select 1 from sales.order_lines ol where ol.tenant_id=x.tenant_id and ol.order_id=x.id and ol.product_service_ref_id=:product_service_id)"},params)
        rows=_query(repository,f"select x.code,x.customer_code_snapshot customer_code,x.customer_name_snapshot customer_name,x.status,x.currency,x.total,x.estimated_cost,x.estimated_margin,x.actual_cost,x.actual_margin,(case when x.total<>0 then round((coalesce(x.actual_margin,x.estimated_margin)/x.total)*100,2) end) margin_percent,x.created_at from sales.orders x where {' and '.join(where)} order by x.created_at desc",params)
        columns=[C("code","Pedido","Order"),C("customer_code","Cliente","Customer"),C("customer_name","Nombre del cliente","Customer name"),C("status","Estatus","Status"),C("currency","Moneda","Currency"),C("total","Venta","Revenue"),C("estimated_cost","Costo estimado","Estimated cost"),C("estimated_margin","Margen estimado","Estimated margin"),C("actual_cost","Costo real","Actual cost"),C("actual_margin","Margen real","Actual margin"),C("margin_percent","Margen %","Margin %"),C("created_at","Fecha","Date")]
    else:
        where=_where(filters,{"status":"x.status=:status","customer_id":"x.customer_id=:customer_id","responsible_worker_id":"x.responsible_worker_ref_id=:responsible_worker_id","date_from":"x.created_at::date>=:date_from","date_to":"x.created_at::date<=:date_to"},params)
        rows=_query(repository,f"select x.code,x.order_code_snapshot order_code,x.customer_name_snapshot customer_name,x.product_service_code,x.product_service_name,x.ordered_quantity,x.unit,x.status,x.responsible_worker_name,x.planned_start_date,x.planned_end_date,x.actual_cost,x.planned_at,x.started_at,x.accepted_at,x.created_at from sales.service_orders x where {' and '.join(where)} order by x.created_at desc",params)
        columns=[C("code","Orden de servicio","Service order"),C("order_code","Pedido","Order"),C("customer_name","Cliente","Customer"),C("product_service_code","Servicio","Service"),C("product_service_name","Nombre del servicio","Service name"),C("ordered_quantity","Cantidad","Quantity"),C("unit","Unidad","Unit"),C("status","Estatus","Status"),C("responsible_worker_name","Responsable","Responsible"),C("planned_start_date","Inicio planeado","Planned start"),C("planned_end_date","Fin planeado","Planned end"),C("actual_cost","Costo real","Actual cost"),C("planned_at","Planeada","Planned"),C("started_at","Iniciada","Started"),C("accepted_at","Aceptada","Accepted"),C("created_at","Creada","Created")]
    return ReportResult(f"sales-{report_code}-{stamp}.csv",columns,rows)
