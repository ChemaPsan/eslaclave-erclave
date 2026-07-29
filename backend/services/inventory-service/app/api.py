import hashlib, json
from typing import Literal
from fastapi import APIRouter, Depends, Header, Query
from erclave_common.errors import ErclaveError
from .authorization import AuthorizedContext, require_inventory_access
from .repositories import InventoryRepository, get_inventory_repository
from .schemas import *

router=APIRouter(prefix="/v1/inventory",tags=["inventory"])
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
def items(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),q:str|None=None,repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.item.read"))): return ItemListResponse(data=repository.list_items(tenant(x_tenant_id),q))
@router.post("/items",response_model=ItemResponse,status_code=201)
def create_item(payload:ItemCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.item.create"))):
    result=repository.create_item(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    if not result: raise ErclaveError("item_conflict","Item code or warehouse is invalid.",status_code=409)
    return ItemResponse(data=result)
@router.get("/items/{item_id}",response_model=ItemResponse)
def get_item(item_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.item.read"))):
    result=repository.get_item(tenant(x_tenant_id),item_id)
    if not result: raise ErclaveError("item_not_found","Item not found.",status_code=404)
    return ItemResponse(data=result)
@router.patch("/items/{item_id}",response_model=ItemResponse)
def update_item(item_id:str,payload:ItemUpdate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.item.update"))):
    try: result=repository.update_item(tenant(x_tenant_id),item_id,payload,key(idempotency_key),digest(payload,{"id":item_id}),access.actor_id)
    except ValueError as exc:
        if str(exc)=="suggested_warehouse_invalid": raise ErclaveError("suggested_warehouse_invalid","Suggested warehouse does not belong to the active tenant.",status_code=409) from exc
        raise
    if not result: raise ErclaveError("item_not_found","Item not found.",status_code=404)
    return ItemResponse(data=result)

@router.get("/movements",response_model=MovementListResponse)
def movements(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:InventoryRepository=Depends(get_inventory_repository),_=Depends(require_inventory_access("inventory.movement.read"))): return MovementListResponse(data=repository.list_movements(tenant(x_tenant_id)))
@router.post("/movements",response_model=MovementResponse,status_code=201)
def create_movement(payload:MovementCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:InventoryRepository=Depends(get_inventory_repository),access:AuthorizedContext=Depends(require_inventory_access("inventory.movement.create"))):
    try: result=repository.create_movement(tenant(x_tenant_id),payload,key(idempotency_key),digest(payload),access.actor_id)
    except ValueError as exc: raise ErclaveError(str(exc),"Movement violates inventory rules.",status_code=409) from exc
    if not result: raise ErclaveError("movement_reference_invalid","Item or warehouse was not found.",status_code=404)
    return MovementResponse(data=result)
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
