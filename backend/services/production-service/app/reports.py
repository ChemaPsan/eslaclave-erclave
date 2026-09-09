from __future__ import annotations

from datetime import date

from sqlalchemy import text

from erclave_common.csv_reports import REPORT_MAX_ROWS, ReportColumn, ReportResult
from erclave_common.errors import ErclaveError


C = ReportColumn
REPORT_PERMISSIONS = {
    "product-services": "production.product_service.read",
    "recipe-versions": "production.recipe.read",
    "orders": "production.order.read",
    "deliverables-by-area": "production.order.read",
    "machines": "production.machine.read",
}


def _query(repository, sql: str, params: dict) -> list[dict]:
    bounded_params={**params,"_report_limit":REPORT_MAX_ROWS+1}
    with repository.engine.connect() as connection:
        return [dict(row) for row in connection.execute(text(f"select * from ({sql}) report_rows limit :_report_limit"), bounded_params).mappings()]


def _where(filters: dict, mapping: dict[str, str], params: dict) -> list[str]:
    clauses = ["x.tenant_id = :tenant_id"]
    for key, expression in mapping.items():
        value = filters.get(key)
        if value not in (None, ""):
            clauses.append(expression)
            params[key] = value
    return clauses


def build_report(repository, tenant_id: str, report_code: str, filters: dict) -> ReportResult:
    if report_code not in REPORT_PERMISSIONS:
        raise ErclaveError("report_not_found", "Production report does not exist.", status_code=404)
    params = {"tenant_id": tenant_id}
    stamp = date.today().isoformat()

    if report_code == "product-services":
        clauses = _where(filters, {
            "status": "x.status = :status", "type": "x.type = :type",
            "q": "(x.code ILIKE '%' || :q || '%' OR x.name ILIKE '%' || :q || '%')",
        }, params)
        rows = _query(repository, f"""select x.code,x.name,x.type,x.category,x.base_unit,x.status,
            x.target_price,x.standard_cost,x.expected_margin,x.responsible_area,x.created_at
            from production.product_services x where {' and '.join(clauses)} order by x.code""", params)
        columns = [C("code","Código","Code"),C("name","Nombre","Name"),C("type","Tipo","Type"),C("category","Categoría","Category"),C("base_unit","Unidad base","Base unit"),C("status","Estatus","Status"),C("target_price","Precio objetivo","Target price"),C("standard_cost","Costo estándar","Standard cost"),C("expected_margin","Margen esperado","Expected margin"),C("responsible_area","Área responsable","Responsible area"),C("created_at","Creado","Created")]
    elif report_code == "recipe-versions":
        clauses = _where(filters, {
            "status": "x.status = :status", "product_id": "p.id = :product_id",
        }, params)
        rows = _query(repository, f"""select p.code product_code,p.name product_name,r.code recipe_code,r.name recipe_name,
            x.version_number,x.status,x.base_quantity,x.base_unit,x.standard_cost,x.suggested_duration_days,
            x.change_reason,x.approved_at,x.created_at
            from production.recipe_versions x join production.recipes r on r.id=x.recipe_id and r.tenant_id=x.tenant_id
            join production.product_services p on p.id=r.product_service_id and p.tenant_id=x.tenant_id
            where {' and '.join(clauses)} order by p.code,r.code,x.version_number desc""", params)
        columns = [C("product_code","Producto","Product"),C("product_name","Nombre de producto","Product name"),C("recipe_code","Receta","Recipe"),C("recipe_name","Nombre de receta","Recipe name"),C("version_number","Versión","Version"),C("status","Estatus","Status"),C("base_quantity","Cantidad base","Base quantity"),C("base_unit","Unidad","Unit"),C("standard_cost","Costo estándar","Standard cost"),C("suggested_duration_days","Duración sugerida (días)","Suggested duration (days)"),C("change_reason","Motivo del cambio","Change reason"),C("approved_at","Aprobada","Approved"),C("created_at","Creada","Created")]
    elif report_code == "orders":
        clauses = _where(filters, {
            "status": "x.status = :status", "priority": "x.priority = :priority",
            "date_from": "x.required_at::date >= :date_from", "date_to": "x.required_at::date <= :date_to",
        }, params)
        rows = _query(repository, f"""select x.code,p.code product_code,p.name product_name,x.quantity,x.unit,x.status,x.priority,
            x.required_at,x.planned_start_at,x.planned_end_at,x.actual_start_at,x.actual_end_at,
            x.responsible_name_snapshot,x.planned_cost,x.actual_cost,x.created_at
            from production.production_orders x join production.product_services p on p.id=x.product_service_id and p.tenant_id=x.tenant_id
            where {' and '.join(clauses)} order by x.required_at desc nulls last,x.created_at desc""", params)
        columns = [C("code","Orden","Order"),C("product_code","Producto","Product"),C("product_name","Nombre","Name"),C("quantity","Cantidad","Quantity"),C("unit","Unidad","Unit"),C("status","Estatus","Status"),C("priority","Prioridad","Priority"),C("required_at","Fecha requerida","Required date"),C("planned_start_at","Inicio planeado","Planned start"),C("planned_end_at","Fin planeado","Planned end"),C("actual_start_at","Inicio real","Actual start"),C("actual_end_at","Fin real","Actual end"),C("responsible_name_snapshot","Responsable","Responsible"),C("planned_cost","Costo planeado","Planned cost"),C("actual_cost","Costo real","Actual cost"),C("created_at","Creada","Created")]
    elif report_code == "deliverables-by-area":
        clauses = _where(filters, {
            "status": "x.status = :status", "area_id": "s.labor_area_ref_id = :area_id",
            "date_from": "x.required_at::date >= :date_from", "date_to": "x.required_at::date <= :date_to",
        }, params)
        rows = _query(repository, f"""select coalesce(s.labor_area_name_snapshot,'Sin área') area_name,x.code order_code,
            p.code product_code,p.name product_name,s.name stage_name,s.status stage_status,s.progress_percent,
            s.responsible_name_snapshot,x.required_at,x.status,x.priority
            from production.production_orders x join production.product_services p on p.id=x.product_service_id and p.tenant_id=x.tenant_id
            join production.production_order_stages s on s.production_order_id=x.id and s.tenant_id=x.tenant_id
            where {' and '.join(clauses)} order by area_name,x.required_at,x.code,s.sort_order""", params)
        columns = [C("area_name","Área","Area"),C("order_code","Orden","Order"),C("product_code","Producto","Product"),C("product_name","Nombre","Name"),C("stage_name","Etapa","Stage"),C("stage_status","Estatus de etapa","Stage status"),C("progress_percent","Avance %","Progress %"),C("responsible_name_snapshot","Responsable","Responsible"),C("required_at","Fecha requerida","Required date"),C("status","Estatus de orden","Order status"),C("priority","Prioridad","Priority")]
    else:
        clauses = _where(filters, {
            "status": "x.status = :status", "area_id": "x.area_ref_id = :area_id",
            "q": "(x.code ILIKE '%' || :q || '%' OR x.name ILIKE '%' || :q || '%')",
        }, params)
        rows = _query(repository, f"""select x.code,x.name,x.machine_type,x.area_name,x.available_minutes_per_day,
            x.cost_per_minute,x.status,x.maintenance_order_ref_id,x.created_at
            from production.machines x where {' and '.join(clauses)} order by x.code""", params)
        columns = [C("code","Código","Code"),C("name","Máquina","Machine"),C("machine_type","Tipo","Type"),C("area_name","Área","Area"),C("available_minutes_per_day","Minutos disponibles/día","Available minutes/day"),C("cost_per_minute","Costo/minuto","Cost/minute"),C("status","Estatus","Status"),C("maintenance_order_ref_id","Orden de mantenimiento","Maintenance order"),C("created_at","Creada","Created")]

    return ReportResult(f"production-{report_code}-{stamp}.csv", columns, rows)
