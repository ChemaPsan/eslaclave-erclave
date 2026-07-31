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
@router.get("/areas",response_model=AreaListResponse)
def areas(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access("hr.area.read"))):return AreaListResponse(data=repository.list_areas(tenant(x_tenant_id)))
@router.post("/areas",response_model=AreaResponse,status_code=201)
def create_area(payload:AreaCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.area.create"))):
    try:value=repository.create_area(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Area command conflicts with a previous request.",status_code=409) from exc
    if not value:raise ErclaveError("area_conflict","Area code already exists.",status_code=409)
    return AreaResponse(data=value)
@router.patch("/areas/{area_id}",response_model=AreaResponse)
def update_area(area_id:str,payload:AreaUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.area.update"))):
    try:value=repository.update_area(tenant(x_tenant_id),area_id,payload,key(idempotency_key),digest(payload,{"id":area_id}),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Area command conflicts with a previous request.",status_code=409) from exc
    if not value:raise ErclaveError("area_not_found","Area not found.",status_code=404)
    return AreaResponse(data=value)
@router.get("/positions",response_model=RoleListResponse)
def positions(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),area_id:str|None=None,production_only:bool=False,repository:HrRepository=Depends(get_hr_repository),_=Depends(require_hr_access("hr.position.read"))):return RoleListResponse(data=repository.list_roles(tenant(x_tenant_id),area_id,production_only))
@router.post("/positions",response_model=RoleResponse,status_code=201)
def create_position(payload:RoleCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.position.create"))):
    try:value=repository.create_role(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Position violates HR rules.",status_code=409) from exc
    if not value:raise ErclaveError("position_conflict","Position already exists in this area.",status_code=409)
    return RoleResponse(data=value)
@router.patch("/positions/{position_id}",response_model=RoleResponse)
def update_position(position_id:str,payload:RoleUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:HrRepository=Depends(get_hr_repository),access:AuthorizedContext=Depends(require_hr_access("hr.position.update"))):
    try:value=repository.update_role(tenant(x_tenant_id),position_id,payload,key(idempotency_key),digest(payload,{"id":position_id}),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Position violates HR rules.",status_code=409) from exc
    if not value:raise ErclaveError("position_not_found","Position not found.",status_code=404)
    return RoleResponse(data=value)
