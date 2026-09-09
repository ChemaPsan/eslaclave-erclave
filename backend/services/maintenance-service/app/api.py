from erclave_common.material_return_client import MaterialReturnValidation,MaterialReturnReconcile,MaterialReturnClient,get_material_return_client
import hashlib,json
from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,Header,Query
from erclave_common.errors import ErclaveError
from erclave_common.csv_reports import csv_report_response,validate_date_range
from .authorization import AuthorizedContext,require_maintenance_access
from .authorities import MaintenanceAuthorityClient,get_maintenance_authority_client
from .repositories import MaintenanceRepository,get_maintenance_repository
from .reports import REPORT_PERMISSIONS,build_report
from .schemas import *

router=APIRouter(prefix="/v1/maintenance",tags=["maintenance"])
@router.get("/reports/{report_code}/export")
def export_report(report_code:str,lang:Literal["es","en"]="es",date_from:date|None=None,date_to:date|None=None,status:str|None=None,priority:str|None=None,q:str|None=None,target_type:str|None=None,responsible_worker_id:str|None=None,worker_id:str|None=None,warehouse_id:str|None=None,x_tenant_id:str=Header(alias="X-Tenant-Id"),r:MaintenanceRepository=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access(tuple(REPORT_PERMISSIONS.values())))):
    validate_date_range(date_from,date_to);permission=REPORT_PERMISSIONS.get(report_code)
    if not permission:raise ErclaveError("report_not_found","Maintenance report does not exist.",status_code=404)
    access.require(permission)
    filters={"date_from":date_from,"date_to":date_to,"status":status,"priority":priority,"q":q,"target_type":target_type,"responsible_worker_id":responsible_worker_id,"worker_id":worker_id,"warehouse_id":warehouse_id}
    return csv_report_response(build_report(r,x_tenant_id,report_code,filters),lang)
MAINTENANCE_ORDER_ACTION_PERMISSIONS=tuple(f"maintenance.order.{action}" for action in ("request","assign","start","wait_for_parts","resume","resolve","close","reopen","cancel"))
def tenant(v):
    if not v:raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
    return v
def key(v):
    if not v or len(v.strip())<8:raise ErclaveError("idempotency_key_required","Idempotency-Key header is required.",status_code=400)
    return v.strip()
def digest(p=None,path=None):return hashlib.sha256(json.dumps({"body":p.model_dump(mode="json") if p else {},"path":path or {}},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def failure(exc):
    code=str(exc);messages={"idempotency_key_reused":"Idempotency-Key was reused with different data.","command_in_progress":"The command is still in progress.","maintenance_order_conflict":"Order code or active machine outage already exists.","maintenance_order_not_editable":"The order can no longer be edited.","invalid_maintenance_transition":"The requested maintenance transition is invalid.","maintenance_resolution_evidence_required":"Diagnosis, work performed and verification are required.","maintenance_time_required":"At least one time entry is required.","maintenance_materials_not_reconciled":"Every material request must be issued or cancelled.","maintenance_integration_pending":"Reconcile the pending external operation before continuing.","maintenance_time_status_invalid":"Time cannot be captured in the current status.","maintenance_time_worker_not_assigned":"Only the assigned maintenance technician can log time.","maintenance_time_overlap":"This worker already has overlapping time on the order.","maintenance_material_status_invalid":"Materials cannot be requested in the current status.","material_request_not_cancellable":"Only reserved or reconcilable requests can be cancelled.","material_request_not_reconcilable":"The material request has no retryable operation."};return ErclaveError(code,messages.get(code,"Maintenance command conflict."),status_code=409)
def eligible_worker(workers,worker_id):
    worker=next((item for item in workers if item["id"]==worker_id),None)
    if not worker:raise ErclaveError("maintenance_worker_not_eligible","Select an active maintenance-eligible worker.",status_code=422)
    return worker
def apply_machine_integration(tenant_id,order,authorization,r,a,actor):
    operation=order.get("integration_operation")
    if not operation:return order
    try:
        stable=f"maintenance-{order['id']}-production-{operation}"
        if operation=="block":a.block_machine(tenant_id,order["production_machine_id"],order["id"],order.get("source_production_order_id"),authorization,stable)
        else:a.release_machine(tenant_id,order["production_machine_id"],order["id"],authorization,stable)
        return r.set_order_integration(tenant_id,order["id"],"completed",actor=actor)
    except ErclaveError as exc:return r.set_order_integration(tenant_id,order["id"],"needs_reconciliation",str(exc.code),actor)
def cancel_material(tenant_id,request_id,authorization,k,r,a,actor):
    try:
        with r.material_command_lock(tenant_id,request_id):
            return cancel_material_locked(tenant_id,request_id,authorization,k,r,a,actor)
    except ValueError as exc:raise failure(exc) from exc

def cancel_material_locked(tenant_id,request_id,authorization,k,r,a,actor):
    value,plan=r.prepare_material_cancellation(tenant_id,request_id,k,digest(path={"id":request_id}),actor)
    if plan is None:return value
    released=[]
    try:
        for line in plan:
            a.release_reservation(tenant_id,line["reservation_id"],authorization,f"maintenance-{request_id}-release-{line['line_id']}")
            released.append(line["line_id"])
    except ErclaveError as exc:return r.complete_material_cancellation(tenant_id,request_id,k,released,str(exc.code),actor)
    return r.complete_material_cancellation(tenant_id,request_id,k,released,None,actor)

@router.get("/warehouse-material-requests",response_model=WarehouseMaterialListResponse)
def warehouse_material_requests(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),_=Depends(require_maintenance_access("inventory.movement.read"))):
    data,has_more=r.list_warehouse_material_requests(x_tenant_id,limit,offset)
    return WarehouseMaterialListResponse(data=data,page={"limit":limit,"offset":offset,"has_more":has_more})

@router.post("/material-requests/{id}/issue",response_model=DataResponse)
def issue_material_request(id:str,p:MaterialIssueRequest|None=None,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.create"))):
    key(idempotency_key)
    try:
        with r.material_command_lock(x_tenant_id,id):
            value,plan=r.prepare_warehouse_issue(x_tenant_id,id,access.actor_id)
            if not value:raise ErclaveError("maintenance_material_request_not_found","Material request not found.",status_code=404)
            if plan is None:return DataResponse(data=value)
            results=[];error=None
            try:
                for line in plan:
                    movement=a.consume(x_tenant_id,line["reservation_id"],float(line["quantity"]),authorization,f"maintenance-{value['order_id']}-consume-{line['id']}")
                    if not movement.get("id"):raise ErclaveError("maintenance_reconciliation_incomplete","Inventory did not confirm the movement.",status_code=503)
                    results.append((line["id"],movement))
            except ErclaveError as exc:error=str(exc.code)
            return DataResponse(data=r.complete_warehouse_issue(x_tenant_id,id,results,error,access.actor_id))
    except ValueError as exc:raise failure(exc) from exc

@router.post("/material-requests/{id}/reject",response_model=DataResponse)
def reject_material_request(id:str,p:MaterialRejectRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.create"))):
    k=key(idempotency_key)
    try:
        with r.material_command_lock(x_tenant_id,id):
            value=r.get_material_request(x_tenant_id,id)
            if not value:raise ErclaveError("maintenance_material_request_not_found","Material request not found.",status_code=404)
            r.record_warehouse_rejection(x_tenant_id,id,p.reason,k,digest(p,{"id":id}),access.actor_id)
            if value["status"]=="cancelled":return DataResponse(data=value)
            return DataResponse(data=cancel_material_locked(x_tenant_id,id,authorization,k,r,a,access.actor_id))
    except ValueError as exc:raise failure(exc) from exc

@router.get("/orders",response_model=ListResponse)
def orders(q:str|None=None,status:str|None=None,limit:int=Query(100,ge=1,le=200),x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),_=Depends(require_maintenance_access("maintenance.order.read"))):return ListResponse(data=r.list_orders(x_tenant_id,q,status,limit))
@router.post("/orders",response_model=DataResponse,status_code=201)
def create_order(p:OrderCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.create"))):
    snapshots={"machine_code_snapshot":None,"machine_name_snapshot":None,"source_production_order_code_snapshot":None}
    if p.production_machine_id:
        machine=a.machine(x_tenant_id,p.production_machine_id,authorization);snapshots.update({"machine_code_snapshot":machine["code"],"machine_name_snapshot":machine["name"]})
    if p.source_production_order_id:
        order=a.production_order(x_tenant_id,p.source_production_order_id,authorization)
        if order["status"] not in {"waiting_resources","in_progress"}:raise ErclaveError("production_order_not_maintenance_eligible","Production order must be waiting for resources or in progress.",status_code=409)
        if not any(x.get("resource_type")=="machine" and x.get("resource_ref_id")==p.production_machine_id for x in order.get("resources",[])):raise ErclaveError("production_machine_not_in_order","The selected machine is not assigned to the Production order.",status_code=422)
        snapshots["source_production_order_code_snapshot"]=order["code"]
    try:return DataResponse(data=r.create_order(x_tenant_id,p,snapshots,key(idempotency_key),digest(p),access.actor_id))
    except ValueError as exc:raise failure(exc) from exc
@router.get("/orders/{id}",response_model=DataResponse)
def get_order(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),_=Depends(require_maintenance_access("maintenance.order.read"))):
    value=r.get_order(x_tenant_id,id)
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return DataResponse(data=value)
@router.patch("/orders/{id}",response_model=DataResponse)
def update_order(id:str,p:OrderUpdate,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.update"))):
    try:value=r.update_order(x_tenant_id,id,p,key(idempotency_key),digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:raise failure(exc) from exc
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/orders/{id}/transitions",response_model=DataResponse)
def transition_order(id:str,p:TransitionRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access(MAINTENANCE_ORDER_ACTION_PERMISSIONS))):
    access.require(f"maintenance.order.{p.transition}")
    k=key(idempotency_key);before=r.get_order(x_tenant_id,id)
    if not before:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    worker=None
    if p.assigned_worker_id:worker=eligible_worker(a.workers(x_tenant_id,authorization),p.assigned_worker_id)
    if p.transition in {"start","resume","reopen"}:worker=eligible_worker(a.workers(x_tenant_id,authorization),before.get("assigned_worker_id"))
    if p.transition=="resolve":
        if not all(before.get(field) and str(before[field]).strip() for field in ("diagnosis","work_performed","verification_notes")):raise failure(ValueError("maintenance_resolution_evidence_required"))
        if before.get("total_minutes",0)<=0:raise failure(ValueError("maintenance_time_required"))
        if any(request["status"] not in {"issued","cancelled"} for request in before.get("material_requests",[])):raise failure(ValueError("maintenance_materials_not_reconciled"))
    if p.transition=="cancel":
        for request_value in before.get("material_requests",[]):
            if request_value["status"] not in {"issued","cancelled"}:
                cancelled=cancel_material(x_tenant_id,request_value["id"],authorization,f"{k}-cancel-{request_value['id']}",r,a,access.actor_id)
                if cancelled["status"]!="cancelled":raise failure(ValueError("maintenance_materials_not_reconciled"))
    try:value=r.transition(x_tenant_id,id,p,worker,k,digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:
        result=failure(exc);result.details={"workflow":"maintenance","requested_status":p.transition,"current_status":before["status"]};raise result from exc
    if value["production_machine_id"] and p.transition in {"request","resolve","cancel","reopen"}:value=apply_machine_integration(x_tenant_id,value,authorization,r,a,access.actor_id)
    return DataResponse(data=value)
@router.post("/orders/{id}/reconcile",response_model=DataResponse)
def reconcile_order(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.reconcile"))):
    key(idempotency_key);value=r.get_order(x_tenant_id,id)
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    if any(request.get("pending_operation") for request in value.get("material_requests",[])):raise failure(ValueError("maintenance_materials_not_reconciled"))
    if value.get("integration_operation"):value=apply_machine_integration(x_tenant_id,value,authorization,r,a,access.actor_id)
    elif value.get("integration_status")=="needs_reconciliation":value=r.set_order_integration(x_tenant_id,id,"completed",actor=access.actor_id)
    return DataResponse(data=value)
@router.get("/orders/{id}/time-entries",response_model=ListResponse)
def time_entries(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),_=Depends(require_maintenance_access("maintenance.time.read"))):
    value=r.get_order(x_tenant_id,id)
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return ListResponse(data=value["time_entries"])
@router.post("/orders/{id}/time-entries",response_model=DataResponse,status_code=201)
def create_time(id:str,p:TimeEntryCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.time.create"))):
    worker=eligible_worker(a.workers(x_tenant_id,authorization),p.worker_id)
    try:value=r.create_time(x_tenant_id,id,p,worker,key(idempotency_key),digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:raise failure(exc) from exc
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/orders/{id}/material-requests",response_model=ListResponse)
def material_requests(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),_=Depends(require_maintenance_access("maintenance.material_request.read"))):
    value=r.get_order(x_tenant_id,id)
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return ListResponse(data=value["material_requests"])
@router.post("/orders/{id}/material-requests",response_model=DataResponse,status_code=201)
def create_material_request(id:str,p:MaterialRequestCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.material_request.create"))):
    try:
        with r.material_creation_lock(x_tenant_id,id):
            return create_material_request_locked(id,p,x_tenant_id,authorization,idempotency_key,r,a,access)
    except ValueError as exc:raise failure(exc) from exc

def create_material_request_locked(id,p,x_tenant_id,authorization,idempotency_key,r,a,access):
    warehouse=a.warehouse(x_tenant_id,p.warehouse_id,authorization)
    if warehouse.get("status")!="active" or warehouse.get("type") not in {"spare_parts","spareParts"}:raise ErclaveError("spare_parts_warehouse_required","Select an active spare-parts warehouse.",status_code=422)
    items=[]
    for line in p.lines:
        item=a.item(x_tenant_id,line.item_id,authorization)
        if item.get("status")!="active" or item.get("base_unit")!=line.unit_code:raise ErclaveError("maintenance_material_invalid","Material must be active and use its base unit.",status_code=422)
        items.append(item)
    k=key(idempotency_key)
    try:request_info,plan=r.prepare_material_request(x_tenant_id,id,p,{"warehouse_name":warehouse["name"],"items":items},k,digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:raise failure(exc) from exc
    if not request_info:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    if plan is None:return DataResponse(data=request_info)
    reservations=[]
    try:
        for line in plan:reservations.append(a.reserve(x_tenant_id,id,request_info["id"],line,p.warehouse_id,authorization,f"maintenance-{request_info['id']}-reserve-{line['line_id']}"))
    except ErclaveError as exc:return DataResponse(data=r.complete_material_request(x_tenant_id,request_info["id"],k,reservations,str(exc.code),access.actor_id))
    return DataResponse(data=r.complete_material_request(x_tenant_id,request_info["id"],k,reservations,actor=access.actor_id))
@router.post("/material-requests/{id}/cancel",response_model=DataResponse)
def cancel_material_request(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.material_request.cancel"))):
    k=key(idempotency_key)
    try:value=cancel_material(x_tenant_id,id,authorization,k,r,a,access.actor_id)
    except ValueError as exc:raise failure(exc) from exc
    if not value:raise ErclaveError("maintenance_material_request_not_found","Material request not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/material-requests/{id}/reconcile",response_model=DataResponse)
def reconcile_material_request(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.material_request.reconcile"))):
    try:
        with r.material_command_lock(x_tenant_id,id):
            return reconcile_material_request_locked(id,x_tenant_id,authorization,idempotency_key,r,a,access)
    except ValueError as exc:raise failure(exc) from exc

def reconcile_material_request_locked(id,x_tenant_id,authorization,idempotency_key,r,a,access):
    k=key(idempotency_key)
    try:value,plan=r.prepare_material_reconciliation(x_tenant_id,id,k,digest(path={"id":id}),access.actor_id)
    except ValueError as exc:raise failure(exc) from exc
    if not value:raise ErclaveError("maintenance_material_request_not_found","Material request not found.",status_code=404)
    if plan is None:return DataResponse(data=value)
    results=[]
    try:
        if value["pending_operation"]=="reserve":
            for line in plan:results.append(a.reserve(x_tenant_id,value["order_id"],id,line,value["warehouse_id"],authorization,f"maintenance-{id}-reserve-{line['line_id']}"))
        else:
            for line in plan:
                a.release_reservation(x_tenant_id,line["reservation_id"],authorization,f"maintenance-{id}-release-{line['line_id']}");results.append({"id":line["reservation_id"]})
    except ErclaveError as exc:return DataResponse(data=r.complete_material_reconciliation(x_tenant_id,id,k,results,str(exc.code),access.actor_id))
    return DataResponse(data=r.complete_material_reconciliation(x_tenant_id,id,k,results,None,access.actor_id))


@router.get("/returnable-materials")
def returnable_materials(limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias="X-Tenant-Id"),repository:MaintenanceRepository=Depends(get_maintenance_repository),_=Depends(require_maintenance_access(("maintenance.material_request.create","inventory.movement.read")))):
    return {"data":repository.returnable_materials(x_tenant_id,limit,offset)}

@router.post("/material-returns/validate")
def validate_material_return(payload:MaterialReturnValidation,x_tenant_id:str=Header(alias="X-Tenant-Id"),repository:MaintenanceRepository=Depends(get_maintenance_repository),_=Depends(require_maintenance_access(("maintenance.material_request.create","inventory.movement.create")))):
    try:value=repository.validate_material_return(x_tenant_id,payload.model_dump(mode="json"))
    except ValueError as exc:raise ErclaveError(str(exc),"The order must be finished or cancelled before returning unused materials.",status_code=409) from exc
    return {"data":{"source_code":value["source_code"]}}

@router.post("/material-returns/reconcile")
def reconcile_material_return(payload:MaterialReturnReconcile,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:MaintenanceRepository=Depends(get_maintenance_repository),authority:MaterialReturnClient=Depends(get_material_return_client),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.create"))):
    key(idempotency_key)
    value=authority.get_return(x_tenant_id,payload.return_id,authorization)
    try:return {"data":repository.reconcile_material_return(x_tenant_id,value,access.actor_id)}
    except ValueError as exc:raise ErclaveError(str(exc),"Confirm the physical return in Warehouse before adjusting the order.",status_code=409) from exc
