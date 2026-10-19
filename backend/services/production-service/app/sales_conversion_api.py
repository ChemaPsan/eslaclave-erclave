"""Explicit conversion of an authenticated Sales request into a Production order."""
import hashlib
from decimal import Decimal
from fastapi import APIRouter, Depends, Header, Query
from erclave_common.errors import ErclaveError
from .api import (require_tenant_id,require_idempotency_key,request_fingerprint,_create_order,validate_resources,
    HrWorkerClient,get_hr_worker_client,ResourceAuthorityClient,get_resource_authority_client)
from .authorization import AuthorizedContext,require_production_access
from .repositories import ProductionRepository,get_production_repository
from .schemas import (ProductionSalesRequestResponse,ProductionSalesStatusResponse,ProductionSalesRequestCancel,
    ProductionOrderCreateRequest,ProductionOrderResponse,ResourceValidationRequest,ResourceValidationResponse,RecipeListResponse,SalesProductionOrderCreateRequest,SalesProductionValidationRequest,SalesRequestRecipesResponse)
from .order_context import guard_order,production_access
from .sales_source import SalesSourceClient,get_sales_source_client,validate_source

router=APIRouter(prefix='/v1/production/order-requests')
READ_PERMISSIONS=('production.order.read','production.order.release','sales.order.read','sales.order.fulfill','sales.order.cancel')
VALIDATE_PERMISSIONS=('production.order.validate','production.order.release')

def scoped_request(repository,tenant,id,authorization,permissions,actor,active=False):
    value=repository.get_sales_request(tenant,id)
    if value is None:raise ErclaveError('production_request_not_found','Production request was not found.',status_code=404)
    guard_order(value,tenant,authorization,permissions,actor,active=active)
    return value

def request_payload(repository,tenant,value,payload):
    version=repository.get_recipe_version(tenant,payload.recipe_version_id)
    recipe=repository.get_recipe(tenant,version.recipe_id) if version else None
    division=value.organization_context.division_ref_id if value.organization_context else None
    if not version or not recipe or recipe.product_service_id!=value.product_service_id or Decimal(str(payload.quantity))!=Decimal(str(value.original_quantity if value.original_quantity is not None else value.quantity)) or payload.unit!=value.unit or payload.division_ref_id!=division:
        raise ErclaveError('production_request_source_conflict','Recipe product, quantity, unit and Division must match the request.',status_code=409)
    if isinstance(payload,ProductionOrderCreateRequest):
        if payload.source_id not in (None,value.sales_order_id) or payload.source_line_id not in (None,value.sales_order_line_id) or payload.source_type not in ('manual','sales_order'):
            raise ErclaveError('production_request_source_conflict','Source cannot be replaced.',status_code=409)
        return payload.model_copy(update={'source_type':'sales_order','source_id':value.sales_order_id,'source_line_id':value.sales_order_line_id})
    return payload

@router.get('/{request_id}',response_model=ProductionSalesRequestResponse)
def read_request(request_id:str,x_tenant_id:str|None=Header(None,alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access(READ_PERMISSIONS))):
    return ProductionSalesRequestResponse(data=scoped_request(repository,require_tenant_id(x_tenant_id),request_id,authorization,READ_PERMISSIONS,access.actor_id))

@router.get('/{request_id}/production-status',response_model=ProductionSalesStatusResponse)
def request_status(request_id:str,x_tenant_id:str|None=Header(None,alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access(READ_PERMISSIONS))):
    tenant=require_tenant_id(x_tenant_id)
    scoped_request(repository,tenant,request_id,authorization,READ_PERMISSIONS,access.actor_id)
    return ProductionSalesStatusResponse(data=repository.sales_request_status(tenant,request_id))

@router.get('/{request_id}/recipes',response_model=SalesRequestRecipesResponse)
def request_recipes(request_id:str,q:str=Query('',max_length=120),limit:int=Query(25,ge=1,le=25),offset:int=Query(0,ge=0),x_tenant_id:str|None=Header(None,alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access(VALIDATE_PERMISSIONS))):
    tenant=require_tenant_id(x_tenant_id)
    value=scoped_request(repository,tenant,request_id,authorization,VALIDATE_PERMISSIONS,access.actor_id,active=True)
    return SalesRequestRecipesResponse(**repository.sales_request_recipes(tenant,value,q,limit,offset))

@router.post('/{request_id}/resource-validations',response_model=ResourceValidationResponse)
def request_validation(request_id:str,payload:SalesProductionValidationRequest,x_tenant_id:str|None=Header(None,alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),idempotency_key:str|None=Header(None,alias='Idempotency-Key'),repository:ProductionRepository=Depends(get_production_repository),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),source_client:SalesSourceClient=Depends(get_sales_source_client),access:AuthorizedContext=Depends(require_production_access(VALIDATE_PERMISSIONS))):
    tenant=require_tenant_id(x_tenant_id)
    value=scoped_request(repository,tenant,request_id,authorization,VALIDATE_PERMISSIONS,access.actor_id,active=True)
    if value.status!='pending_configuration':raise ErclaveError('production_request_already_converted','Request is not pending configuration.',status_code=409)
    request_payload(repository,tenant,value,payload)
    validate_source(source_client.proof(tenant,value.sales_order_id,value.sales_order_line_id,authorization),value,tenant,authorization,VALIDATE_PERMISSIONS,access.actor_id)
    return validate_resources(payload,x_tenant_id,authorization,idempotency_key,repository,authorities,access)

@router.post('/{request_id}/orders',response_model=ProductionOrderResponse,status_code=201)
def convert_request(request_id:str,payload:SalesProductionOrderCreateRequest,x_tenant_id:str|None=Header(None,alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),idempotency_key:str|None=Header(None,alias='Idempotency-Key'),repository:ProductionRepository=Depends(get_production_repository),hr_client:HrWorkerClient=Depends(get_hr_worker_client),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),source_client:SalesSourceClient=Depends(get_sales_source_client),access:AuthorizedContext=Depends(require_production_access('production.order.release'))):
    tenant=require_tenant_id(x_tenant_id);key=require_idempotency_key(idempotency_key)
    scoped_request(repository,tenant,request_id,authorization,'production.order.release',access.actor_id)
    with repository.material_command_lock(tenant,'sales-request:'+request_id):
        value=scoped_request(repository,tenant,request_id,authorization,'production.order.release',access.actor_id)
        payload=request_payload(repository,tenant,value,payload)
        attempt='ord_'+hashlib.sha256(f'{tenant}:{key}'.encode()).hexdigest()[:26]
        repository.select_sales_attempt(tenant,request_id,attempt)
        try:
            return _create_order(payload,x_tenant_id,authorization,key,repository,hr_client,authorities,access,sales_request=value,source_client=source_client)
        except Exception:
            repository.release_unstarted_sales_attempt(tenant,request_id,attempt)
            raise

@router.post('/{request_id}/cancel',response_model=ProductionSalesRequestResponse)
def cancel_request(request_id:str,payload:ProductionSalesRequestCancel,x_tenant_id:str|None=Header(None,alias='X-Tenant-Id'),authorization:str|None=Header(None,alias='Authorization'),idempotency_key:str|None=Header(None,alias='Idempotency-Key'),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access('sales.order.cancel'))):
    tenant=require_tenant_id(x_tenant_id);key=require_idempotency_key(idempotency_key)
    scoped_request(repository,tenant,request_id,authorization,'sales.order.cancel',access.actor_id)
    with repository.material_command_lock(tenant,'sales-request:'+request_id):
        scoped_request(repository,tenant,request_id,authorization,'sales.order.cancel',access.actor_id)
        return ProductionSalesRequestResponse(data=repository.cancel_sales_request(tenant,request_id,payload,key,request_fingerprint(payload,{'request_id':request_id}),access.actor_id))
