from datetime import date

from sqlalchemy import text

from erclave_common.csv_reports import REPORT_MAX_ROWS, ReportColumn, ReportResult
from erclave_common.errors import ErclaveError

C=ReportColumn
REPORT_PERMISSIONS={"areas-positions":"hr.position.read","workers":"hr.worker.read","production-capacity":"hr.position.read","eligibility":"hr.position.read"}

def _query(repository,sql,params):
    bounded_params={**params,"_report_limit":REPORT_MAX_ROWS+1}
    with repository.engine.connect() as connection:return [dict(x) for x in connection.execute(text(f"select * from ({sql}) report_rows limit :_report_limit"),bounded_params).mappings()]

def build_report(repository,tenant_id,report_code,filters):
    if report_code not in REPORT_PERMISSIONS:raise ErclaveError("report_not_found","HR report does not exist.",status_code=404)
    params={"tenant_id":tenant_id};where=["x.tenant_id=:tenant_id"]
    stamp=date.today().isoformat()
    if report_code=="areas-positions":
        for key,expr in {"area_id":"a.id=:area_id","status":"x.status=:status","eligibility":"(:eligibility='production' and x.intervenes_in_production) or (:eligibility='maintenance' and x.intervenes_in_maintenance)"}.items():
            if filters.get(key):where.append(f"({expr})");params[key]=filters[key]
        rows=_query(repository,f"""select a.code area_code,a.name area_name,a.status area_status,x.position,x.recipe_name,x.resource_quantity,x.minutes_per_resource,x.hourly_cost,x.intervenes_in_production,x.intervenes_in_maintenance,x.status
          from hr.labor_roles x join hr.labor_areas a on a.id=x.labor_area_id and a.tenant_id=x.tenant_id where {' and '.join(where)} order by a.code,x.position""",params)
        columns=[C("area_code","Área","Area"),C("area_name","Nombre de área","Area name"),C("area_status","Estatus de área","Area status"),C("position","Puesto","Position"),C("recipe_name","Perfil/receta","Profile/recipe"),C("resource_quantity","Recursos","Resources"),C("minutes_per_resource","Minutos por recurso","Minutes per resource"),C("hourly_cost","Costo por hora","Hourly cost"),C("intervenes_in_production","Elegible producción","Production eligible"),C("intervenes_in_maintenance","Elegible mantenimiento","Maintenance eligible"),C("status","Estatus","Status")]
    elif report_code=="workers":
        for key,expr in {"area_id":"a.id=:area_id","position_id":"r.id=:position_id","status":"x.status=:status"}.items():
            if filters.get(key):where.append(expr);params[key]=filters[key]
        rows=_query(repository,f"""select x.employee_number,concat_ws(' ',x.first_names,x.first_last_name,x.second_last_name) full_name,x.hire_date,a.code area_code,a.name area_name,r.position,r.intervenes_in_production,r.intervenes_in_maintenance,x.status,x.created_at
          from hr.workers x left join hr.labor_roles r on r.id=x.labor_position_id and r.tenant_id=x.tenant_id left join hr.labor_areas a on a.id=r.labor_area_id and a.tenant_id=x.tenant_id where {' and '.join(where)} order by x.employee_number""",params)
        columns=[C("employee_number","Número de empleado","Employee number"),C("full_name","Nombre","Name"),C("hire_date","Ingreso","Hire date"),C("area_code","Área","Area"),C("area_name","Nombre de área","Area name"),C("position","Puesto","Position"),C("intervenes_in_production","Elegible producción","Production eligible"),C("intervenes_in_maintenance","Elegible mantenimiento","Maintenance eligible"),C("status","Estatus","Status"),C("created_at","Creado","Created")]
    elif report_code=="production-capacity":
        where.append("x.intervenes_in_production=true")
        for key,expr in {"area_id":"a.id=:area_id","position_id":"x.id=:position_id","status":"x.status=:status"}.items():
            if filters.get(key):where.append(expr);params[key]=filters[key]
        rows=_query(repository,f"""select a.code area_code,a.name area_name,x.position,x.recipe_name,x.resource_quantity,x.minutes_per_resource,(x.resource_quantity*x.minutes_per_resource) configured_minutes,x.hourly_cost,x.status,
          count(w.id) filter(where w.status='active') active_workers,(count(w.id) filter(where w.status='active')*x.minutes_per_resource) staffed_minutes
          from hr.labor_roles x join hr.labor_areas a on a.id=x.labor_area_id and a.tenant_id=x.tenant_id left join hr.workers w on w.labor_position_id=x.id and w.tenant_id=x.tenant_id
          where {' and '.join(where)} group by a.code,a.name,x.id order by a.code,x.position""",params)
        columns=[C("area_code","Área","Area"),C("area_name","Nombre de área","Area name"),C("position","Puesto","Position"),C("recipe_name","Perfil/receta","Profile/recipe"),C("resource_quantity","Recursos configurados","Configured resources"),C("minutes_per_resource","Minutos por recurso","Minutes per resource"),C("configured_minutes","Minutos configurados","Configured minutes"),C("active_workers","Trabajadores activos","Active workers"),C("staffed_minutes","Minutos con plantilla","Staffed minutes"),C("hourly_cost","Costo por hora","Hourly cost"),C("status","Estatus","Status")]
    else:
        purpose=filters.get("purpose") or "production"
        if purpose not in {"production","maintenance","sales"}:raise ErclaveError("report_filter_invalid","Eligibility purpose is invalid.",status_code=422)
        if purpose=="production":where.append("x.intervenes_in_production=true")
        elif purpose=="maintenance":where.append("x.intervenes_in_maintenance=true")
        else:where.append("x.status='active'")
        for key,expr in {"area_id":"a.id=:area_id","status":"x.status=:status"}.items():
            if filters.get(key):where.append(expr);params[key]=filters[key]
        params["purpose"]=purpose
        rows=_query(repository,f"""select :purpose purpose,a.code area_code,a.name area_name,x.position,x.recipe_name,x.status,count(w.id) filter(where w.status='active') active_workers
          from hr.labor_roles x join hr.labor_areas a on a.id=x.labor_area_id and a.tenant_id=x.tenant_id left join hr.workers w on w.labor_position_id=x.id and w.tenant_id=x.tenant_id
          where {' and '.join(where)} group by a.code,a.name,x.id order by a.code,x.position""",params)
        columns=[C("purpose","Propósito","Purpose"),C("area_code","Área","Area"),C("area_name","Nombre de área","Area name"),C("position","Puesto elegible","Eligible position"),C("recipe_name","Perfil/receta","Profile/recipe"),C("active_workers","Trabajadores activos","Active workers"),C("status","Estatus","Status")]
    return ReportResult(f"hr-{report_code}-{stamp}.csv",columns,rows)
