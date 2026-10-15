from uuid import uuid4
from fastapi import APIRouter, Depends, Header, Query, Path
from erclave_common.organization_client import OrganizationAccess, OrganizationClient, get_organization_client, require_organization_access, deny
from .repositories import get_production_repository
from .organization_store import OrganizationStore
from .organization_schemas import MachineDivisionCommand, MachineDivisionResponse, ProductServiceDivisionCommand, ProductServiceDivisionResponse, ProductServiceDivisionListResponse, ProductServiceEstimatedCostCommand, ProductServiceEstimatedCostResponse, DivisionChoicesResponse, EligibleProductServicesResponse
router = APIRouter(prefix='/v1/production', tags=['Organization assignments'])

def require_production_organization(permission):
    return require_organization_access('production', permission)

def store(repository=Depends(get_production_repository)):
    return OrganizationStore(repository)

def command_meta(key: str | None=Header(None, alias='Idempotency-Key', max_length=160), correlation: str | None=Header(None, alias='X-Correlation-Id', max_length=128)):
    if not key or len(key.strip()) < 8:
        deny('idempotency_key_required', 400)
    return (key.strip(), correlation or str(uuid4()))

@router.get('/organization/divisions', response_model=DivisionChoicesResponse)
def divisions(q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_production_organization(('production.machine.read', 'production.product_service.read')))):
    rows = sorted((row for row in access.divisions if q.casefold() in (row['code'] + ' ' + row['name']).casefold()), key=lambda row: row['code'])
    return {'data': rows[offset:offset + limit], 'meta': {'total': len(rows), 'limit': limit, 'offset': offset}}

@router.get('/machines/{machine_id}/division', response_model=MachineDivisionResponse)
def machine_division(machine_id: str=Path(max_length=40), access: OrganizationAccess=Depends(require_production_organization('production.machine.read')), repository: OrganizationStore=Depends(store)):
    return {'data': repository.machine(access, machine_id)}

@router.patch('/machines/{machine_id}/division', response_model=MachineDivisionResponse)
def assign_machine(payload: MachineDivisionCommand, machine_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_production_organization('production.machine.update')), repository: OrganizationStore=Depends(store), client: OrganizationClient=Depends(get_organization_client)):
    return {'data': repository.save(access, 'machine', machine_id, payload.division_ref_id, payload, *meta, client)}

@router.get('/product-services/{product_service_id}/division-assignments', response_model=ProductServiceDivisionListResponse)
def product_service_divisions(product_service_id: str=Path(max_length=40), division_id: str | None=Query(None, min_length=1, max_length=40), limit: int=Query(25, ge=1, le=100), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_production_organization('production.product_service.read')), repository: OrganizationStore=Depends(store)):
    return repository.products(access, product_service_id, limit, offset, division_id)

@router.put('/product-services/{product_service_id}/division-assignments/{division_id}', response_model=ProductServiceDivisionResponse)
def assign_item(payload: ProductServiceDivisionCommand, product_service_id: str=Path(max_length=40), division_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_production_organization('production.product_service.update')), repository: OrganizationStore=Depends(store), client: OrganizationClient=Depends(get_organization_client)):
    return {'data': repository.save(access, 'product_service', product_service_id, division_id, payload, *meta, client)}

@router.put('/product-services/{product_service_id}/division-assignments/{division_id}/estimated-unit-cost',response_model=ProductServiceDivisionResponse)
def confirm_product_estimated_cost(payload: ProductServiceEstimatedCostCommand,product_service_id: str=Path(max_length=40),division_id: str=Path(max_length=40),meta: tuple=Depends(command_meta),access: OrganizationAccess=Depends(require_production_organization('production.product_service.update')),repository: OrganizationStore=Depends(store)):
    return {'data':repository.confirm_estimated_cost(access,product_service_id,division_id,payload,*meta)}

@router.get('/division-product-services/{product_service_id}/estimated-cost',response_model=ProductServiceEstimatedCostResponse)
def product_estimated_cost(product_service_id: str=Path(max_length=40),division_id: str=Query(min_length=1,max_length=40),access: OrganizationAccess=Depends(require_production_organization(('production.product_service.read','sales.quote.update','sales.quote.submit','sales.quote.approve'))),repository: OrganizationStore=Depends(store)):
    return {'data':repository.estimated_cost(access,product_service_id,division_id)}

@router.get('/division-product-services', response_model=EligibleProductServicesResponse)
def division_items(division_id: str=Query(min_length=1, max_length=40), resource_id: str | None=Query(None, min_length=1, max_length=40), q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_production_organization(('production.product_service.read', 'sales.quote.update', 'sales.quote.submit', 'sales.quote.approve','sales.order.create','sales.order.fulfill','sales.service_order.plan','sales.service_order.assign','sales.service_order.start','sales.service_order.resume','sales.service_order.submit_acceptance','sales.service_order.accept','sales.service_order.time.create','sales.service_order.cost.create','sales.service_order.evidence.create'))), repository: OrganizationStore=Depends(store)):
    return repository.eligible(access, division_id, q, limit, offset, resource_id)


from .schemas import ProductionReservationContextResponse

@router.get('/orders/{order_id}/reservation-context',response_model=ProductionReservationContextResponse)
def reservation_context(order_id: str=Path(max_length=40), line_id: str=Query(min_length=1,max_length=160), access: OrganizationAccess=Depends(require_production_organization('production.order.release')), repository=Depends(get_production_repository)):
    value=repository.creation_context(access.tenant_id,order_id,access.actor_id,line_id)
    if value:
        from erclave_common.operational_context import OperationalContext
        OperationalContext.model_validate(value['organization_context']).authorize(access)
    return {'data':value}

from datetime import date
from .machine_capacity import MachineCapacityStore
from .organization_schemas import EligibleMachinesResponse

@router.get('/division-machines', response_model=EligibleMachinesResponse)
def division_machines(division_id: str=Query(min_length=1,max_length=40), planned_date: date=Query(...), resource_id: str | None=Query(None,min_length=1,max_length=40), q: str=Query('',max_length=240), limit: int=Query(20,ge=1,le=25), offset: int=Query(0,ge=0), access: OrganizationAccess=Depends(require_production_organization(('production.machine.read','production.order.validate','production.order.release'))), repository=Depends(get_production_repository)):
    """Confirmed Society-base tariffs and globally committed machine minutes; read only."""
    return MachineCapacityStore(repository).eligible(access,division_id,planned_date,q,limit,offset,resource_id)

from .organization_schemas import EligibleRecipesResponse

@router.get('/division-recipes',response_model=EligibleRecipesResponse)
def division_recipes(division_id: str=Query(min_length=1,max_length=40), q: str=Query('',max_length=240), limit: int=Query(20,ge=1,le=25), offset: int=Query(0,ge=0), access: OrganizationAccess=Depends(require_production_organization(('production.recipe.read','production.order.validate','production.order.release'))), repository=Depends(get_production_repository)):
    return repository.division_recipes(access,division_id,q,limit,offset)
