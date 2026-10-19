import hashlib,json
from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,Header,Query
from erclave_common.errors import ErclaveError
from erclave_common.csv_reports import csv_report_response,validate_date_range
from .authorization import AuthorizedContext,require_purchasing_access
from .authorities import PurchasingAuthorityClient,get_purchasing_authority_client
from .repositories import PurchasingRepository,get_purchasing_repository
from .reports import REPORT_PERMISSIONS,build_report
from .schemas import *
from .receipt_context import ReceiptContext,receipt_proof,receipt_divisions,authorize_receipt
from .document_context import document_access,divisions_for,context_from_division,fixed_context,authorize_document,validate_document_items,check_submitted_terms
router=APIRouter(prefix="/v1/purchasing",tags=["purchasing"])
@router.get("/reference-data",response_model=PurchasingReferenceDataResponse)
def reference_data(x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client),_=Depends(require_purchasing_access(("purchasing.supplier.create","purchasing.supplier.update")))):
    return PurchasingReferenceDataResponse(data=PurchasingReferenceDataRead(
        currencies=[ReferenceOption.model_validate(item) for item in a.list_catalog(x_tenant_id,"currencies",authorization)],
        payment_terms=[ReferenceOption.model_validate(item) for item in a.list_catalog(x_tenant_id,"payment_terms",authorization)],
    ))
@router.get("/reports/{report_code}/export")
def export_report(report_code:str,lang:Literal["es","en"]="es",date_from:date|None=None,date_to:date|None=None,status:str|None=None,priority:str|None=None,q:str|None=None,currency:str|None=None,supplier_id:str|None=None,line_type:str|None=None,x_tenant_id:str=Header(alias="X-Tenant-Id"),r:PurchasingRepository=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access(tuple(REPORT_PERMISSIONS.values()))),authorization:str|None=Header(None,alias="Authorization"),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client)):
    validate_date_range(date_from,date_to);permission=REPORT_PERMISSIONS.get(report_code)
    if not permission:raise ErclaveError("report_not_found","Purchasing report does not exist.",status_code=404)
    access.require(permission)
    filters={"date_from":date_from,"date_to":date_to,"status":status,"priority":priority,"q":q,"currency":currency,"supplier_id":supplier_id,"line_type":line_type}
    if report_code!="suppliers":filters["allowed_divisions"]=divisions_for(document_access(r,a,x_tenant_id,permission,authorization,access.actor_id))
    return csv_report_response(build_report(r,x_tenant_id,report_code,filters),lang)
def key(v):
    if not v or len(v.strip())<8:raise ErclaveError("idempotency_key_required","Idempotency-Key header is required.",status_code=400)
    return v.strip()
def digest(payload=None,path=None):return hashlib.sha256(json.dumps({"body":payload.model_dump(mode="json") if payload else {},"path":path or {}},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def document_digest(actor,payload=None,path=None):return hashlib.sha256(json.dumps({'actor':actor,'request':digest(payload,path)},sort_keys=True,separators=(',',':')).encode()).hexdigest()
def fail(exc):return ErclaveError(str(exc),"Purchasing command conflicts with current state.",status_code=409)

def document_replay(r,t,operation,k,d,scope):
    try:return r.document_replay(t,operation,key(k),d,scope)
    except ValueError as exc:raise fail(exc) from exc
def validate_lines(t,lines,a,auth):
    snapshots={}
    for line in lines:
        line_type=line["line_type"] if isinstance(line,dict) else line.line_type
        unit_code=line["unit_code"] if isinstance(line,dict) else line.unit_code
        inventory_item_id=(line.get("inventory_item_ref_id") or line.get("inventory_item_id")) if isinstance(line,dict) else line.inventory_item_id
        a.require_unit(t,unit_code,auth)
        if line_type=="inventory_item":
            item=a.item(t,inventory_item_id,auth)
            if item.get("status")!="active":raise ErclaveError("inactive_inventory_item","Purchasing lines require active Inventory items.",status_code=422)
            if str(item.get("base_unit",item.get("unit",""))).upper()!=unit_code.upper():raise ErclaveError("purchase_unit_mismatch","Line unit must match Inventory base unit.",status_code=422)
            snapshots[inventory_item_id]=item
    return snapshots
def validate_warehouses(t,payload,r,a,auth):
    order=r.get_order(t,payload.purchase_order_id)
    if not order:return
    order_lines={line["id"]:line for line in order["lines"]}
    inventory_warehouses=set()
    for item in payload.lines:
        line=order_lines.get(item.order_line_id)
        if not line:continue
        if line["line_type"]=="service" and item.warehouse_id:
            raise ErclaveError("service_warehouse_not_allowed","Service receipts must not reference an Inventory warehouse.",status_code=422)
        if line["line_type"]=="inventory_item" and item.warehouse_id:inventory_warehouses.add(item.warehouse_id)
    for warehouse_id in inventory_warehouses:
        warehouse=a.warehouse(t,warehouse_id,auth)
        if warehouse.get("status")!="active":raise ErclaveError("inactive_purchase_warehouse","Purchasing receipts require active warehouses.",status_code=422)
@router.get("/suppliers",response_model=ListResponse)
def suppliers(x_tenant_id:str=Header(alias="X-Tenant-Id"),r:PurchasingRepository=Depends(get_purchasing_repository),_=Depends(require_purchasing_access("purchasing.supplier.read"))):return ListResponse(data=r.list_suppliers(x_tenant_id))
@router.post("/suppliers",response_model=DataResponse,status_code=201)
def create_supplier(p:SupplierCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.supplier.create"))):
    k=key(idempotency_key);request_digest=digest(p)
    try:replay=r.supplier_replay(x_tenant_id,k,request_digest,access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if replay:return DataResponse(data=replay)
    a.require_catalog(x_tenant_id,"currencies",p.currency,authorization); a.require_catalog(x_tenant_id,"payment_terms",p.payment_terms,authorization)
    allocation=a.allocate_code(x_tenant_id,"purchasing.supplier",p.code,authorization,k)
    try:return DataResponse(data=r.create_supplier(x_tenant_id,p.model_copy(update={"code":allocation["code"]}),k,request_digest,access.actor_id,code_mode=allocation["mode"]))
    except ValueError as exc:raise fail(exc) from exc
@router.patch("/suppliers/{id}",response_model=DataResponse)
def update_supplier(id:str,p:SupplierUpdate,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.supplier.update"))):
    before=r.get_supplier(x_tenant_id,id)
    if not before:raise ErclaveError("supplier_not_found","Supplier not found.",status_code=404)
    fiscal_fields={"legal_name","tax_id","tax_regime","billing_email","fiscal_postal_code","fiscal_country"}
    if p.model_fields_set & fiscal_fields:
        merged={name:(getattr(p,name) if name in p.model_fields_set else before.get(name)) for name in fiscal_fields}
        if not merged.get("tax_id"):raise ErclaveError("incomplete_supplier_fiscal_profile","Legal name, RFC, tax regime, billing email and fiscal postal code are required together.",status_code=422)
        try:validate_fiscal_profile(merged)
        except ValueError as exc:raise ErclaveError("incomplete_supplier_fiscal_profile","Legal name, RFC, tax regime, billing email and fiscal postal code are required together.",status_code=422) from exc
        if merged.get("fiscal_country")=="MX" and merged.get("fiscal_postal_code") and (len(merged["fiscal_postal_code"])!=5 or not merged["fiscal_postal_code"].isdigit()):raise ErclaveError("invalid_mexican_postal_code","Mexican fiscal postal code must contain five digits.",status_code=422)
    if p.currency:a.require_catalog(x_tenant_id,"currencies",p.currency,authorization)
    if p.payment_terms:a.require_catalog(x_tenant_id,"payment_terms",p.payment_terms,authorization)
    try:value=r.update_supplier(x_tenant_id,id,p,key(idempotency_key),digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("supplier_not_found","Supplier not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/requisitions",response_model=ListResponse)
def requisitions(x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.read")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):
    scope=document_access(r,a,x_tenant_id,'purchasing.requisition.read',authorization,access.actor_id)
    return ListResponse(data=r.list_requisitions(x_tenant_id,allowed_divisions=divisions_for(scope)))
@router.post("/requisitions",response_model=DataResponse,status_code=201)
def create_requisition(p:RequisitionCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.create"))):
    scope=document_access(r,a,x_tenant_id,'purchasing.requisition.create',authorization,access.actor_id)
    request_digest=document_digest(access.actor_id,p)
    replay=document_replay(r,x_tenant_id,'requisition.create',idempotency_key,request_digest,scope)
    if replay:return DataResponse(data=replay)
    context=context_from_division(scope,p.division_ref_id)
    validate_document_items(x_tenant_id,p.lines,context,a,authorization)
    snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    allocation=a.allocate_code(x_tenant_id,"purchasing.requisition",p.code,authorization,key(idempotency_key))
    try:return DataResponse(data=r.create_requisition(x_tenant_id,p.model_copy(update={"code":allocation["code"]}),key(idempotency_key),request_digest,access.actor_id,snapshots,context=context,organization_access=scope,code_mode=allocation["mode"]))
    except ValueError as exc:raise fail(exc) from exc
@router.patch("/requisitions/{id}",response_model=DataResponse)
def update_requisition(id:str,p:RequisitionWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.update"))):
    scope=document_access(r,a,x_tenant_id,'purchasing.requisition.update',authorization,access.actor_id)
    current=r.get_requisition(x_tenant_id,id)
    if not current:raise ErclaveError('requisition_not_found','Requisition not found.',status_code=404)
    context=fixed_context(current,p.division_ref_id,scope)
    request_digest=document_digest(access.actor_id,p,{'id':id})
    replay=document_replay(r,x_tenant_id,'requisition.update',idempotency_key,request_digest,scope)
    if replay:return DataResponse(data=replay)
    validate_document_items(x_tenant_id,p.lines,context,a,authorization)
    snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    try:value=r.update_requisition(x_tenant_id,id,p,key(idempotency_key),request_digest,access.actor_id,snapshots,organization_access=scope)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("requisition_not_found","Requisition not found.",status_code=404)
    return DataResponse(data=value)
def transition(id,target,reason,t,k,r,access,a,authorization):
    scope=document_access(r,a,t,'purchasing.requisition.'+{'submitted':'submit','approved':'approve','rejected':'reject'}[target],authorization,access.actor_id)
    current=r.get_requisition(t,id)
    authorize_document(current,scope)
    request_digest=document_digest(access.actor_id,path={"id":id,"target":target,"reason":reason})
    replay=document_replay(r,t,'requisition.'+target,k,request_digest,scope)
    if replay:return DataResponse(data=replay)
    try:value=r.transition_requisition(t,id,target,reason,key(k),request_digest,access.actor_id,organization_access=scope)
    except ValueError as exc:
        result=fail(exc);result.details={"workflow":"requisition","requested_status":target};raise result from exc
    if not value:raise ErclaveError("requisition_not_found","Requisition not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/requisitions/{id}/submit",response_model=DataResponse)
def submit(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.submit")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):return transition(id,"submitted",None,x_tenant_id,idempotency_key,r,access,a,authorization)
@router.post("/requisitions/{id}/approve",response_model=DataResponse)
def approve(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.approve")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):return transition(id,"approved",None,x_tenant_id,idempotency_key,r,access,a,authorization)
@router.post("/requisitions/{id}/reject",response_model=DataResponse)
def reject(id:str,p:ReasonRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.reject")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):return transition(id,"rejected",p.reason,x_tenant_id,idempotency_key,r,access,a,authorization)
@router.post("/requisitions/{id}/cancel",response_model=DataResponse)
def cancel_requisition(id:str,p:ReasonRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.cancel")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):
    scope=document_access(r,a,x_tenant_id,'purchasing.requisition.cancel',authorization,access.actor_id)
    current=r.get_requisition(x_tenant_id,id)
    authorize_document(current,scope,legacy=True,active=False)
    request_digest=document_digest(access.actor_id,p,{'id':id}) if current and current.get('organization_context') else digest(p,{'id':id})
    try:value=r.cancel_requisition(x_tenant_id,id,p.reason,key(idempotency_key),request_digest,access.actor_id,organization_access=scope)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("requisition_not_found","Requisition not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/orders",response_model=ListResponse)
def orders(x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.read")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):
    scope=document_access(r,a,x_tenant_id,'purchasing.order.read',authorization,access.actor_id)
    return ListResponse(data=r.list_orders(x_tenant_id,allowed_divisions=divisions_for(scope)))
@router.post("/orders",response_model=DataResponse,status_code=201)
def create_order(p:PurchaseOrderCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.create"))):
    scope=document_access(r,a,x_tenant_id,'purchasing.order.create',authorization,access.actor_id)
    request_digest=document_digest(access.actor_id,p)
    replay=document_replay(r,x_tenant_id,'order.create',idempotency_key,request_digest,scope)
    if replay:return DataResponse(data=replay)
    if p.requisition_id:
        req=r.get_requisition(x_tenant_id,p.requisition_id)
        if not req:raise ErclaveError('requisition_not_found','Requisition not found.',status_code=404)
        context=fixed_context(req,p.division_ref_id,scope)
    else:context=context_from_division(scope,p.division_ref_id)
    terms=r.get_document_terms(x_tenant_id,p.supplier_id,context);check_submitted_terms(p,terms)
    a.require_catalog(x_tenant_id,'currencies',terms['values']['currency'],authorization);a.require_catalog(x_tenant_id,'payment_terms',terms['values']['payment_terms'],authorization)
    validate_document_items(x_tenant_id,p.lines,context,a,authorization)
    snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    allocation=a.allocate_code(x_tenant_id,"purchasing.order",p.code,authorization,key(idempotency_key))
    try:return DataResponse(data=r.create_order(x_tenant_id,p.model_copy(update={"code":allocation["code"]}),key(idempotency_key),request_digest,access.actor_id,snapshots,context=context,terms=terms,organization_access=scope,code_mode=allocation["mode"]))
    except ValueError as exc:raise fail(exc) from exc
@router.patch("/orders/{id}",response_model=DataResponse)
def update_order(id:str,p:PurchaseOrderWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.update"))):
    scope=document_access(r,a,x_tenant_id,'purchasing.order.update',authorization,access.actor_id)
    current=r.get_order(x_tenant_id,id)
    if not current:raise ErclaveError('order_not_found','Purchase order not found.',status_code=404)
    context=fixed_context(current,p.division_ref_id,scope)
    request_digest=document_digest(access.actor_id,p,{'id':id})
    replay=document_replay(r,x_tenant_id,'order.update',idempotency_key,request_digest,scope)
    if replay:return DataResponse(data=replay)
    if current['requisition_id']!=p.requisition_id:raise fail(ValueError('order_origin_locked'))
    terms=current['commercial_terms_snapshot'] if current['supplier_id']==p.supplier_id else r.get_document_terms(x_tenant_id,p.supplier_id,context)
    check_submitted_terms(p,terms)
    if current['supplier_id']!=p.supplier_id:
        a.require_catalog(x_tenant_id,'currencies',terms['values']['currency'],authorization)
        a.require_catalog(x_tenant_id,'payment_terms',terms['values']['payment_terms'],authorization)
    validate_document_items(x_tenant_id,p.lines,context,a,authorization)
    snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    try:value=r.update_order(x_tenant_id,id,p,key(idempotency_key),request_digest,access.actor_id,snapshots,terms=terms,organization_access=scope)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/orders/{id}/issue",response_model=DataResponse)
def issue(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.issue"))):
    k=key(idempotency_key);request_digest=document_digest(access.actor_id,path={"id":id})
    current=r.get_order(x_tenant_id,id)
    if not current:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    scope=document_access(r,a,x_tenant_id,'purchasing.order.issue',authorization,access.actor_id)
    authorize_document(current,scope)
    replay=document_replay(r,x_tenant_id,'order.issue',idempotency_key,request_digest,scope)
    if replay:return DataResponse(data=replay)
    if current["status"]=="draft":
        a.require_catalog(x_tenant_id,'currencies',current['currency'],authorization)
        a.require_catalog(x_tenant_id,'payment_terms',current['payment_terms'],authorization)
        validate_document_items(x_tenant_id,current['lines'],current['organization_context'],a,authorization)
        validate_lines(x_tenant_id,current["lines"],a,authorization)
    try:value=r.issue_order(x_tenant_id,id,k,request_digest,access.actor_id,organization_access=scope)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/orders/{id}/cancel",response_model=DataResponse)
def cancel_order(id:str,p:ReasonRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.cancel")),authorization:str|None=Header(None,alias="Authorization"),a=Depends(get_purchasing_authority_client)):
    scope=document_access(r,a,x_tenant_id,'purchasing.order.cancel',authorization,access.actor_id)
    current=r.get_order(x_tenant_id,id)
    authorize_document(current,scope,legacy=True,active=False)
    request_digest=document_digest(access.actor_id,p,{'id':id}) if current and current.get('organization_context') else digest(p,{'id':id})
    try:value=r.cancel_order(x_tenant_id,id,p.reason,key(idempotency_key),request_digest,access.actor_id,organization_access=scope)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/receipts",response_model=ListResponse)
def receipts(x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.receipt.read")),authorization:str|None=Header(None,alias="Authorization"),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client)):
    divisions=receipt_divisions(r,a,x_tenant_id,"purchasing.receipt.read",authorization,access.actor_id)
    return ListResponse(data=r.list_receipts(x_tenant_id,allowed_divisions=divisions))
@router.post("/receipts",response_model=DataResponse,status_code=201)
def create_receipt(p:ReceiptCreate,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.receipt.create"))):
    k=key(idempotency_key)
    try:replay=r.receipt_replay(x_tenant_id,k,digest(p),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if replay:
        authorize_receipt(r,a,x_tenant_id,replay,"purchasing.receipt.create",authorization,access.actor_id)
        return DataResponse(data=replay)
    snapshots=ReceiptContext(r,a).prepare(x_tenant_id,p,authorization,access.actor_id)
    validate_warehouses(x_tenant_id,p,r,a,authorization)
    scope=document_access(r,a,x_tenant_id,'purchasing.receipt.create',authorization,access.actor_id)
    allocation=a.allocate_code(x_tenant_id,"purchasing.receipt",p.code,authorization,k)
    try:receipt,plan=r.prepare_receipt(x_tenant_id,p.model_copy(update={"code":allocation["code"]}),k,digest(p),access.actor_id,snapshots,organization_access=scope,code_mode=allocation["mode"])
    except ValueError as exc:raise fail(exc) from exc
    if not receipt:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    if plan is None:
        authorize_receipt(r,a,x_tenant_id,receipt,'purchasing.receipt.create',authorization,access.actor_id)
        return DataResponse(data=receipt)
    return DataResponse(data=receipt)
@router.get("/receipts/{receipt_id}/lines/{line_id}/inventory-proof",response_model=DataResponse)
def inventory_receipt_proof(receipt_id:str,line_id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),r=Depends(get_purchasing_repository),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("inventory.movement.create"))):
    return DataResponse(data=receipt_proof(r,a,x_tenant_id,receipt_id,line_id,authorization,access.actor_id))
@router.post("/receipts/{id}/reconcile",response_model=DataResponse)
def reconcile_receipt(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access(("purchasing.receipt.reconcile","inventory.movement.create")))):
    permissions=access.permissions or frozenset({access.permission})
    if "inventory.movement.create" not in permissions:
        raise ErclaveError("purchase_warehouse_receipt_required","Warehouse must confirm or reconcile physical receipt in Movements.",status_code=403)
    return confirm_receipt_lines(id,"inventory_item",x_tenant_id,authorization,idempotency_key,r,a,access)


def confirm_receipt_lines(id,line_type,tenant,authorization,idempotency_key,r,a,access):
    k=key(idempotency_key)
    with r.receipt_command_lock(tenant,id):
        current=r.get_receipt(tenant,id)
        if not current:raise ErclaveError("receipt_not_found","Receipt not found.",status_code=404)
        permission="inventory.movement.create" if line_type=="inventory_item" else ("purchasing.requisition.create","purchasing.order.create")
        authorize_receipt(r,a,tenant,current,permission,authorization,access.actor_id)
        if line_type=="service":r.require_service_requester(tenant,id,access.actor_id)
        try:receipt,plan=r.prepare_reconciliation(tenant,id,k,digest(path={"id":id,"line_type":line_type}),access.actor_id)
        except ValueError as exc:raise fail(exc) from exc
        if not receipt:raise ErclaveError("receipt_not_found","Receipt not found.",status_code=404)
        if plan is None:return DataResponse(data=receipt)
        plan=[line for line in plan if line["line_type"]==line_type]
        movements=[];dependency_error=None
        for line in plan:
            if dependency_error:movements.append(None);continue
            try:
                if line_type=="service":movements.append({"id":None})
                else:
                    movement=a.receive(tenant,line,receipt["id"],receipt["purchase_order_id"],authorization,line["inventory_idempotency_key"])
                    if not movement.get("id"):raise ErclaveError("inventory_response_incomplete","Inventory did not confirm a movement.",status_code=502)
                    movements.append(movement)
            except ErclaveError as exc:dependency_error=exc.code;movements.append(None)
        return DataResponse(data=r.complete_receipt(tenant,receipt,plan,movements,k,access.actor_id,dependency_error,"receipt.reconcile"))


@router.get("/warehouse-receipts",response_model=ListResponse)
def warehouse_receipts(limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("inventory.movement.read")),authorization:str|None=Header(None,alias="Authorization"),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client)):
    divisions=receipt_divisions(r,a,x_tenant_id,"inventory.movement.read",authorization,access.actor_id)
    return ListResponse(data=r.list_pending_receipts(x_tenant_id,"inventory_item",limit=limit,offset=offset,allowed_divisions=divisions))

@router.get("/service-acceptances",response_model=ListResponse)
def service_acceptances(limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access(("purchasing.requisition.create","purchasing.order.create"))),authorization:str|None=Header(None,alias="Authorization"),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client)):
    divisions=receipt_divisions(r,a,x_tenant_id,("purchasing.requisition.create","purchasing.order.create"),authorization,access.actor_id)
    return ListResponse(data=r.list_pending_receipts(x_tenant_id,"service",access.actor_id,limit,offset,allowed_divisions=divisions))

@router.post("/receipts/{id}/accept-services",response_model=DataResponse)
def accept_receipt_services(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access(("purchasing.requisition.create","purchasing.order.create")))):
    return confirm_receipt_lines(id,"service",x_tenant_id,authorization,idempotency_key,r,a,access)
