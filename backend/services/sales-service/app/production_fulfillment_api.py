"""Authenticated manufacturing source and explicit receipt reconciliation."""
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, Path, Query, Header
from pydantic import BaseModel, ConfigDict, Field
from erclave_common.organization_client import OrganizationAccess, require_organization_access, deny
from erclave_common.operational_context import OperationalContext
from .repositories import get_sales_repository
from .authorities import get_sales_authority_client
from .schemas import SalesOrderResponse
from .api import fingerprint, require_key

router=APIRouter(prefix='/v1/sales',tags=['Sales production'])

def source_order(repository,access,order_id,line_id,active=True):
    order=repository.get_order(access.tenant_id,order_id)
    if not order:deny('sales_order_not_found',404)
    context=None
    if order.division_ref_id:
        division=access.division(order.division_ref_id)
        if division['society_id']!=order.society_ref_id:deny('operational_context_mismatch',409)
        if not order.cost_currency:deny('operational_cost_currency_unavailable',409)
        frozen=(order.commercial_terms_snapshot or {}).get('division')
        if not isinstance(frozen,dict) or not frozen.get('code') or not frozen.get('name'):deny('operational_context_mismatch',409)
        context=OperationalContext(division_ref_id=order.division_ref_id,society_ref_id=order.society_ref_id,division_code=frozen['code'],division_name=frozen['name'],cost_currency=order.cost_currency)
    line=next((line for line in order.lines if line.id==line_id),None)
    if not line:deny('sales_order_line_not_found',404)
    if active and (order.status in ('cancelled','delivered') or order.cancellation_state!='idle'):deny('sales_order_not_fulfillable',409)
    if line.product_service_type!='product':deny('product_fulfillment_required',422)
    return order,line,context

class ProductionSource(BaseModel):
    order_id:str
    order_line_id:str
    product_service_id:str
    quantity:Decimal
    unit:str
    requested_due_date:str|None=None
    organization_context:OperationalContext|None
    request_id:str|None=None
class ProductionSourceResponse(BaseModel):
    data:ProductionSource

@router.get('/orders/{order_id}/production-context',response_model=ProductionSourceResponse)
def production_context(order_id:str=Path(max_length=40),line_id:str=Query(min_length=1,max_length=40),access:OrganizationAccess=Depends(require_organization_access('sales',('sales.order.fulfill','production.order.validate','production.order.release','production.order.start','production.order.resume'))),repository=Depends(get_sales_repository)):
    order,line,context=source_order(repository,access,order_id,line_id)
    pending=line.fulfillment_mode=='pending' and order.fulfillment_state in ('processing','needs_reconciliation')
    intent=repository.production_intent(access.tenant_id,order_id,line_id) if pending else None
    if not (pending and intent and intent.get('mode')=='production') and not (line.fulfillment_mode=='production' and line.production_request_id):deny('sales_production_source_unavailable',409)
    return {'data':{'order_id':order.id,'order_line_id':line.id,'product_service_id':line.product_service_id,'quantity':line.ordered_quantity,'unit':line.unit,'requested_due_date':str(order.promised_delivery_date) if order.promised_delivery_date else None,'organization_context':context,'request_id':line.production_request_id}}

class ProductionReceiptWarehouse(BaseModel):
    warehouse_id:str
    warehouse_code:str
    warehouse_name:str
    inventory_item_id:str
    item_code:str
    item_name:str
    received_quantity:Decimal
    unit:str
    eligible_for_reconciliation:bool
class ProductionStatus(BaseModel):
    order_line_id:str
    request_id:str
    production_order_id:str|None=None
    production_order_status:str|None=None
    request_status:str
    organization_context:OperationalContext|None
    quantity:Decimal
    unit:str
    warehouses:list[ProductionReceiptWarehouse]
    reconciliation_status:str|None=None
class ProductionStatusResponse(BaseModel):
    data:ProductionStatus
class ProductionReconcileRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    order_line_id:str=Field(min_length=1,max_length=40)
    warehouse_id:str=Field(min_length=1,max_length=40)

def production_receipts(repository,authority,access,order_id,line_id):
    from urllib.parse import quote
    order,line,context=source_order(repository,access,order_id,line_id)
    if line.fulfillment_mode!='production' or not line.production_request_id:deny('sales_production_source_unavailable',409)
    source=authority._get(authority.production_url+'/v1/production/order-requests/'+quote(line.production_request_id,safe='')+'/production-status',access.tenant_id,access.authorization)
    expected=context.model_dump(mode='json') if context else None
    try:source_quantity=Decimal(str(source['quantity']))
    except (TypeError,KeyError,ValueError,InvalidOperation):deny('assignment_authority_unavailable',503)
    if not source_quantity.is_finite() or 'organization_context' not in source:deny('assignment_authority_unavailable',503)
    if (not isinstance(source,dict) or source.get('request_id')!=line.production_request_id or source.get('sales_order_id')!=order.id or source.get('sales_order_line_id')!=line.id or source.get('product_service_id')!=line.product_service_id or source.get('unit')!=line.unit or source_quantity!=line.ordered_quantity or source.get('organization_context')!=expected):deny('operational_context_mismatch',409)
    record=repository.production_reconciliation(access.tenant_id,order.id,line.id)
    warehouses=[]
    if source.get('production_order_id'):
        rows=authority._get(authority.inventory_url+'/v1/inventory/finished-goods-receipts/'+quote(source['production_order_id'],safe='')+'/stock-context',access.tenant_id,access.authorization)
        if not isinstance(rows,list):deny('assignment_authority_unavailable',503)
        product=authority.get_product(access.tenant_id,line.product_service_id,access.authorization)
        for row in rows:
            if row.get('inventory_item_id')!=product.inventory_item_id or row.get('unit')!=line.unit or row.get('organization_context')!=expected:continue
            remaining=line.ordered_quantity-line.delivered_quantity
            try:received,available=Decimal(str(row['received_quantity'])),Decimal(str(row['available_quantity']))
            except (KeyError,TypeError,ValueError,InvalidOperation):deny('assignment_authority_unavailable',503)
            if not received.is_finite() or not available.is_finite():deny('assignment_authority_unavailable',503)
            eligible=source.get('production_order_status')=='completed' and received>=remaining and available>=remaining and line.fulfillment_status=='production_requested'
            if record and record['status'] in ('processing','needs_reconciliation'):
                eligible=row['warehouse_id']==record['warehouse_id'] and row['inventory_item_id']==record['inventory_item_id']
            warehouses.append({**row,'eligible_for_reconciliation':eligible})
    record=repository.production_reconciliation(access.tenant_id,order.id,line.id)
    result={'order_line_id':line.id,'request_id':line.production_request_id,'production_order_id':source.get('production_order_id'),'production_order_status':source.get('production_order_status'),'request_status':source['status'],'organization_context':context,'quantity':line.ordered_quantity-line.delivered_quantity,'unit':line.unit,'warehouses':warehouses,'reconciliation_status':record['status'] if record else None}
    return order,line,source,result

@router.get('/orders/{order_id}/production-status',response_model=ProductionStatusResponse)
def production_status(order_id:str=Path(max_length=40),line_id:str=Query(min_length=1,max_length=40),access:OrganizationAccess=Depends(require_organization_access('sales','sales.order.fulfill')),repository=Depends(get_sales_repository),authority=Depends(get_sales_authority_client)):
    return {'data':production_receipts(repository,authority,access,order_id,line_id)[3]}

@router.post('/orders/{order_id}/production-reconciliations',response_model=SalesOrderResponse)
def reconcile_production(payload:ProductionReconcileRequest,order_id:str=Path(max_length=40),idempotency_key:str|None=Header(None,alias='Idempotency-Key',max_length=160),access:OrganizationAccess=Depends(require_organization_access('sales','sales.order.fulfill')),repository=Depends(get_sales_repository),authority=Depends(get_sales_authority_client)):
    key=require_key(idempotency_key);digest=fingerprint(payload,{'order_id':order_id})
    order,line,context=source_order(repository,access,order_id,payload.order_line_id,active=False)
    existing=repository.production_reconciliation(access.tenant_id,order_id,line.id)
    if existing:
        if existing['request_hash']!=digest:deny('production_reconciliation_in_progress',409)
        if existing['status']=='completed':return {'data':order}
        if order.status in ('cancelled','delivered') or order.cancellation_state!='idle':deny('sales_order_not_fulfillable',409)
        record=existing
        product=authority.get_inventory_item(access.tenant_id,record['inventory_item_id'],access.authorization)
    else:
        if order.status in ('cancelled','delivered') or order.cancellation_state!='idle':deny('sales_order_not_fulfillable',409)
        order,line,source,status=production_receipts(repository,authority,access,order_id,line.id)
        if source.get('production_order_status')!='completed':deny('sales_production_not_completed',409)
        warehouse=next((row for row in status['warehouses'] if row['warehouse_id']==payload.warehouse_id and row['eligible_for_reconciliation']),None)
        if not warehouse:deny('sales_production_receipt_required',409,'warehouse_id')
        product=authority.get_inventory_item(access.tenant_id,warehouse['inventory_item_id'],access.authorization)
        record=repository.prepare_production_reconciliation(access.tenant_id,order_id,line.id,payload.warehouse_id,product,source,key,digest)
    try:
        reservation=authority.reserve_stock(access.tenant_id,order_id,line.id,record['inventory_item_id'],record['warehouse_id'],record['quantity'],record['unit'],access.authorization,record['command_key']+'-production-reserve')
        expected=context.model_dump(mode='json') if context else None
        if reservation.get('organization_context')!=expected:deny('operational_context_mismatch',409)
        value=repository.finish_production_reconciliation(access.tenant_id,order_id,line.id,reservation,product,digest,access.actor_id)
    except Exception as exc:
        repository.fail_production_reconciliation(access.tenant_id,line.id,getattr(exc,'code','authority_unavailable'))
        raise
    return {'data':value}
