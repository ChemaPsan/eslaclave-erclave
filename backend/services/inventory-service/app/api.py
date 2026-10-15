from .finished_goods_context import finished_goods_context
from .producer_context import maintenance_context, purchase_context
from erclave_common.operational_context import OperationalContext
from .reservation_context import ReservationContextClient, get_reservation_context_client, read_divisions
import hashlib, json
from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, Header, Query
from erclave_common.errors import ErclaveError
from erclave_common.business_codes import BusinessCodeClient,get_business_code_client
from erclave_common.material_return_client import MaterialReturnClient,get_material_return_client
from erclave_common.csv_reports import csv_report_response,validate_date_range
from .authorization import AuthorizedContext, ProductionOrderClient, UnitCatalogClient, get_production_order_client, get_unit_catalog_client, require_inventory_access
from .repositories import InventoryRepository, get_inventory_repository
from .reports import REPORT_PERMISSIONS,build_report
from .schemas import *

router=APIRouter(prefix="/v1/inventory",tags=["inventory"])

def movement_folio(codes,tenant_id,authorization):
    if not hasattr(codes,"allocate"):
        return None  # Direct repository/API harnesses bypass FastAPI dependency injection.
    return lambda operation,stable_key,manual_code=None:codes.allocate(tenant_id,"inventory.movement",authorization,f"inventory.{operation}:{stable_key}",manual_code)


def authorize_handoff(repository,client,t,snapshot,warehouse,permission,authorization,actor=None,active=False):
    if snapshot:
        value=OperationalContext.model_validate(snapshot) if isinstance(snapshot,dict) else snapshot
        value.authorize(client.access(t,permission,authorization,actor),active=active)
    elif hasattr(repository,'warehouse_dimension') and repository.warehouse_dimension(t,warehouse):
        # Reading/replaying legacy never grants access through an old null snapshot.
        client.warehouse_context(repository,t,warehouse,permission,authorization,actor)


def validate_return_snapshot(source,proof):
    if source.get('source_type') != 'maintenance_order' or not source.get('organization_context'):
        return
    original=OperationalContext.model_validate(source['organization_context'])
    try:
        confirmed=OperationalContext.model_validate(proof['organization_context'])
        cost=Decimal(str(proof['unit_cost_snapshot']))
        expected=Decimal(str(source['unit_cost']))
    except (KeyError,ValueError,TypeError,ArithmeticError):
        raise ErclaveError('assignment_authority_unavailable','Return proof is incomplete.',status_code=503)
    if confirmed!=original or not cost.is_finite() or cost!=expected:
        raise ErclaveError('operational_context_mismatch','Return proof differs from the original movement.',status_code=409)

@router.get("/reports/{report_code}/export")
def export_report(report_code:str,lang:Literal["es","en"]="es",date_from:date|None=None,date_to:date|None=None,status:str|None=None,type_filter:str|None=Query(None,alias="type"),category:str|None=None,q:str|None=Query(None,max_length=120),warehouse_id:str|None=None,item_id:str|None=None,movement_type:str|None=None,condition:str|None=None,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(tuple(REPORT_PERMISSIONS.values())))):
    validate_date_range(date_from,date_to);permission=REPORT_PERMISSIONS.get(report_code)
    if not permission:raise ErclaveError("report_not_found","Inventory report does not exist.",status_code=404)
    access.require(permission)
    filters={"date_from":date_from,"date_to":date_to,"status":status,"type":type_filter,"category":category,"q":q,"warehouse_id":warehouse_id,"item_id":item_id,"movement_type":movement_type,"condition":condition}
    filters["allowed_divisions"]=read_divisions(repository,context_client,tenant(x_tenant_id),permission,authorization,access.actor_id)
    return csv_report_response(build_report(repository,tenant(x_tenant_id),report_code,filters),lang)
UNIT_FACTORS={
    "H87":("count",1),"C62":("count",1),"DZN":("count",12),"PR":("count",2),
    "KGM":("mass",1),"GRM":("mass",0.001),"MGM":("mass",0.000001),"TNE":("mass",1000),"LBR":("mass",0.45359237),"ONZ":("mass",0.028349523125),
    "MTR":("length",1),"CMT":("length",0.01),"MMT":("length",0.001),"KMT":("length",1000),"INH":("length",0.0254),"FOT":("length",0.3048),"YRD":("length",0.9144),
    "MTK":("area",1),"CMK":("area",0.0001),"MMK":("area",0.000001),"HAR":("area",10000),
    "LTR":("volume",1),"MLT":("volume",0.001),"MTQ":("volume",1000),"CMQ":("volume",0.001),"GLL":("volume",3.785411784),
    "SEC":("time",1),"MIN":("time",60),"HUR":("time",3600),"DAY":("time",86400),"WEE":("time",604800),
    "WHR":("energy",1),"KWH":("energy",1000),"WTT":("power",1),"KWT":("power",1000),
}
def tenant(value):
    if not value: raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
    return value
def key(value):
    if not value: raise ErclaveError("idempotency_key_required","Idempotency-Key header is required.",status_code=400)
    return value
def digest(payload, path=None):
    return hashlib.sha256(json.dumps({"body":payload.model_dump(mode="json") if payload else {},"path":path or {}},sort_keys=True,separators=(",",":")).encode()).hexdigest()

@router.get("/warehouses",response_model=WarehouseListResponse)
def warehouses(x_tenant_id: str|None=Header(None,alias="X-Tenant-Id"), q: str|None=None, repository: InventoryRepository=Depends(get_inventory_repository), _=Depends(require_inventory_access(("inventory.warehouse.read","inventory.movement.read","inventory.movement.create","maintenance.material_request.read","maintenance.material_request.create")))): return WarehouseListResponse(data=repository.list_warehouses(tenant(x_tenant_id),q))
@router.post("/warehouses",response_model=WarehouseResponse,status_code=201)
def create_warehouse(payload: WarehouseCreate,x_tenant_id: str|None=Header(None,alias="X-Tenant-Id"),idempotency_key: str|None=Header(None,alias="Idempotency-Key"),repository: InventoryRepository=Depends(get_inventory_repository),access: AuthorizedContext=Depends(require_inventory_access("inventory.warehouse.create"))):
    result=repository.create_warehouse(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    if not result: raise ErclaveError("warehouse_conflict","Warehouse code already exists.",status_code=409)
    return WarehouseResponse(data=result)
@router.get("/warehouses/{warehouse_id}",response_model=WarehouseResponse)
def get_warehouse(warehouse_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access(("inventory.warehouse.read","purchasing.receipt.create","maintenance.material_request.create")))):
    result=repository.get_warehouse(tenant(x_tenant_id),warehouse_id)
    if not result:raise ErclaveError("warehouse_not_found","Warehouse not found.",status_code=404)
    return WarehouseResponse(data=result)
@router.patch("/warehouses/{warehouse_id}",response_model=WarehouseResponse)
def update_warehouse(warehouse_id:str,payload:WarehouseUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.warehouse.update"))):
    result=repository.update_warehouse(tenant(x_tenant_id),warehouse_id,payload,key(idempotency_key),digest(payload,{"id":warehouse_id}),access.actor_id)
    if not result: raise ErclaveError("warehouse_not_found","Warehouse not found.",status_code=404)
    return WarehouseResponse(data=result)

@router.get("/items",response_model=ItemListResponse)
def items(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),q:str|None=None,use_in_recipe:bool|None=None,status:Status|None=None,repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access(("inventory.item.read","production.product_service.create","production.product_service.update","sales.order.fulfill","maintenance.material_request.read","maintenance.material_request.create","purchasing.requisition.create","purchasing.requisition.update","purchasing.order.create","purchasing.order.update","purchasing.order.issue")))): return ItemListResponse(data=repository.list_items(tenant(x_tenant_id),q,use_in_recipe,status))
@router.post("/items",response_model=ItemResponse,status_code=201)
def create_item(payload:ItemCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.item.create"))):
    resolved_tenant=tenant(x_tenant_id); unit_catalog.require_active(resolved_tenant,payload.base_unit,authorization)
    result=repository.create_item(resolved_tenant,payload,key(idempotency_key),digest(payload),access.actor_id)
    if not result: raise ErclaveError("item_conflict","Item code or warehouse is invalid.",status_code=409)
    return ItemResponse(data=result)
@router.get("/items/{item_id}",response_model=ItemResponse)
def get_item(item_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access(("inventory.item.read","production.product_service.create","production.product_service.update","sales.order.fulfill","maintenance.material_request.create","purchasing.requisition.create","purchasing.requisition.update","purchasing.order.create","purchasing.order.update","purchasing.order.issue")))):
    result=repository.get_item(tenant(x_tenant_id),item_id)
    if not result: raise ErclaveError("item_not_found","Item not found.",status_code=404)
    return ItemResponse(data=result)
@router.post("/items/{item_id}/unit-conversion",response_model=UnitConversionResponse)
def convert_item_unit(item_id:str,payload:UnitConversionRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),_=Depends(require_inventory_access("inventory.item.read"))):
    resolved_tenant=tenant(x_tenant_id); item=repository.get_item(resolved_tenant,item_id)
    if not item: raise ErclaveError("item_not_found","Item not found.",status_code=404)
    source=unit_catalog.resolve_active(resolved_tenant,payload.source_unit,authorization); target=unit_catalog.resolve_active(resolved_tenant,item.base_unit,authorization)
    source_code=source["code"].upper(); target_code=target["code"].upper()
    if source_code==target_code: factor=1.0
    else:
        source_factor=UNIT_FACTORS.get(source_code);target_factor=UNIT_FACTORS.get(target_code)
        if not source_factor or not target_factor or source.get("category")!=target.get("category") or source_factor[0]!=target_factor[0] or source_factor[0]!=source.get("category"):
            raise ErclaveError("unit_conversion_unsupported","Units are not compatible or require an item-specific conversion.",status_code=422,details={"source_unit":source_code,"base_unit":target_code})
        factor=source_factor[1]/target_factor[1]
    base_quantity=payload.quantity*factor
    base_cost=(payload.source_unit_cost/factor) if payload.source_unit_cost is not None else None
    return UnitConversionResponse(data=UnitConversionRead(inventory_item_id=item.id,source_unit=source_code,base_unit=target_code,conversion_factor=factor,source_quantity=payload.quantity,base_quantity=base_quantity,source_unit_cost=payload.source_unit_cost,unit_cost_per_base_unit=base_cost))
@router.patch("/items/{item_id}",response_model=ItemResponse)
def update_item(item_id:str,payload:ItemUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.item.update"))):
    if payload.base_unit: unit_catalog.require_active(tenant(x_tenant_id),payload.base_unit,authorization)
    try: result=repository.update_item(tenant(x_tenant_id),item_id,payload,key(idempotency_key),digest(payload,{"id":item_id}),access.actor_id)
    except ValueError as exc:
        if str(exc)=="suggested_warehouse_invalid": raise ErclaveError("suggested_warehouse_invalid","Suggested warehouse does not belong to the active tenant.",status_code=409) from exc
        if str(exc)=="item_base_unit_locked_by_movements": raise ErclaveError("item_base_unit_locked_by_movements","Base unit cannot change after inventory movements or reservations exist.",status_code=409) from exc
        if str(exc)=="invalid_stock_limits": raise ErclaveError("invalid_stock_limits","Maximum stock must be greater than or equal to minimum stock.",status_code=422) from exc
        raise
    if not result: raise ErclaveError("item_not_found","Item not found.",status_code=404)
    return ItemResponse(data=result)

@router.get("/movements",response_model=MovementListResponse)
def movements(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.movement.read"))):
    divisions=read_divisions(repository,context_client,tenant(x_tenant_id),"inventory.movement.read",authorization)
    return MovementListResponse(data=repository.list_movements(tenant(x_tenant_id),**({"allowed_divisions":divisions} if divisions is not None else {})))

@router.get("/transfers",response_model=TransferListResponse)
def transfers(limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.movement.read")),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client)):
    divisions=read_divisions(repository,context_client,tenant(x_tenant_id),'inventory.movement.read',authorization)
    return TransferListResponse(data=repository.list_transfers(tenant(x_tenant_id),limit,offset,**({'allowed_divisions':divisions} if divisions is not None else {})))

@router.get("/material-returns",response_model=MaterialReturnListResponse)
def material_returns(limit:int=Query(25,ge=1,le=100),offset:int=Query(0,ge=0),x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.movement.read")),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client)):
    divisions=read_divisions(repository,context_client,tenant(x_tenant_id),'inventory.movement.read',authorization)
    return MaterialReturnListResponse(data=repository.list_material_returns(tenant(x_tenant_id),limit,offset,**({'allowed_divisions':divisions} if divisions is not None else {})))

@router.get("/material-returns/{return_id}",response_model=MaterialReturnResponse)
def material_return(return_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access(("inventory.movement.read","inventory.movement.create"))),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client)):
    value=repository.get_material_return(tenant(x_tenant_id),return_id)
    if value is None:raise ErclaveError("material_return_not_found","Material return not found.",status_code=404)
    authorize_handoff(repository,context_client,tenant(x_tenant_id),value.organization_context,value.warehouse_id,('inventory.movement.read','inventory.movement.create'),authorization)
    return MaterialReturnResponse(data=value)

@router.post("/material-returns",response_model=MaterialReturnResponse,status_code=201)
def request_material_return(payload:MaterialReturnRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),authority:MaterialReturnClient=Depends(get_material_return_client),access:AuthorizedContext=Depends(require_inventory_access(("production.order.update","maintenance.material_request.create","inventory.movement.create"))),context_client:ReservationContextClient=Depends(get_reservation_context_client)):
    t=tenant(x_tenant_id);k=key(idempotency_key)
    try:source=repository.return_source(t,payload.original_movement_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Only issued order materials can be returned.",status_code=409) from exc
    permission={"production_order":"production.order.update","maintenance_order":"maintenance.material_request.create"}[source['source_type']]
    if not (access.permissions or frozenset({access.permission})).intersection({permission,"inventory.movement.create"}):raise ErclaveError("permission_denied","This order's return permission is required.",status_code=403)
    authorize_handoff(repository,context_client,t,source.get('organization_context'),source.get('warehouse_id'),(permission,'inventory.movement.create'),authorization,access.actor_id)
    source['quantity']=payload.quantity
    try:replay=repository.replay_material_return_request(t,k,digest(payload))
    except ValueError as exc:raise ErclaveError(str(exc),"The request key was reused with different data.",status_code=409) from exc
    if replay:return MaterialReturnResponse(data=replay)
    validated=authority.validate(t,source,authorization)
    validate_return_snapshot(source,validated)
    try:value=repository.request_material_return(t,payload,source,validated['source_code'],k,digest(payload),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Return exceeds the remaining issued quantity.",status_code=409) from exc
    return MaterialReturnResponse(data=value)

@router.post("/material-returns/{return_id}/receive",response_model=MaterialReturnResponse)
def receive_material_return(return_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),authority:MaterialReturnClient=Depends(get_material_return_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create")),context_client:ReservationContextClient=Depends(get_reservation_context_client),codes:BusinessCodeClient=Depends(get_business_code_client)):
    t=tenant(x_tenant_id);key(idempotency_key)
    with repository.return_command_lock(t,return_id):
        value=repository.get_material_return(t,return_id)
        if value is None:raise ErclaveError("material_return_not_found","Material return not found.",status_code=404)
        authorize_handoff(repository,context_client,t,value.organization_context,value.warehouse_id,'inventory.movement.create',authorization,access.actor_id,active=value.status=='pending')
        if value.status=='completed':return MaterialReturnResponse(data=value)
        if value.status=='cancelled':raise ErclaveError('material_return_not_receivable','A cancelled return cannot be received.',status_code=409)
        if value.status=='pending':
            validated=authority.validate(t,value.model_dump(mode='json'),authorization)
            validate_return_snapshot(value.model_dump(mode='json'),validated)
            try:value=repository.receive_material_return(t,return_id,access.actor_id,folio=movement_folio(codes,t,authorization))
            except ValueError as exc:raise ErclaveError(str(exc),"Material return cannot be received.",status_code=409) from exc
        error_code=None
        try:authority.reconcile(t,value.model_dump(mode='json'),authorization)
        except ErclaveError as exc:error_code=exc.code
        return MaterialReturnResponse(data=repository.finish_material_return(t,return_id,access.actor_id,error_code))

@router.post("/material-returns/{return_id}/cancel",response_model=MaterialReturnResponse)
def cancel_material_return(return_id:str,payload:ReverseRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create")),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client)):
    t=tenant(x_tenant_id);key(idempotency_key)
    with repository.return_command_lock(t,return_id):
        current=repository.get_material_return(t,return_id)
        if current:authorize_handoff(repository,context_client,t,current.organization_context,current.warehouse_id,'inventory.movement.create',authorization,access.actor_id)
        try:value=repository.cancel_material_return(t,return_id,payload.reason,access.actor_id)
        except ValueError as exc:raise ErclaveError(str(exc),"Only a pending physical return can be cancelled.",status_code=409) from exc
        if value is None:raise ErclaveError('material_return_not_found','Material return not found.',status_code=404)
        return MaterialReturnResponse(data=value)

@router.post("/transfers/{transfer_id}/{action}",response_model=TransferResponse)
def transfer_action(transfer_id:str,action:Literal["receive","request-return","receive-return"],payload:TransferActionRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create")),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),codes:BusinessCodeClient=Depends(get_business_code_client)):
    current=repository.get_transfer(tenant(x_tenant_id),transfer_id)
    if current:
        for snapshot,warehouse in ((current.organization_context,current.origin_warehouse_id),(current.destination_context,current.destination_warehouse_id)):
            target=current.origin_warehouse_id if action=='receive-return' else current.destination_warehouse_id
            active=action!='request-return' and warehouse==target and current.status not in ('received','returned')
            authorize_handoff(repository,context_client,tenant(x_tenant_id),snapshot,warehouse,'inventory.movement.create',authorization,access.actor_id,active=active)
    try:value=repository.transition_transfer(tenant(x_tenant_id),transfer_id,action,payload,key(idempotency_key),digest(payload,{"id":transfer_id,"action":action}),access.actor_id,folio=movement_folio(codes,tenant(x_tenant_id),authorization))
    except ValueError as exc:raise ErclaveError(str(exc),"Transfer requires physical receipt at the specified warehouse.",status_code=409) from exc
    if value is None:raise ErclaveError("transfer_not_found","Transfer not found.",status_code=404)
    return TransferResponse(data=value)
@router.post("/movements",response_model=MovementResponse,status_code=201)
def create_movement(payload:MovementCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create")),codes:BusinessCodeClient=Depends(get_business_code_client)):
    context=context_client.warehouse_context(repository,tenant(x_tenant_id),payload.warehouse_id,"inventory.movement.create",authorization,access.actor_id)
    if payload.source.type!='manual':raise ErclaveError('operational_context_mismatch','Use the owning producer endpoint.',status_code=422)
    destination=context_client.warehouse_context(repository,tenant(x_tenant_id),payload.destination_warehouse_id,'inventory.movement.create',authorization,access.actor_id) if payload.movement_type=='transfer' else None
    unit_catalog.require_active(tenant(x_tenant_id),payload.unit,authorization)
    try: result=repository.create_movement(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id,**({"organization_context":context} if context else {}),**({'destination_context':destination} if destination else {}),folio=movement_folio(codes,tenant(x_tenant_id),authorization))
    except ValueError as exc: raise ErclaveError(str(exc),"Movement violates inventory rules.",status_code=409) from exc
    if not result: raise ErclaveError("movement_reference_invalid","Item or warehouse was not found.",status_code=404)
    return MovementResponse(data=result)
@router.post("/purchase-receipts",response_model=MovementResponse,status_code=201)
def create_purchase_receipt_movement(payload:MovementCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create")),context_client:ReservationContextClient=Depends(get_reservation_context_client),codes:BusinessCodeClient=Depends(get_business_code_client)):
    if payload.movement_type!="entry" or payload.source.type!="purchase_receipt" or not payload.source.line_id or payload.destination_warehouse_id:
        raise ErclaveError("purchase_receipt_payload_invalid","Purchasing receipts only accept purchase-order entries with an order line.",status_code=422)
    unit_catalog.require_active(tenant(x_tenant_id),payload.unit,authorization)
    context,proof=purchase_context(context_client,tenant(x_tenant_id),payload,key(idempotency_key),authorization,access.actor_id)
    context.authorize(context_client.access(tenant(x_tenant_id),'inventory.movement.create',authorization,access.actor_id))
    try:result=repository.create_movement(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id,organization_context=context,purchase_proof=proof,folio=movement_folio(codes,tenant(x_tenant_id),authorization))
    except ValueError as exc:raise ErclaveError(str(exc),"Purchase receipt violates inventory rules.",status_code=409) from exc
    if not result:raise ErclaveError("purchase_receipt_reference_invalid","Item or warehouse was not found.",status_code=404)
    return MovementResponse(data=result)
@router.get("/finished-goods-receipts",response_model=FinishedGoodsReceiptListResponse)
def finished_goods_receipts(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.finished_goods_receipt.read"))):
    divisions=read_divisions(repository,context_client,tenant(x_tenant_id),"inventory.finished_goods_receipt.read",authorization)
    return FinishedGoodsReceiptListResponse(data=repository.list_finished_goods_receipts(tenant(x_tenant_id),**({"allowed_divisions":divisions} if divisions is not None else {})))
@router.post("/finished-goods-receipts",response_model=FinishedGoodsReceiptResponse,status_code=201)
def create_finished_goods_receipt(payload:FinishedGoodsReceiptCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),production:ProductionOrderClient=Depends(get_production_order_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.finished_goods_receipt.receive")),codes:BusinessCodeClient=Depends(get_business_code_client)):
    resolved_tenant=tenant(x_tenant_id);candidate=production.get_finished_goods_candidate(resolved_tenant,payload.production_order_id,authorization)
    order=candidate.get("order") or {};product=candidate.get("product") or {}
    context,_original_cost=finished_goods_context(order,product,payload.production_order_id)
    if context:context.authorize(context_client.access(resolved_tenant,"inventory.finished_goods_receipt.receive",authorization,access.actor_id))
    if order.get("status")!="completed":raise ErclaveError("production_order_not_completed","Only a completed production order can be received.",status_code=409)
    if product.get("type")!="product" or product.get("status")!="active" or not product.get("inventory_item_id"):
        raise ErclaveError("finished_good_mapping_required","The production product must be active and linked to a finished-goods inventory item.",status_code=409)
    try:result=repository.create_finished_goods_receipt(resolved_tenant,payload,order,product,key(idempotency_key),digest(payload),access.actor_id,folio=movement_folio(codes,resolved_tenant,authorization))
    except ValueError as exc:
        messages={"finished_goods_receipt_reference_invalid":"The item or warehouse is inactive, missing, or not a finished good.","finished_goods_receipt_unit_mismatch":"The order, product, and inventory item must use the same base unit.","finished_goods_receipt_quantity_exceeded":"The receipt exceeds the quantity pending from the production order."}
        raise ErclaveError(str(exc),messages.get(str(exc),"The finished-goods receipt violates inventory rules."),status_code=409) from exc
    if not result:raise ErclaveError("finished_goods_receipt_reference_not_found","The linked item or selected warehouse was not found.",status_code=404)
    return FinishedGoodsReceiptResponse(data=result)
@router.post("/movements/{movement_id}/reverse",response_model=MovementResponse)
def reverse_movement(movement_id:str,payload:ReverseRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.reverse")),codes:BusinessCodeClient=Depends(get_business_code_client)):
    current=repository.get_movement(tenant(x_tenant_id),movement_id)
    if current and current.organization_context:current.organization_context.authorize(context_client.access(tenant(x_tenant_id),'inventory.movement.reverse',authorization,access.actor_id),active=False)
    try: result=repository.reverse_movement(tenant(x_tenant_id),movement_id,payload.reason,key(idempotency_key),digest(payload,{"id":movement_id}),access.actor_id,folio=movement_folio(codes,tenant(x_tenant_id),authorization))
    except ValueError as exc: raise ErclaveError(str(exc),"Movement cannot be reversed.",status_code=409) from exc
    if not result: raise ErclaveError("movement_not_found","Movement not found.",status_code=404)
    return MovementResponse(data=result)
@router.get("/balances",response_model=BalanceListResponse)
def balances(
    x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"), q:str|None=None,
    inventory_item_id:str|None=None, warehouse_id:str|None=None, category:str|None=None,
    item_type:str|None=None, item_status:Status|None=None, inventory_policy:str|None=None, unit:str|None=None,
    stock_status:Literal["negative","out_of_stock","below_minimum","normal","above_maximum"]|None=None,
    sort:Literal["item_code","item_name","on_hand_asc","on_hand_desc"]="item_code",
    cursor:str|None=None, limit:int=Query(50,ge=1,le=200),
    authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),
    repository:InventoryRepository=Depends(get_inventory_repository),
    _=Depends(require_inventory_access("inventory.balance.read"))
):
    try:
        data,page=repository.list_balances(tenant(x_tenant_id),allowed_divisions=read_divisions(repository,context_client,tenant(x_tenant_id),"inventory.balance.read",authorization),q=q,inventory_item_id=inventory_item_id,warehouse_id=warehouse_id,category=category,item_type=item_type,item_status=item_status,inventory_policy=inventory_policy,unit=unit,stock_status=stock_status,sort=sort,cursor=cursor,limit=limit)
    except (ValueError, UnicodeError) as exc:
        raise ErclaveError("invalid_cursor","The balance cursor is invalid.",status_code=400) from exc
    return BalanceListResponse(data=data,page=page)
@router.get("/kardex",response_model=MovementListResponse)
def kardex(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),inventory_item_id:str|None=None,warehouse_id:str|None=None,authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.kardex.read"))):
    divisions=read_divisions(repository,context_client,tenant(x_tenant_id),"inventory.kardex.read",authorization)
    return MovementListResponse(data=repository.list_movements(tenant(x_tenant_id),inventory_item_id,warehouse_id,**({"allowed_divisions":divisions} if divisions is not None else {})))

@router.post("/availability-checks",response_model=AvailabilityCheckResponse)
def availability_check(payload:AvailabilityCheckRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(("production.order.validate","production.order.release")))):
    key(idempotency_key)
    context = context_client.division_context(tenant(x_tenant_id), payload.division_ref_id, ("production.order.validate", "production.order.release"), authorization, access.actor_id) if payload.division_ref_id else None
    return AvailabilityCheckResponse(data=repository.check_availability(tenant(x_tenant_id),payload,**({"organization_context":context} if context else {})))

@router.post("/reservation-requests",response_model=ReservationResponse,status_code=201)
def create_reservation(payload:ReservationCreateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(("production.order.release","sales.order.fulfill","maintenance.material_request.create")))):
    source_permissions={"sales_order":"sales.order.fulfill","production_order":"production.order.release","maintenance_order":"maintenance.material_request.create"}
    permission=source_permissions.get(payload.source.type)
    if not permission:raise ErclaveError("permission_denied","Unsupported reservation source.",status_code=403)
    access.require(permission)
    context=context_client.sales_context(tenant(x_tenant_id),payload.source,authorization,access.actor_id,payload) if payload.source.type=="sales_order" else context_client.production_context(tenant(x_tenant_id),payload,authorization,access.actor_id) if payload.source.type=="production_order" else maintenance_context(context_client,tenant(x_tenant_id),payload,authorization,access.actor_id)
    if context:context.authorize(context_client.access(tenant(x_tenant_id),permission,authorization,access.actor_id))
    try:result=repository.create_reservation(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id,**({"organization_context":context} if context else {}))
    except ValueError as exc:raise ErclaveError(str(exc),"Inventory could not reserve the requested material.",status_code=409) from exc
    return ReservationResponse(data=result)

@router.post("/reservations/{reservation_id}/release",response_model=ReservationResponse)
def release_reservation(reservation_id:str,payload:ReservationActionRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(("production.order.cancel","sales.order.cancel","maintenance.material_request.cancel","maintenance.order.cancel","inventory.movement.create")))):
    current=repository.get_reservation(tenant(x_tenant_id),reservation_id)
    if current and current.organization_context:
        current.organization_context.authorize(context_client.access(tenant(x_tenant_id),access.permission,authorization,access.actor_id),active=False)
    permissions=access.permissions or frozenset({access.permission})
    source_permissions={"production_order":{"production.order.cancel"},"sales_order":{"sales.order.cancel"},"maintenance_order":{"maintenance.material_request.cancel","maintenance.order.cancel","inventory.movement.create"}}
    allowed_sources={source for source,required in source_permissions.items() if permissions.intersection(required)}
    try:result=repository.release_reservation(tenant(x_tenant_id),reservation_id,payload.reason,key(idempotency_key),digest(payload,{"id":reservation_id}),access.actor_id,allowed_sources=allowed_sources)
    except ValueError as exc:raise ErclaveError(str(exc),"Reservation cannot be released.",status_code=403 if str(exc)=="permission_denied" else 409) from exc
    if not result:raise ErclaveError("reservation_not_found","Reservation not found.",status_code=404)
    return ReservationResponse(data=result)

@router.post("/reservations/{reservation_id}/consume",response_model=MovementResponse,status_code=201)
def consume_reservation(reservation_id:str,payload:ReservationActionRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),authorization:str|None=Header(None,alias="Authorization"),context_client:ReservationContextClient=Depends(get_reservation_context_client),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create")),codes:BusinessCodeClient=Depends(get_business_code_client)):
    current=repository.get_reservation(tenant(x_tenant_id),reservation_id)
    if current and current.organization_context:
        current.organization_context.authorize(context_client.access(tenant(x_tenant_id),access.permission,authorization,access.actor_id),active=True)
    permissions=access.permissions or frozenset({access.permission})
    source_permissions={"production_order":{"inventory.movement.create"},"sales_order":{"inventory.movement.create"},"maintenance_order":{"inventory.movement.create"}}
    allowed_sources={source for source,required in source_permissions.items() if permissions.intersection(required)}
    try:result=repository.consume_reservation(tenant(x_tenant_id),reservation_id,payload.reason,key(idempotency_key),digest(payload,{"id":reservation_id}),access.actor_id,payload.quantity,allowed_sources=allowed_sources,folio=movement_folio(codes,tenant(x_tenant_id),authorization))
    except ValueError as exc:raise ErclaveError(str(exc),"Reservation cannot be consumed.",status_code=403 if str(exc)=="permission_denied" else 409) from exc
    if not result:raise ErclaveError("reservation_not_found","Reservation not found.",status_code=404)
    return MovementResponse(data=result)


@router.post("/production-reservation-rollbacks")
def rollback_production_reservations(payload:ProductionReservationRollbackRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),production:ProductionOrderClient=Depends(get_production_order_client),access:AuthorizedContext=Depends(require_inventory_access("production.order.release"))):
    t=tenant(x_tenant_id);key(idempotency_key)
    proof=production.get_failed_creation(t,payload.source_id,authorization)
    if proof.get('id')!=payload.source_id or proof.get('actor_id')!=access.actor_id:raise ErclaveError("production_creation_recovery_not_allowed","Only the failed creation owner can recover reservations.",status_code=403)
    try:return {"data":repository.rollback_production_reservations(t,payload.source_id,access.actor_id)}
    except ValueError as exc:raise ErclaveError(str(exc),"Reservations cannot be released by creation recovery.",status_code=409) from exc
