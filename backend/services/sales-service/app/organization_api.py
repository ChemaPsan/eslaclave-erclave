from uuid import uuid4
from fastapi import APIRouter, Depends, Header, Query, Path
from erclave_common.organization_client import OrganizationAccess, require_organization_access, deny
from .repositories import get_sales_repository
from .organization_store import OrganizationStore
from .organization_schemas import AssignmentCommand, AssignmentResponse, AssignmentListResponse, DivisionChoicesResponse, EligiblePartiesResponse
router=APIRouter(prefix='/v1/sales',tags=['Organization assignments'])
def require_sales_organization(permission):return require_organization_access('sales',permission)
def store(repository=Depends(get_sales_repository)):return OrganizationStore(repository)
def command_meta(key: str | None=Header(None,alias='Idempotency-Key',max_length=160),correlation: str | None=Header(None,alias='X-Correlation-Id',max_length=128)):
    if not key or len(key.strip())<8:deny('idempotency_key_required',400)
    return key.strip(),correlation or str(uuid4())
@router.get('/organization/divisions',response_model=DivisionChoicesResponse)
def divisions(q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_sales_organization('sales.customer.read'))):
    rows=sorted((row for row in access.divisions if q.casefold() in (row['code']+' '+row['name']).casefold()),key=lambda row:row['code'])
    return {'data':rows[offset:offset+limit],'meta':{'total':len(rows),'limit':limit,'offset':offset}}
@router.get('/customers/{resource_id}/division-assignments',response_model=AssignmentListResponse)
def assignments(resource_id: str=Path(max_length=40),division_id: str | None=Query(None,min_length=1,max_length=40),limit: int=Query(25,ge=1,le=100),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_sales_organization('sales.customer.read')),repository: OrganizationStore=Depends(store)):
    return repository.assignments(access,resource_id,limit,offset,division_id)
@router.put('/customers/{resource_id}/division-assignments/{division_id}',response_model=AssignmentResponse)
def assign(payload: AssignmentCommand,resource_id: str=Path(max_length=40),division_id: str=Path(max_length=40),meta: tuple=Depends(command_meta),access: OrganizationAccess=Depends(require_sales_organization('sales.customer.update')),repository: OrganizationStore=Depends(store)):
    return {'data':repository.save(access,resource_id,division_id,payload,*meta)}
@router.get('/division-customers',response_model=EligiblePartiesResponse)
def eligible(division_id: str=Query(min_length=1,max_length=40),q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_sales_organization('sales.customer.read')),repository: OrganizationStore=Depends(store)):
    return repository.eligible(access,division_id,q,limit,offset)

from .commercial_terms_schemas import CommercialTermsCommand, CommercialTermsResponse
from .commercial_terms_store import CommercialTermsStore
from .authorities import get_sales_authority_client

def terms_store(repository=Depends(get_sales_repository)):
    return CommercialTermsStore(repository)

@router.get('/customers/{resource_id}/division-assignments/{division_id}/commercial-terms', response_model=CommercialTermsResponse)
def commercial_terms(resource_id: str=Path(max_length=40), division_id: str=Path(max_length=40), access: OrganizationAccess=Depends(require_sales_organization('sales.customer.read')), repository: CommercialTermsStore=Depends(terms_store)):
    return {'data': repository.read(access, resource_id, division_id)}

@router.put('/customers/{resource_id}/division-assignments/{division_id}/commercial-terms', response_model=CommercialTermsResponse)
def save_commercial_terms(payload: CommercialTermsCommand, resource_id: str=Path(max_length=40), division_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_sales_organization('sales.customer.update')), repository: CommercialTermsStore=Depends(terms_store), authority=Depends(get_sales_authority_client)):
    return {'data': repository.save(access, resource_id, division_id, payload, *meta, authority)}

from .quote_context import QuoteContextCommand, QuoteContextStore
from .schemas import QuoteResponse

@router.get('/organization/quote-divisions', response_model=DivisionChoicesResponse)
def quote_divisions(q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_sales_organization('sales.quote.update'))):
    rows=sorted((row for row in access.divisions if q.casefold() in (row['code']+' '+row['name']).casefold()),key=lambda row:row['code'])
    return {'data':rows[offset:offset+limit],'meta':{'total':len(rows),'limit':limit,'offset':offset}}

@router.put('/quotes/{quote_id}/organization-context',response_model=QuoteResponse)
def assign_quote_context(payload: QuoteContextCommand,quote_id: str=Path(max_length=40),meta: tuple=Depends(command_meta),access: OrganizationAccess=Depends(require_sales_organization('sales.quote.update')),repository=Depends(get_sales_repository),authority=Depends(get_sales_authority_client)):
    return {'data':QuoteContextStore(repository).save(access,quote_id,payload,*meta,authority)}

from urllib.parse import urlencode
from erclave_common.organization_client import deny
from pydantic import BaseModel

class ServiceWorkerChoice(BaseModel):
    id: str
    employee_number: str
    full_name: str
    position_name: str
    division_ref_id: str

class ServiceWorkerChoices(BaseModel):
    data: list[ServiceWorkerChoice]
    has_more: bool

@router.get('/service-orders/{service_order_id}/eligible-workers',response_model=ServiceWorkerChoices)
def service_workers(service_order_id: str=Path(max_length=40),q: str=Query('',max_length=240),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_sales_organization(('sales.service_order.assign','sales.service_order.time.create'))),repository=Depends(get_sales_repository),authority=Depends(get_sales_authority_client)):
    value=repository.get_service_order(access.tenant_id,service_order_id)
    if not value:deny('service_order_not_found',404)
    if not value.division_ref_id:deny('quote_context_unavailable',409)
    division=access.division(value.division_ref_id)
    if division['society_id']!=value.society_ref_id:deny('quote_context_unavailable',409)
    rows=authority._get(authority.hr_url+'/v1/hr/division-workers?'+urlencode({'division_id':value.division_ref_id,'q':q,'offset':offset,'limit':21}),access.tenant_id,access.authorization)
    if not isinstance(rows,list):deny('authority_unavailable',503)
    return {'data':[row for row in rows[:20] if row.get('division_ref_id')==value.division_ref_id],'has_more':len(rows)>20}

from erclave_common.operational_context import OperationalContext

class OrderExecutionContext(BaseModel):
    order_id: str
    order_line_id: str
    organization_context: OperationalContext | None
    allocation: dict | None = None

class OrderExecutionContextResponse(BaseModel):
    data: OrderExecutionContext

@router.get('/orders/{order_id}/execution-context', response_model=OrderExecutionContextResponse, response_model_exclude_unset=True)
def order_execution_context(order_id: str=Path(max_length=40), line_id: str=Query(min_length=1,max_length=40), access: OrganizationAccess=Depends(require_sales_organization('sales.order.fulfill')), repository=Depends(get_sales_repository)):
    value=repository.get_order(access.tenant_id,order_id)
    if not value:deny('sales_order_not_found',404)
    if value.division_ref_id:
        division=access.division(value.division_ref_id)
        if division['society_id']!=value.society_ref_id:deny('operational_context_mismatch',409)
    line=next((line for line in value.lines if line.id==line_id),None)
    if not line:deny('sales_order_line_not_found',404)
    if value.status in ('cancelled','delivered') or value.cancellation_state!='idle':deny('sales_order_not_fulfillable',409)
    if line.product_service_type!='product':deny('product_fulfillment_required',422)
    reconciliation=repository.production_reconciliation(access.tenant_id,order_id,line_id) if hasattr(repository,'production_reconciliation') else None
    if value.division_ref_id and (not value.cost_currency or (value.fulfillment_state not in ('processing','needs_reconciliation') and not reconciliation)):deny('sales_order_not_fulfillable',409)
    snapshot=None
    if value.division_ref_id:
        frozen=(value.commercial_terms_snapshot or {}).get('division')
        if not isinstance(frozen,dict) or not frozen.get('code') or not frozen.get('name'):deny('operational_context_mismatch',409)
        snapshot=OperationalContext(division_ref_id=value.division_ref_id,society_ref_id=value.society_ref_id,division_code=frozen['code'],division_name=frozen['name'],cost_currency=value.cost_currency)
    allocation=None
    if reconciliation:
        allocation={'line_id':line.id,'inventory_item_id':reconciliation['inventory_item_id'],'warehouse_id':reconciliation['warehouse_id'],'quantity':str(reconciliation['quantity']),'unit':reconciliation['unit']}
    return {'data':{'order_id':value.id,'order_line_id':line.id,'organization_context':snapshot,**({'allocation':allocation} if allocation else {})}}

class StockWarehouseChoice(BaseModel):
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    available_quantity: str | float

class SalesStockChoices(BaseModel):
    inventory_item_id: str
    item_code: str
    item_name: str
    unit: str
    cost_currency: str
    warehouses: list[StockWarehouseChoice]
    has_more: bool

class SalesStockChoicesResponse(BaseModel):
    data: SalesStockChoices

@router.get('/orders/{order_id}/stock-options',response_model=SalesStockChoicesResponse)
def stock_options(order_id: str=Path(max_length=40),line_id: str=Query(min_length=1,max_length=40),q: str=Query('',max_length=240),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_sales_organization('sales.order.fulfill')),repository=Depends(get_sales_repository),authority=Depends(get_sales_authority_client)):
    order=repository.get_order(access.tenant_id,order_id)
    if not order:deny('sales_order_not_found',404)
    if not order.division_ref_id:deny('quote_context_unavailable',409)
    division=access.division(order.division_ref_id)
    if division['society_id']!=order.society_ref_id:deny('operational_context_mismatch',409)
    line=next((line for line in order.lines if line.id==line_id),None)
    if not line:deny('sales_order_line_not_found',404)
    if line.product_service_type!='product':deny('product_fulfillment_required',422)
    product=authority.get_product(access.tenant_id,line.product_service_id,access.authorization)
    if not product.inventory_item_id:deny('product_inventory_mapping_mismatch',422)
    result=authority._get(authority.inventory_url+'/v1/inventory/division-stock?'+urlencode({'division_id':order.division_ref_id,'inventory_item_id':product.inventory_item_id,'q':q,'offset':offset}),access.tenant_id,access.authorization)
    if not isinstance(result,dict) or result.get('inventory_item_id')!=product.inventory_item_id:deny('assignment_authority_unavailable',503)
    return {'data':result}
