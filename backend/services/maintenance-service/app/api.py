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
from .inventory_context import material_context, guard_material, material_divisions, PROOF_PERMISSIONS
from .document_context import authorize_order,create_context,divisions_for,validate_worker,labor_snapshot
from erclave_common.operational_context import society_currency

router=APIRouter(prefix="/v1/maintenance",tags=["maintenance"])
@router.get('/document-divisions',operation_id='listMaintenanceDocumentDivisions')
def document_divisions(q:str=Query('',max_length=240),limit:int=Query(20,ge=1,le=25),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access('maintenance.order.create'))):
    scope=a.organization_access(x_tenant_id,'maintenance.order.create',authorization,access.actor_id)
    rows=[{key:row[key] for key in ('id','code','name','society_id')}|{'cost_currency':society_currency(scope,row['society_id'])} for row in scope.divisions if q.casefold() in (row['code']+' '+row['name']).casefold()]
    rows.sort(key=lambda row:(row['code'],row['id']))
    return {'data':rows[offset:offset+limit],'meta':{'total':len(rows),'limit':limit,'offset':offset}}
@router.get("/reports/{report_code}/export")
def export_report(report_code:str,lang:Literal["es","en"]="es",date_from:date|None=None,date_to:date|None=None,status:str|None=None,priority:str|None=None,q:str|None=None,target_type:str|None=None,responsible_worker_id:str|None=None,worker_id:str|None=None,warehouse_id:str|None=None,x_tenant_id:str=Header(alias="X-Tenant-Id"),r:MaintenanceRepository=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access(tuple(REPORT_PERMISSIONS.values()))),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client)):
    validate_date_range(date_from,date_to);permission=REPORT_PERMISSIONS.get(report_code)
    if not permission:raise ErclaveError("report_not_found","Maintenance report does not exist.",status_code=404)
    access.require(permission)
    filters={"date_from":date_from,"date_to":date_to,"status":status,"priority":priority,"q":q,"target_type":target_type,"responsible_worker_id":responsible_worker_id,"worker_id":worker_id,"warehouse_id":warehouse_id}
    filters['divisions']=divisions_for(a.organization_access(x_tenant_id,permission,authorization,access.actor_id))
    return csv_report_response(build_report(r,x_tenant_id,report_code,filters),lang)
MAINTENANCE_ORDER_ACTION_PERMISSIONS=tuple(f"maintenance.order.{action}" for action in ("request","assign","start","wait_for_parts","resume","resolve","close","reopen","cancel"))
def tenant(v):
    if not v:raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
    return v
def key(v):
    if not v or len(v.strip())<8:raise ErclaveError("idempotency_key_required","Idempotency-Key header is required.",status_code=400)
    return v.strip()
def digest(p=None,path=None):return hashlib.sha256(json.dumps({"body":p.model_dump(mode="json") if p else {},"path":path or {}},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def document_digest(actor,p=None,path=None):return hashlib.sha256(json.dumps({'actor':actor,'request':digest(p,path)},sort_keys=True,separators=(',',':')).encode()).hexdigest()
def replay_document(r,t,operation,k,h,scope,legacy=False):
    try:return r.document_replay(t,operation,k,h,scope,legacy=legacy)
    except ValueError as exc:raise failure(exc) from exc
def order_scope(r,a,t,id,permission,authorization,actor,legacy=False,active=True):
    scope=a.organization_access(t,permission,authorization,actor)
    order=r.get_order(t,id)
    if not order:raise ErclaveError('maintenance_order_not_found','Maintenance order not found.',status_code=404)
    authorize_order(order,scope,legacy=legacy,active=active)
    return order,scope
def scoped_worker(a,t,context,worker_id,authorization,field='assigned_worker_id'):
    workers=a.division_workers(t,context['division_ref_id'],authorization,worker_id=worker_id,limit=1)
    worker=next((row for row in workers if row['id']==worker_id),None)
    return validate_worker(worker,context,worker_id,field)
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
    guard_material(r.get_material_request(tenant_id,request_id),tenant_id,authorization,('maintenance.material_request.cancel','maintenance.order.cancel','inventory.movement.create'),actor,active=False)
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
def warehouse_material_requests(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias='Authorization'),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.read"))):
    divisions=material_divisions(r,x_tenant_id,authorization,'inventory.movement.read',access.actor_id)
    data,has_more=r.list_warehouse_material_requests(x_tenant_id,limit,offset,divisions=divisions)
    return WarehouseMaterialListResponse(data=data,page={"limit":limit,"offset":offset,"has_more":has_more})

@router.post("/material-requests/{id}/issue",response_model=DataResponse)
def issue_material_request(id:str,p:MaterialIssueRequest|None=None,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.create"))):
    key(idempotency_key)
    guard_material(r.get_material_request(x_tenant_id,id),x_tenant_id,authorization,'inventory.movement.create',access.actor_id)
    try:
        with r.material_command_lock(x_tenant_id,id):
            value,plan=r.prepare_warehouse_issue(x_tenant_id,id,access.actor_id,key(idempotency_key),digest(path={'id':id}))
            if not value:raise ErclaveError("maintenance_material_request_not_found","Material request not found.",status_code=404)
            if plan is None:return DataResponse(data=value)
            results=[];error=None
            try:
                for line in plan:
                    movement=a.consume(x_tenant_id,line["reservation_id"],float(line["quantity"]),authorization,f"maintenance-{value['order_id']}-consume-{line['id']}")
                    if not movement.get("id"):raise ErclaveError("maintenance_reconciliation_incomplete","Inventory did not confirm the movement.",status_code=503)
                    results.append((line["id"],movement))
            except ErclaveError as exc:error=str(exc.code)
            return DataResponse(data=r.complete_warehouse_issue(x_tenant_id,id,results,error,access.actor_id,key(idempotency_key)))
    except ValueError as exc:raise failure(exc) from exc

@router.post("/material-requests/{id}/reject",response_model=DataResponse)
def reject_material_request(id:str,p:MaterialRejectRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.create"))):
    k=key(idempotency_key)
    guard_material(r.get_material_request(x_tenant_id,id),x_tenant_id,authorization,'inventory.movement.create',access.actor_id,active=False)
    try:
        with r.material_command_lock(x_tenant_id,id):
            value=r.get_material_request(x_tenant_id,id)
            if not value:raise ErclaveError("maintenance_material_request_not_found","Material request not found.",status_code=404)
            r.record_warehouse_rejection(x_tenant_id,id,p.reason,k,digest(p,{"id":id}),access.actor_id)
            if value["status"]=="cancelled":return DataResponse(data=value)
            return DataResponse(data=cancel_material_locked(x_tenant_id,id,authorization,k,r,a,access.actor_id))
    except ValueError as exc:raise failure(exc) from exc

@router.get("/orders",response_model=ListResponse)
def orders(q:str|None=None,status:str|None=None,limit:int=Query(100,ge=1,le=200),x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.read")),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client)):
    scope=a.organization_access(x_tenant_id,'maintenance.order.read',authorization,access.actor_id)
    return ListResponse(data=r.list_orders(x_tenant_id,q,status,limit,divisions=divisions_for(scope)))
@router.post("/orders",response_model=DataResponse,status_code=201)
def create_order(p:OrderCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.create"))):
    scope=a.organization_access(x_tenant_id,'maintenance.order.create',authorization,access.actor_id)
    k=key(idempotency_key);h=document_digest(access.actor_id,p)
    replay=replay_document(r,x_tenant_id,'order.create',k,h,scope)
    if replay:return DataResponse(data=replay)
    machine=source=None
    snapshots={"machine_code_snapshot":None,"machine_name_snapshot":None,"source_production_order_code_snapshot":None}
    if p.production_machine_id:
        machine=a.machine(x_tenant_id,p.production_machine_id,authorization);snapshots.update({"machine_code_snapshot":machine["code"],"machine_name_snapshot":machine["name"]})
    if p.source_production_order_id:
        order=a.production_order(x_tenant_id,p.source_production_order_id,authorization)
        source=order
        if order["status"] not in {"waiting_resources","in_progress"}:raise ErclaveError("production_order_not_maintenance_eligible","Production order must be waiting for resources or in progress.",status_code=409)
        if not any(x.get("resource_type")=="machine" and x.get("resource_ref_id")==p.production_machine_id for x in order.get("resources",[])):raise ErclaveError("production_machine_not_in_order","The selected machine is not assigned to the Production order.",status_code=422)
        snapshots["source_production_order_code_snapshot"]=order["code"]
    snapshots['organization_context']=create_context(p,scope,machine,source)
    allocation=a.allocate_order_code(x_tenant_id,p.code,authorization,f"maintenance-order:{access.actor_id}:{k}")
    snapshots['code_mode']=allocation['mode']
    stored=p.model_copy(update={'code':allocation['code']})
    try:return DataResponse(data=r.create_order(x_tenant_id,stored,snapshots,k,h,access.actor_id,organization_access=scope))
    except ValueError as exc:raise failure(exc) from exc
@router.get("/orders/{id}",response_model=DataResponse)
def get_order(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.read")),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client)):
    value,_=order_scope(r,a,x_tenant_id,id,'maintenance.order.read',authorization,access.actor_id,legacy=True,active=False)
    return DataResponse(data=value)
@router.patch("/orders/{id}",response_model=DataResponse)
def update_order(id:str,p:OrderUpdate,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.update")),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client)):
    _,scope=order_scope(r,a,x_tenant_id,id,'maintenance.order.update',authorization,access.actor_id)
    try:value=r.update_order(x_tenant_id,id,p,key(idempotency_key),document_digest(access.actor_id,p,{"id":id}),access.actor_id,organization_access=scope)
    except ValueError as exc:raise failure(exc) from exc
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/orders/{id}/transitions",response_model=DataResponse)
def transition_order(id:str,p:TransitionRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access(MAINTENANCE_ORDER_ACTION_PERMISSIONS))):
    try:
        with r.material_creation_lock(x_tenant_id,id):
            return transition_order_locked(id,p,x_tenant_id,authorization,idempotency_key,r,a,access)
    except ValueError as exc:raise failure(exc) from exc

def transition_order_locked(id,p,x_tenant_id,authorization,idempotency_key,r,a,access):
    access.require(f"maintenance.order.{p.transition}")
    k=key(idempotency_key)
    before,scope=order_scope(r,a,x_tenant_id,id,f'maintenance.order.{p.transition}',authorization,access.actor_id,legacy=p.transition=='cancel',active=p.transition!='cancel')
    h=document_digest(access.actor_id,p,{'id':id}) if before.get('organization_context') else digest(p,{'id':id})
    replay,applied=r.prepare_order_transition(x_tenant_id,id,k,h,access.actor_id)
    if applied:
        if applied=='pending' and before.get('integration_operation'):apply_machine_integration(x_tenant_id,before,authorization,r,a,access.actor_id)
        return DataResponse(data=r.complete_order_transition(x_tenant_id,id,k,h,access.actor_id))
    worker=None
    if p.transition=='assign':worker=scoped_worker(a,x_tenant_id,before['organization_context'],p.assigned_worker_id,authorization)
    if p.transition in {"start","resume","reopen"}:worker=scoped_worker(a,x_tenant_id,before['organization_context'],before.get("assigned_worker_id"),authorization)
    if p.transition=="resolve":
        if not all(before.get(field) and str(before[field]).strip() for field in ("diagnosis","work_performed","verification_notes")):raise failure(ValueError("maintenance_resolution_evidence_required"))
        if before.get("total_minutes",0)<=0:raise failure(ValueError("maintenance_time_required"))
        if any(request["status"] not in {"issued","cancelled"} for request in before.get("material_requests",[])):raise failure(ValueError("maintenance_materials_not_reconciled"))
    if p.transition=="cancel":
        for request_value in before.get("material_requests",[]):
            if request_value["status"] not in {"issued","cancelled"}:
                cancelled=cancel_material_locked(x_tenant_id,request_value["id"],authorization,f"{k}-cancel-{request_value['id']}",r,a,access.actor_id)
                if cancelled["status"]!="cancelled":raise failure(ValueError("maintenance_materials_not_reconciled"))
    try:value=r.transition(x_tenant_id,id,p,worker,k,h,access.actor_id,organization_access=scope)
    except ValueError as exc:
        result=failure(exc);result.details={"workflow":"maintenance","requested_status":p.transition,"current_status":before["status"]};raise result from exc
    if value["production_machine_id"] and p.transition in {"request","resolve","cancel","reopen"}:value=apply_machine_integration(x_tenant_id,value,authorization,r,a,access.actor_id)
    return DataResponse(data=r.complete_order_transition(x_tenant_id,id,k,h,access.actor_id))
@router.post("/orders/{id}/reconcile",response_model=DataResponse)
def reconcile_order(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.order.reconcile"))):
    try:
        with r.material_creation_lock(x_tenant_id,id):
            return reconcile_order_locked(id,x_tenant_id,authorization,idempotency_key,r,a,access)
    except ValueError as exc:raise failure(exc) from exc

def reconcile_order_locked(id,x_tenant_id,authorization,idempotency_key,r,a,access):
    k=key(idempotency_key);value,_=order_scope(r,a,x_tenant_id,id,'maintenance.order.reconcile',authorization,access.actor_id,legacy=True)
    if any(request.get("pending_operation") for request in value.get("material_requests",[])):raise failure(ValueError("maintenance_materials_not_reconciled"))
    try:value,replay=r.prepare_order_reconciliation(x_tenant_id,id,k,digest(path={'id':id}),access.actor_id)
    except ValueError as exc:raise failure(exc) from exc
    if replay:return DataResponse(data=value)
    if value.get("integration_operation"):value=apply_machine_integration(x_tenant_id,value,authorization,r,a,access.actor_id)
    elif value.get("integration_status")=="needs_reconciliation":value=r.set_order_integration(x_tenant_id,id,"completed",actor=access.actor_id)
    return DataResponse(data=r.complete_order_reconciliation(x_tenant_id,id,k,access.actor_id))
@router.get("/orders/{id}/time-entries",response_model=ListResponse)
def time_entries(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.time.read")),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client)):
    value,_=order_scope(r,a,x_tenant_id,id,'maintenance.time.read',authorization,access.actor_id,legacy=True,active=False)
    return ListResponse(data=value["time_entries"])
@router.post("/orders/{id}/time-entries",response_model=DataResponse,status_code=201)
def create_time(id:str,p:TimeEntryCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.time.create"))):
    order,scope=order_scope(r,a,x_tenant_id,id,'maintenance.time.create',authorization,access.actor_id)
    k=key(idempotency_key);h=document_digest(access.actor_id,p,{'id':id})
    replay=replay_document(r,x_tenant_id,'time.create',k,h,scope)
    if replay:return DataResponse(data=replay)
    worker=scoped_worker(a,x_tenant_id,order['organization_context'],p.worker_id,authorization,'worker_id')
    labor_snapshot(worker,order['organization_context'],p)
    try:value=r.create_time(x_tenant_id,id,p,worker,k,h,access.actor_id,organization_access=scope)
    except ValueError as exc:raise failure(exc) from exc
    if not value:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/orders/{id}/material-requests",response_model=ListResponse)
def material_requests(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.material_request.read")),authorization:str|None=Header(None,alias='Authorization'),a=Depends(get_maintenance_authority_client)):
    value,_=order_scope(r,a,x_tenant_id,id,'maintenance.material_request.read',authorization,access.actor_id,legacy=True,active=False)
    return ListResponse(data=value["material_requests"])
@router.post("/orders/{id}/material-requests",response_model=DataResponse,status_code=201)
def create_material_request(id:str,p:MaterialRequestCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r:MaintenanceRepository=Depends(get_maintenance_repository),a:MaintenanceAuthorityClient=Depends(get_maintenance_authority_client),access:AuthorizedContext=Depends(require_maintenance_access("maintenance.material_request.create"))):
    try:
        with r.material_creation_lock(x_tenant_id,id):
            return create_material_request_locked(id,p,x_tenant_id,authorization,idempotency_key,r,a,access)
    except ValueError as exc:raise failure(exc) from exc

def create_material_request_locked(id,p,x_tenant_id,authorization,idempotency_key,r,a,access):
    scope=a.organization_access(x_tenant_id,'maintenance.material_request.create',authorization,access.actor_id)
    current=r.get_order(x_tenant_id,id)
    if current and current.get('organization_context'):authorize_order(current,scope)
    h=document_digest(access.actor_id,p,{'id':id}) if current and current.get('organization_context') else digest(p,{'id':id})
    replay=replay_document(r,x_tenant_id,'material_request.create',key(idempotency_key),h,scope,legacy=True)
    if replay:return DataResponse(data=replay)
    order,scope=order_scope(r,a,x_tenant_id,id,'maintenance.material_request.create',authorization,access.actor_id)
    warehouse=a.warehouse(x_tenant_id,p.warehouse_id,authorization)
    if warehouse.get("status")!="active" or warehouse.get("type") not in {"spare_parts","spareParts"}:raise ErclaveError("spare_parts_warehouse_required","Select an active spare-parts warehouse.",status_code=422)
    items=[]
    for line in p.lines:
        item=a.item(x_tenant_id,line.item_id,authorization)
        if item.get("status")!="active" or item.get("base_unit")!=line.unit_code:raise ErclaveError("maintenance_material_invalid","Material must be active and use its base unit.",status_code=422)
        items.append(item)
    k=key(idempotency_key)
    context=material_context(warehouse,order,a,x_tenant_id,authorization,access.actor_id)
    try:request_info,plan=r.prepare_material_request(x_tenant_id,id,p,{"warehouse_name":warehouse["name"],"items":items,"organization_context":context},k,h,access.actor_id,organization_access=scope)
    except ValueError as exc:raise failure(exc) from exc
    if not request_info:raise ErclaveError("maintenance_order_not_found","Maintenance order not found.",status_code=404)
    guard_material(request_info,x_tenant_id,authorization,'maintenance.material_request.create',access.actor_id)
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
    guard_material(r.get_material_request(x_tenant_id,id),x_tenant_id,authorization,'maintenance.material_request.reconcile',access.actor_id)
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


@router.get('/orders/{id}/inventory-context',response_model=DataResponse)
def inventory_context(id:str,line_id:str=Query(min_length=1,max_length=40),x_tenant_id:str=Header(alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),r=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access(PROOF_PERMISSIONS))):
    value=r.inventory_context(x_tenant_id,id,line_id)
    guard_material(value,x_tenant_id,authorization,PROOF_PERMISSIONS,access.actor_id,active=False)
    return DataResponse(data=value)


@router.get("/returnable-materials")
def returnable_materials(limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias='Authorization'),repository:MaintenanceRepository=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access(("maintenance.material_request.create","inventory.movement.read")))):
    divisions=material_divisions(repository,x_tenant_id,authorization,('maintenance.material_request.create','inventory.movement.read'),access.actor_id)
    return {"data":repository.returnable_materials(x_tenant_id,limit,offset,divisions=divisions)}

@router.post("/material-returns/validate")
def validate_material_return(payload:MaterialReturnValidation,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias='Authorization'),repository:MaintenanceRepository=Depends(get_maintenance_repository),access:AuthorizedContext=Depends(require_maintenance_access(("maintenance.material_request.create","inventory.movement.create")))):
    try:value=repository.validate_material_return(x_tenant_id,payload.model_dump(mode="json"))
    except ValueError as exc:raise ErclaveError(str(exc),"The order must be finished or cancelled before returning unused materials.",status_code=409) from exc
    guard_material(value,x_tenant_id,authorization,('maintenance.material_request.create','inventory.movement.create'),access.actor_id,active=False)
    cost=value.get('unit_cost_snapshot')
    return {"data":{"source_code":value["source_code"],"organization_context":value.get('organization_context'),"unit_cost_snapshot":str(cost) if cost is not None else None}}

@router.post("/material-returns/reconcile")
def reconcile_material_return(payload:MaterialReturnReconcile,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:MaintenanceRepository=Depends(get_maintenance_repository),authority:MaterialReturnClient=Depends(get_material_return_client),access:AuthorizedContext=Depends(require_maintenance_access("inventory.movement.create"))):
    k=key(idempotency_key)
    value=authority.get_return(x_tenant_id,payload.return_id,authorization)
    guard_material(value,x_tenant_id,authorization,'inventory.movement.create',access.actor_id,active=False)
    try:
        with repository.material_creation_lock(x_tenant_id,value['source_id']):
            replay=repository.prepare_material_return_reconciliation(x_tenant_id,k,digest(payload),access.actor_id)
            if replay:return {"data":replay}
            result=repository.reconcile_material_return(x_tenant_id,value,access.actor_id)
            return {"data":repository.complete_material_return_reconciliation(x_tenant_id,k,value,result)}
    except ValueError as exc:raise ErclaveError(str(exc),"Confirm the physical return in Warehouse before adjusting the order.",status_code=409) from exc
