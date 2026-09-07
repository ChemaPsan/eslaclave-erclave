import hashlib,json
from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,Header
from erclave_common.errors import ErclaveError
from erclave_common.csv_reports import csv_report_response,validate_date_range
from .authorization import AuthorizedContext,require_purchasing_access
from .authorities import PurchasingAuthorityClient,get_purchasing_authority_client
from .repositories import PurchasingRepository,get_purchasing_repository
from .reports import REPORT_PERMISSIONS,build_report
from .schemas import *
router=APIRouter(prefix="/v1/purchasing",tags=["purchasing"])
@router.get("/reports/{report_code}/export")
def export_report(report_code:str,lang:Literal["es","en"]="es",date_from:date|None=None,date_to:date|None=None,status:str|None=None,priority:str|None=None,q:str|None=None,currency:str|None=None,supplier_id:str|None=None,line_type:str|None=None,x_tenant_id:str=Header(alias="X-Tenant-Id"),r:PurchasingRepository=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access(tuple(REPORT_PERMISSIONS.values())))):
    validate_date_range(date_from,date_to);permission=REPORT_PERMISSIONS.get(report_code)
    if not permission:raise ErclaveError("report_not_found","Purchasing report does not exist.",status_code=404)
    access.require(permission)
    filters={"date_from":date_from,"date_to":date_to,"status":status,"priority":priority,"q":q,"currency":currency,"supplier_id":supplier_id,"line_type":line_type}
    return csv_report_response(build_report(r,x_tenant_id,report_code,filters),lang)
def key(v):
    if not v or len(v.strip())<8:raise ErclaveError("idempotency_key_required","Idempotency-Key header is required.",status_code=400)
    return v.strip()
def digest(payload=None,path=None):return hashlib.sha256(json.dumps({"body":payload.model_dump(mode="json") if payload else {},"path":path or {}},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def fail(exc):return ErclaveError(str(exc),"Purchasing command conflicts with current state.",status_code=409)
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
def create_supplier(p:SupplierWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.supplier.create"))):
    a.require_catalog(x_tenant_id,"currencies",p.currency,authorization); a.require_catalog(x_tenant_id,"payment_terms",p.payment_terms,authorization)
    try:return DataResponse(data=r.create_supplier(x_tenant_id,p,key(idempotency_key),digest(p),access.actor_id))
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
def requisitions(x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),_=Depends(require_purchasing_access("purchasing.requisition.read"))):return ListResponse(data=r.list_requisitions(x_tenant_id))
@router.post("/requisitions",response_model=DataResponse,status_code=201)
def create_requisition(p:RequisitionWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.create"))):
    snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    try:return DataResponse(data=r.create_requisition(x_tenant_id,p,key(idempotency_key),digest(p),access.actor_id,snapshots))
    except ValueError as exc:raise fail(exc) from exc
@router.patch("/requisitions/{id}",response_model=DataResponse)
def update_requisition(id:str,p:RequisitionWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.update"))):
    snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    try:value=r.update_requisition(x_tenant_id,id,p,key(idempotency_key),digest(p,{"id":id}),access.actor_id,snapshots)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("requisition_not_found","Requisition not found.",status_code=404)
    return DataResponse(data=value)
def transition(id,target,reason,t,k,r,access):
    try:value=r.transition_requisition(t,id,target,reason,key(k),digest(path={"id":id,"target":target,"reason":reason}),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("requisition_not_found","Requisition not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/requisitions/{id}/submit",response_model=DataResponse)
def submit(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.submit"))):return transition(id,"submitted",None,x_tenant_id,idempotency_key,r,access)
@router.post("/requisitions/{id}/approve",response_model=DataResponse)
def approve(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.approve"))):return transition(id,"approved",None,x_tenant_id,idempotency_key,r,access)
@router.post("/requisitions/{id}/reject",response_model=DataResponse)
def reject(id:str,p:ReasonRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.reject"))):return transition(id,"rejected",p.reason,x_tenant_id,idempotency_key,r,access)
@router.post("/requisitions/{id}/cancel",response_model=DataResponse)
def cancel_requisition(id:str,p:ReasonRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.requisition.cancel"))):
    try:value=r.cancel_requisition(x_tenant_id,id,p.reason,key(idempotency_key),digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("requisition_not_found","Requisition not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/orders",response_model=ListResponse)
def orders(x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),_=Depends(require_purchasing_access("purchasing.order.read"))):return ListResponse(data=r.list_orders(x_tenant_id))
@router.post("/orders",response_model=DataResponse,status_code=201)
def create_order(p:PurchaseOrderWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.create"))):
    a.require_catalog(x_tenant_id,"currencies",p.currency,authorization); a.require_catalog(x_tenant_id,"payment_terms",p.payment_terms,authorization); snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    try:return DataResponse(data=r.create_order(x_tenant_id,p,key(idempotency_key),digest(p),access.actor_id,snapshots))
    except ValueError as exc:raise fail(exc) from exc
@router.patch("/orders/{id}",response_model=DataResponse)
def update_order(id:str,p:PurchaseOrderWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.update"))):
    a.require_catalog(x_tenant_id,"currencies",p.currency,authorization);a.require_catalog(x_tenant_id,"payment_terms",p.payment_terms,authorization);snapshots=validate_lines(x_tenant_id,p.lines,a,authorization)
    try:value=r.update_order(x_tenant_id,id,p,key(idempotency_key),digest(p,{"id":id}),access.actor_id,snapshots)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/orders/{id}/issue",response_model=DataResponse)
def issue(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.issue"))):
    k=key(idempotency_key);request_digest=digest(path={"id":id})
    current=r.get_order(x_tenant_id,id)
    if not current:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    if current["status"]=="draft":validate_lines(x_tenant_id,current["lines"],a,authorization)
    try:value=r.issue_order(x_tenant_id,id,k,request_digest,access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    return DataResponse(data=value)
@router.post("/orders/{id}/cancel",response_model=DataResponse)
def cancel_order(id:str,p:ReasonRequest,x_tenant_id:str=Header(alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.order.cancel"))):
    try:value=r.cancel_order(x_tenant_id,id,p.reason,key(idempotency_key),digest(p,{"id":id}),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not value:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    return DataResponse(data=value)
@router.get("/receipts",response_model=ListResponse)
def receipts(x_tenant_id:str=Header(alias="X-Tenant-Id"),r=Depends(get_purchasing_repository),_=Depends(require_purchasing_access("purchasing.receipt.read"))):return ListResponse(data=r.list_receipts(x_tenant_id))
@router.post("/receipts",response_model=DataResponse,status_code=201)
def create_receipt(p:ReceiptWrite,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.receipt.create"))):
    k=key(idempotency_key)
    validate_warehouses(x_tenant_id,p,r,a,authorization)
    try:receipt,plan=r.prepare_receipt(x_tenant_id,p,k,digest(p),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not receipt:raise ErclaveError("order_not_found","Purchase order not found.",status_code=404)
    if plan is None:return DataResponse(data=receipt)
    movements=[];dependency_error=None
    for line in plan:
        if line["line_type"]=="service":movements.append({"id":None});continue
        if dependency_error:movements.append(None);continue
        try:movements.append(a.receive(x_tenant_id,line,receipt["id"],p.purchase_order_id,authorization,line["inventory_idempotency_key"]))
        except ErclaveError as exc:dependency_error=str(exc.code);movements.append(None)
    if dependency_error:
        value=r.complete_receipt(x_tenant_id,receipt,plan,movements,k,access.actor_id,dependency_error); return DataResponse(data=value)
    return DataResponse(data=r.complete_receipt(x_tenant_id,receipt,plan,movements,k,access.actor_id))
@router.post("/receipts/{id}/reconcile",response_model=DataResponse)
def reconcile_receipt(id:str,x_tenant_id:str=Header(alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),r=Depends(get_purchasing_repository),a:PurchasingAuthorityClient=Depends(get_purchasing_authority_client),access:AuthorizedContext=Depends(require_purchasing_access("purchasing.receipt.reconcile"))):
    k=key(idempotency_key)
    try:receipt,plan=r.prepare_reconciliation(x_tenant_id,id,k,digest(path={"id":id}),access.actor_id)
    except ValueError as exc:raise fail(exc) from exc
    if not receipt:raise ErclaveError("receipt_not_found","Purchase receipt not found.",status_code=404)
    if plan is None:return DataResponse(data=receipt)
    movements=[];dependency_error=None
    for line in plan:
        if line["line_type"]=="inventory_item":
            if dependency_error:movements.append(None);continue
            try:
                warehouse=a.warehouse(x_tenant_id,line["warehouse_id"],authorization)
                if warehouse.get("status")!="active":raise ErclaveError("inactive_purchase_warehouse","Purchasing receipts require active warehouses.",status_code=422)
                movements.append(a.receive(x_tenant_id,line,receipt["id"],receipt["purchase_order_id"],authorization,line["inventory_idempotency_key"]))
            except ErclaveError as exc:dependency_error=str(exc.code);movements.append(None)
        else:movements.append({"id":None})
    if dependency_error:return DataResponse(data=r.complete_receipt(x_tenant_id,receipt,plan,movements,k,access.actor_id,dependency_error,"receipt.reconcile"))
    return DataResponse(data=r.complete_receipt(x_tenant_id,receipt,plan,movements,k,access.actor_id,operation="receipt.reconcile"))
