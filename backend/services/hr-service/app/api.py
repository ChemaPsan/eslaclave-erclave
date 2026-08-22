import hashlib,json
from fastapi import APIRouter,Depends,Header
from erclave_common.errors import ErclaveError
from .authorization import AuthorizedContext,require_hr_access
from .repositories import HrRepository,get_hr_repository
from .schemas import *
router=APIRouter(prefix="/v1/hr",tags=["hr"])
def tenant(v):
    if not v:raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
    return v
def key(v):
    if not v or len(v.strip())<8:raise ErclaveError("idempotency_key_required","Idempotency-Key header is required.",status_code=400)
    return v.strip()
def digest(p,path=None):return hashlib.sha256(json.dumps({"body":p.model_dump(mode="json"),"path":path or {}},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def conflict(exc,default_code,default_message):
    code=str(exc)
    known={
        "idempotency_key_reused":("idempotency_key_reused","La clave de idempotencia ya fue usada con datos distintos."),
        "labor_area_invalid":("labor_area_invalid","Selecciona un area activa de Recursos Humanos."),
        "labor_position_invalid":("labor_position_invalid","Selecciona un puesto activo de Recursos Humanos."),
    }
    safe_code,safe_message=known.get(code,(default_code,default_message))
    return ErclaveError(safe_code,safe_message,status_code=409)
@router.get("/areas",response_model=AreaListResponse)
def areas(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access("hr.area.read"))):return AreaListResponse(data=repository.list_areas(tenant(x_tenant_id)))
@router.post("/areas",response_model=AreaResponse,status_code=201)
def create_area(payload:AreaCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.area.create"))):
    try:value=repository.create_area(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:raise conflict(exc,"area_command_conflict","No se pudo completar el comando de area por un conflicto de estado.") from exc
    if not value:raise ErclaveError("area_conflict","Area code already exists.",status_code=409)
    return AreaResponse(data=value)
@router.patch("/areas/{area_id}",response_model=AreaResponse)
def update_area(area_id:str,payload:AreaUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.area.update"))):
    try:value=repository.update_area(tenant(x_tenant_id),area_id,payload,key(idempotency_key),digest(payload,{"id":area_id}),access.actor_id)
    except ValueError as exc:raise conflict(exc,"area_command_conflict","No se pudo completar el comando de area por un conflicto de estado.") from exc
    if not value:raise ErclaveError("area_not_found","Area not found.",status_code=404)
    return AreaResponse(data=value)
@router.get("/positions",response_model=RoleListResponse)
def positions(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),area_id:str|None=None,production_only:bool=False,repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access("hr.position.read"))):return RoleListResponse(data=repository.list_roles(tenant(x_tenant_id),area_id,production_only))
@router.post("/positions",response_model=RoleResponse,status_code=201)
def create_position(payload:RoleCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.position.create"))):
    try:value=repository.create_role(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:raise conflict(exc,"position_command_conflict","No se pudo completar el comando de puesto por un conflicto de estado.") from exc
    if not value:raise ErclaveError("position_conflict","Position already exists in this area.",status_code=409)
    return RoleResponse(data=value)
@router.patch("/positions/{position_id}",response_model=RoleResponse)
def update_position(position_id:str,payload:RoleUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.position.update"))):
    try:value=repository.update_role(tenant(x_tenant_id),position_id,payload,key(idempotency_key),digest(payload,{"id":position_id}),access.actor_id)
    except ValueError as exc:raise conflict(exc,"position_command_conflict","No se pudo completar el comando de puesto por un conflicto de estado.") from exc
    if not value:raise ErclaveError("position_not_found","Position not found.",status_code=404)
    return RoleResponse(data=value)
@router.get("/workers",response_model=WorkerListResponse)
def workers(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),position_id:str|None=None,production_only:bool=False,active_only:bool=False,repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access("hr.worker.read"))):return WorkerListResponse(data=repository.list_workers(tenant(x_tenant_id),position_id,production_only,active_only))
@router.get("/workers/production-eligible",response_model=WorkerListResponse)
def production_workers(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access("production.order.create"))):return WorkerListResponse(data=repository.list_workers(tenant(x_tenant_id),production_only=True))
@router.get("/workers/sales-eligible",response_model=SalesEligibleWorkerListResponse)
def sales_workers(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access(("sales.customer.create","sales.customer.update","sales.quote.create","sales.quote.update")))):return SalesEligibleWorkerListResponse(data=repository.list_sales_eligible_workers(tenant(x_tenant_id)))
@router.get("/production-capacity",response_model=ProductionCapacityListResponse)
def production_capacity(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access(("production.order.validate","production.order.create")))):return ProductionCapacityListResponse(data=repository.list_production_capacity(tenant(x_tenant_id)))
@router.post("/workers",response_model=WorkerResponse,status_code=201)
def create_worker(payload:WorkerCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.worker.create"))):
    try:value=repository.create_worker(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:raise conflict(exc,"worker_command_conflict","No se pudo completar el comando de trabajador por un conflicto de estado.") from exc
    if not value:raise ErclaveError("worker_identity_conflict","Employee number, CURP, RFC or NSS already exists.",status_code=409)
    return WorkerResponse(data=value)
@router.patch("/workers/{worker_id}",response_model=WorkerResponse)
def update_worker(worker_id:str,payload:WorkerUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.worker.update"))):
    try:value=repository.update_worker(tenant(x_tenant_id),worker_id,payload,key(idempotency_key),digest(payload,{"id":worker_id}),access.actor_id)
    except ValueError as exc:raise conflict(exc,"worker_command_conflict","No se pudo completar el comando de trabajador por un conflicto de estado.") from exc
    if not value:raise ErclaveError("worker_not_found","Worker not found.",status_code=404)
    return WorkerResponse(data=value)
