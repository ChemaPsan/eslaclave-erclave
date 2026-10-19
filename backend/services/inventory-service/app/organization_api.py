from uuid import uuid4
from fastapi import APIRouter, Depends, Header, Query, Path
from erclave_common.organization_client import OrganizationAccess, OrganizationClient, get_organization_client, require_organization_access, deny
from .repositories import get_inventory_repository
from .organization_store import OrganizationStore
from .organization_schemas import WarehouseDivisionCommand, WarehouseDivisionResponse, ItemDivisionCommand, ItemDivisionResponse, ItemDivisionListResponse, DivisionChoicesResponse, EligibleItemsResponse
router = APIRouter(prefix='/v1/inventory', tags=['Organization assignments'])

def require_inventory_organization(permission):
    return require_organization_access('inventory', permission)

def store(repository=Depends(get_inventory_repository)):
    return OrganizationStore(repository)

def command_meta(key: str | None=Header(None, alias='Idempotency-Key', max_length=160), correlation: str | None=Header(None, alias='X-Correlation-Id', max_length=128)):
    if not key or len(key.strip()) < 8:
        deny('idempotency_key_required', 400)
    return (key.strip(), correlation or str(uuid4()))

@router.get('/organization/divisions', response_model=DivisionChoicesResponse)
def divisions(q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_inventory_organization(('inventory.warehouse.read', 'inventory.item.read')))):
    rows = sorted((row for row in access.divisions if q.casefold() in (row['code'] + ' ' + row['name']).casefold()), key=lambda row: row['code'])
    return {'data': rows[offset:offset + limit], 'meta': {'total': len(rows), 'limit': limit, 'offset': offset}}

@router.get('/warehouses/{warehouse_id}/division', response_model=WarehouseDivisionResponse)
def warehouse_division(warehouse_id: str=Path(max_length=40), access: OrganizationAccess=Depends(require_inventory_organization('inventory.warehouse.read')), repository: OrganizationStore=Depends(store)):
    return {'data': repository.warehouse(access, warehouse_id)}

@router.patch('/warehouses/{warehouse_id}/division', response_model=WarehouseDivisionResponse)
def assign_warehouse(payload: WarehouseDivisionCommand, warehouse_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_inventory_organization('inventory.warehouse.update')), repository: OrganizationStore=Depends(store), client: OrganizationClient=Depends(get_organization_client)):
    return {'data': repository.save(access, 'warehouse', warehouse_id, payload.division_ref_id, payload, *meta, client)}

@router.get('/items/{item_id}/division-assignments', response_model=ItemDivisionListResponse)
def item_divisions(item_id: str=Path(max_length=40), division_id: str | None=Query(None, min_length=1, max_length=40), limit: int=Query(25, ge=1, le=100), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_inventory_organization('inventory.item.read')), repository: OrganizationStore=Depends(store)):
    return repository.items(access, item_id, limit, offset, division_id)

@router.put('/items/{item_id}/division-assignments/{division_id}', response_model=ItemDivisionResponse)
def assign_item(payload: ItemDivisionCommand, item_id: str=Path(max_length=40), division_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_inventory_organization('inventory.item.update')), repository: OrganizationStore=Depends(store), client: OrganizationClient=Depends(get_organization_client)):
    return {'data': repository.save(access, 'item', item_id, division_id, payload, *meta, client)}

@router.get('/division-items', response_model=EligibleItemsResponse)
def division_items(division_id: str=Query(min_length=1, max_length=40), q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_inventory_organization('inventory.item.read')), repository: OrganizationStore=Depends(store)):
    return repository.eligible(access, division_id, q, limit, offset)

from pydantic import BaseModel
from decimal import Decimal
from sqlalchemy import text
from erclave_common.operational_context import society_currency

class DivisionStockChoice(BaseModel):
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    available_quantity: Decimal

class DivisionStockChoices(BaseModel):
    inventory_item_id: str
    item_code: str
    item_name: str
    unit: str
    cost_currency: str
    warehouses: list[DivisionStockChoice]
    has_more: bool

class DivisionStockResponse(BaseModel):
    data: DivisionStockChoices

@router.get('/division-stock',response_model=DivisionStockResponse)
def division_stock(division_id: str=Query(min_length=1,max_length=40),inventory_item_id: str=Query(min_length=1,max_length=40),q: str=Query('',max_length=240),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_inventory_organization(('inventory.balance.read','sales.order.fulfill'))),repository=Depends(get_inventory_repository)):
    division=access.division(division_id)
    currency=society_currency(access,division['society_id'])
    query=q.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
    with repository.engine.connect() as conn:
        item=conn.execute(text("select i.id,i.code,i.name,i.base_unit from inventory.items i join inventory.item_division_assignments a on a.tenant_id=i.tenant_id and a.item_id=i.id where i.tenant_id=:t and i.id=:id and i.status='active' and a.status='active' and a.division_ref_id=:d"),{'t':access.tenant_id,'id':inventory_item_id,'d':division_id}).mappings().first()
        if not item:deny('operational_context_resource_unavailable',422)
        rows=conn.execute(text("select id,code,name from inventory.warehouses where tenant_id=:t and division_ref_id=:d and status='active' and (code ilike :q or name ilike :q) order by code,id limit 21 offset :offset"),{'t':access.tenant_id,'d':division_id,'q':'%'+query+'%','offset':offset}).mappings().all()
        choices=[{'warehouse_id':row['id'],'warehouse_code':row['code'],'warehouse_name':row['name'],'available_quantity':repository._balance(conn,access.tenant_id,inventory_item_id,row['id'],item['base_unit'])-repository._reserved(conn,access.tenant_id,inventory_item_id,row['id'],item['base_unit'])} for row in rows[:20]]
    return {'data':{'inventory_item_id':item['id'],'item_code':item['code'],'item_name':item['name'],'unit':item['base_unit'],'cost_currency':currency,'warehouses':choices,'has_more':len(rows)>20}}

from erclave_common.operational_context import OperationalContext

class WarehouseOperationContextResponse(BaseModel):
    data: OperationalContext | None

@router.get('/warehouses/{warehouse_id}/operation-context',response_model=WarehouseOperationContextResponse)
def warehouse_operation_context(warehouse_id: str=Path(max_length=40),access: OrganizationAccess=Depends(require_inventory_organization('inventory.movement.create')),repository=Depends(get_inventory_repository)):
    warehouse=repository.get_warehouse(access.tenant_id,warehouse_id)
    if not warehouse:deny('warehouse_not_found',404)
    division_id=repository.warehouse_dimension(access.tenant_id,warehouse_id)
    if not division_id:return {'data':None}
    division=access.division(division_id)
    return {'data':OperationalContext(division_ref_id=division_id,society_ref_id=division['society_id'],division_code=division['code'],division_name=division['name'],cost_currency=society_currency(access,division['society_id']))}

class ReceivedStockChoice(BaseModel):
    warehouse_id:str
    warehouse_code:str
    warehouse_name:str
    inventory_item_id:str
    item_code:str
    item_name:str
    received_quantity:Decimal
    available_quantity:Decimal
    unit:str
    organization_context:OperationalContext|None
class ReceivedStockResponse(BaseModel):
    data:list[ReceivedStockChoice]

@router.get('/finished-goods-receipts/{production_order_id}/stock-context',response_model=ReceivedStockResponse)
def received_stock_context(production_order_id:str=Path(max_length=40),access:OrganizationAccess=Depends(require_inventory_organization('sales.order.fulfill')),repository=Depends(get_inventory_repository)):
    params={'t':access.tenant_id,'id':production_order_id}
    scope=''
    if not access.all_divisions:
        scope=" and (w.division_ref_id is null or w.division_ref_id=any(:divisions))"
        params['divisions']=[row['id'] for row in access.divisions]
    with repository.engine.connect() as conn:
        rows=conn.execute(text("""select m.warehouse_id,w.code warehouse_code,w.name warehouse_name,m.inventory_item_id,i.code item_code,i.name item_name,m.unit,m.organization_context,sum(m.quantity) received_quantity
          from inventory.movements m join inventory.warehouses w on w.tenant_id=m.tenant_id and w.id=m.warehouse_id
          join inventory.items i on i.tenant_id=m.tenant_id and i.id=m.inventory_item_id
          where m.tenant_id=:t and m.source_id=:id and m.source_type='production_order_receipt' and m.direction='in' and m.status='recorded' and w.status='active' and i.status='active' and (w.division_ref_id is null or exists (select 1 from inventory.item_division_assignments a where a.tenant_id=i.tenant_id and a.item_id=i.id and a.division_ref_id=w.division_ref_id and a.status='active'))"""+scope+" group by m.warehouse_id,w.code,w.name,m.inventory_item_id,i.code,i.name,m.unit,m.organization_context order by w.code,m.inventory_item_id"),params).mappings().all()
        result=[]
        for row in rows:
            item=dict(row)
            item['available_quantity']=max(Decimal('0'),repository._balance(conn,access.tenant_id,row['inventory_item_id'],row['warehouse_id'],row['unit'])-repository._reserved(conn,access.tenant_id,row['inventory_item_id'],row['warehouse_id'],row['unit']))
            result.append(item)
    return {'data':result}
