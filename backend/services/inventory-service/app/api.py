import hashlib, json
from typing import Literal
from fastapi import APIRouter, Depends, Header, Query
from erclave_common.errors import ErclaveError
from .authorization import AuthorizedContext, ProductionOrderClient, UnitCatalogClient, get_production_order_client, get_unit_catalog_client, require_inventory_access
from .repositories import InventoryRepository, get_inventory_repository
from .schemas import *

router=APIRouter(prefix="/v1/inventory",tags=["inventory"])
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
def warehouses(x_tenant_id: str|None=Header(None,alias="X-Tenant-Id"), q: str|None=None, repository: InventoryRepository=Depends(get_inventory_repository), _=Depends(require_inventory_access("inventory.warehouse.read"))): return WarehouseListResponse(data=repository.list_warehouses(tenant(x_tenant_id),q))
@router.post("/warehouses",response_model=WarehouseResponse,status_code=201)
def create_warehouse(payload: WarehouseCreate,x_tenant_id: str|None=Header(None,alias="X-Tenant-Id"),idempotency_key: str|None=Header(None,alias="Idempotency-Key"),repository: InventoryRepository=Depends(get_inventory_repository),access: AuthorizedContext=Depends(require_inventory_access("inventory.warehouse.create"))):
    result=repository.create_warehouse(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    if not result: raise ErclaveError("warehouse_conflict","Warehouse code already exists.",status_code=409)
    return WarehouseResponse(data=result)
@router.patch("/warehouses/{warehouse_id}",response_model=WarehouseResponse)
def update_warehouse(warehouse_id:str,payload:WarehouseUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.warehouse.update"))):
    result=repository.update_warehouse(tenant(x_tenant_id),warehouse_id,payload,key(idempotency_key),digest(payload,{"id":warehouse_id}),access.actor_id)
    if not result: raise ErclaveError("warehouse_not_found","Warehouse not found.",status_code=404)
    return WarehouseResponse(data=result)

@router.get("/items",response_model=ItemListResponse)
def items(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),q:str|None=None,use_in_recipe:bool|None=None,status:Status|None=None,repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.item.read"))): return ItemListResponse(data=repository.list_items(tenant(x_tenant_id),q,use_in_recipe,status))
@router.post("/items",response_model=ItemResponse,status_code=201)
def create_item(payload:ItemCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.item.create"))):
    resolved_tenant=tenant(x_tenant_id); unit_catalog.require_active(resolved_tenant,payload.base_unit,authorization)
    result=repository.create_item(resolved_tenant,payload,key(idempotency_key),digest(payload),access.actor_id)
    if not result: raise ErclaveError("item_conflict","Item code or warehouse is invalid.",status_code=409)
    return ItemResponse(data=result)
@router.get("/items/{item_id}",response_model=ItemResponse)
def get_item(item_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access(("inventory.item.read","production.product_service.create","production.product_service.update","sales.order.fulfill")))):
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
def movements(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.movement.read"))): return MovementListResponse(data=repository.list_movements(tenant(x_tenant_id)))
@router.post("/movements",response_model=MovementResponse,status_code=201)
def create_movement(payload:MovementCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create"))):
    unit_catalog.require_active(tenant(x_tenant_id),payload.unit,authorization)
    try: result=repository.create_movement(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc: raise ErclaveError(str(exc),"Movement violates inventory rules.",status_code=409) from exc
    if not result: raise ErclaveError("movement_reference_invalid","Item or warehouse was not found.",status_code=404)
    return MovementResponse(data=result)
@router.get("/finished-goods-receipts",response_model=FinishedGoodsReceiptListResponse)
def finished_goods_receipts(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.movement.read"))):
    return FinishedGoodsReceiptListResponse(data=repository.list_finished_goods_receipts(tenant(x_tenant_id)))
@router.post("/finished-goods-receipts",response_model=FinishedGoodsReceiptResponse,status_code=201)
def create_finished_goods_receipt(payload:FinishedGoodsReceiptCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),production:ProductionOrderClient=Depends(get_production_order_client),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create"))):
    resolved_tenant=tenant(x_tenant_id);order=production.get_order(resolved_tenant,payload.production_order_id,authorization)
    if order.get("status")!="completed":raise ErclaveError("production_order_not_completed","Only a completed production order can be received.",status_code=409)
    product=production.get_product(resolved_tenant,order.get("product_service_id"),authorization)
    if product.get("type")!="product" or product.get("status")!="active" or not product.get("inventory_item_id"):
        raise ErclaveError("finished_good_mapping_required","The production product must be active and linked to a finished-goods inventory item.",status_code=409)
    try:result=repository.create_finished_goods_receipt(resolved_tenant,payload,order,product,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:
        messages={"finished_goods_receipt_reference_invalid":"The item or warehouse is inactive, missing, or not a finished good.","finished_goods_receipt_unit_mismatch":"The order, product, and inventory item must use the same base unit.","finished_goods_receipt_quantity_exceeded":"The receipt exceeds the quantity pending from the production order."}
        raise ErclaveError(str(exc),messages.get(str(exc),"The finished-goods receipt violates inventory rules."),status_code=409) from exc
    if not result:raise ErclaveError("finished_goods_receipt_reference_not_found","The linked item or selected warehouse was not found.",status_code=404)
    return FinishedGoodsReceiptResponse(data=result)
@router.post("/movements/{movement_id}/reverse",response_model=MovementResponse)
def reverse_movement(movement_id:str,payload:ReverseRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.reverse"))):
    try: result=repository.reverse_movement(tenant(x_tenant_id),movement_id,payload.reason,key(idempotency_key),digest(payload,{"id":movement_id}),access.actor_id)
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
    repository:InventoryRepository=Depends(get_inventory_repository),
    _=Depends(require_inventory_access("inventory.balance.read"))
):
    try:
        data,page=repository.list_balances(tenant(x_tenant_id),q=q,inventory_item_id=inventory_item_id,warehouse_id=warehouse_id,category=category,item_type=item_type,item_status=item_status,inventory_policy=inventory_policy,unit=unit,stock_status=stock_status,sort=sort,cursor=cursor,limit=limit)
    except (ValueError, UnicodeError) as exc:
        raise ErclaveError("invalid_cursor","The balance cursor is invalid.",status_code=400) from exc
    return BalanceListResponse(data=data,page=page)
@router.get("/kardex",response_model=MovementListResponse)
def kardex(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),inventory_item_id:str|None=None,warehouse_id:str|None=None,repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.kardex.read"))): return MovementListResponse(data=repository.list_movements(tenant(x_tenant_id),inventory_item_id,warehouse_id))

@router.post("/availability-checks",response_model=AvailabilityCheckResponse)
def availability_check(payload:AvailabilityCheckRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access(("production.order.validate","production.order.create")))):
    key(idempotency_key)
    return AvailabilityCheckResponse(data=repository.check_availability(tenant(x_tenant_id),payload))

@router.post("/reservation-requests",response_model=ReservationResponse,status_code=201)
def create_reservation(payload:ReservationCreateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(("production.order.create","sales.order.fulfill")))):
    try:result=repository.create_reservation(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Inventory could not reserve the requested material.",status_code=409) from exc
    return ReservationResponse(data=result)

@router.post("/reservations/{reservation_id}/release",response_model=ReservationResponse)
def release_reservation(reservation_id:str,payload:ReservationActionRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(("production.order.status.update","sales.order.cancel")))):
    result=repository.release_reservation(tenant(x_tenant_id),reservation_id,payload.reason,key(idempotency_key),digest(payload,{"id":reservation_id}),access.actor_id)
    if not result:raise ErclaveError("reservation_not_found","Reservation not found.",status_code=404)
    return ReservationResponse(data=result)

@router.post("/reservations/{reservation_id}/consume",response_model=MovementResponse,status_code=201)
def consume_reservation(reservation_id:str,payload:ReservationActionRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access(("production.order.status.update","sales.delivery.confirm")))):
    try:result=repository.consume_reservation(tenant(x_tenant_id),reservation_id,payload.reason,key(idempotency_key),digest(payload,{"id":reservation_id}),access.actor_id,payload.quantity)
    except ValueError as exc:raise ErclaveError(str(exc),"Reservation cannot be consumed.",status_code=409) from exc
    if not result:raise ErclaveError("reservation_not_found","Reservation not found.",status_code=404)
    return MovementResponse(data=result)
