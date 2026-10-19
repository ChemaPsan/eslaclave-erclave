from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, Header, Query, Path
from erclave_common.organization_client import OrganizationAccess, OrganizationClient, get_organization_client, require_organization_access, deny
from .repositories import get_hr_repository
from .organization_store import OrganizationStore
from .organization_schemas import (PositionDivisionCommand, WorkerDivisionCommand, PositionDivisionResponse, WorkerDivisionResponse, PositionDivisionListResponse, WorkerDivisionListResponse, DivisionChoicesResponse, EligiblePositionsResponse, EligibleWorkersResponse, DivisionProductionCapacityResponse)
router = APIRouter(prefix='/v1/hr', tags=['Organization assignments'])
def require_hr_organization(permission):
    return require_organization_access('hr', permission)
def store(repository=Depends(get_hr_repository)):
    return OrganizationStore(repository)
def command_meta(key: str | None=Header(None, alias='Idempotency-Key', max_length=160), correlation: str | None=Header(None, alias='X-Correlation-Id', max_length=128)):
    if not key or len(key.strip()) < 8:
        deny('idempotency_key_required', 400)
    return key.strip(), correlation or str(uuid4())
@router.get('/organization/divisions', response_model=DivisionChoicesResponse)
def divisions(q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_hr_organization(('hr.position.read', 'hr.worker.read')))):
    rows = sorted((row for row in access.divisions if q.casefold() in (row['code'] + ' ' + row['name']).casefold()), key=lambda row: row['code'])
    return {'data': rows[offset:offset + limit], 'meta': {'total': len(rows), 'limit': limit, 'offset': offset}}

@router.get('/positions/{resource_id}/division-assignments', response_model=PositionDivisionListResponse)
def position_divisions(resource_id: str=Path(max_length=40), division_id: str | None=Query(None, min_length=1, max_length=40), limit: int=Query(25, ge=1, le=100), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_hr_organization('hr.position.read')), repository: OrganizationStore=Depends(store)):
    return repository.assignments(access, 'position', resource_id, limit, offset, division_id)
@router.put('/positions/{resource_id}/division-assignments/{division_id}', response_model=PositionDivisionResponse)
def assign_position(payload: PositionDivisionCommand, resource_id: str=Path(max_length=40), division_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_hr_organization('hr.position.update')), repository: OrganizationStore=Depends(store), client: OrganizationClient=Depends(get_organization_client)):
    return {'data': repository.save(access, 'position', resource_id, division_id, payload, *meta, client)}
@router.get('/division-positions', response_model=EligiblePositionsResponse)
def eligible_positions(division_id: str=Query(min_length=1, max_length=40), purpose: Literal['all','production','maintenance']=Query('all'), q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_hr_organization('hr.position.read')), repository: OrganizationStore=Depends(store)):
    return repository.eligible(access, 'position', division_id, purpose, q, limit, offset)

@router.get('/workers/{resource_id}/division-assignments', response_model=WorkerDivisionListResponse)
def worker_divisions(resource_id: str=Path(max_length=40), division_id: str | None=Query(None, min_length=1, max_length=40), limit: int=Query(25, ge=1, le=100), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(require_hr_organization('hr.worker.read')), repository: OrganizationStore=Depends(store)):
    return repository.assignments(access, 'worker', resource_id, limit, offset, division_id)
@router.put('/workers/{resource_id}/division-assignments/{division_id}', response_model=WorkerDivisionResponse)
def assign_worker(payload: WorkerDivisionCommand, resource_id: str=Path(max_length=40), division_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_hr_organization('hr.worker.update')), repository: OrganizationStore=Depends(store), client: OrganizationClient=Depends(get_organization_client)):
    return {'data': repository.save(access, 'worker', resource_id, division_id, payload, *meta, client)}
from erclave_common.config import Settings, get_settings

def worker_lookup_access(purpose: Literal['all','production','maintenance']=Query('all'), x_tenant_id: str | None=Header(None, alias='X-Tenant-Id'), authorization: str | None=Header(None, alias='Authorization'), x_actor_id: str | None=Header(None, alias='X-Actor-Id'), settings: Settings=Depends(get_settings), client: OrganizationClient=Depends(get_organization_client)):
    permissions = ('hr.worker.read', 'sales.quote.update', 'sales.quote.submit', 'sales.quote.approve','sales.order.create','sales.service_order.plan','sales.service_order.assign','sales.service_order.start','sales.service_order.resume','sales.service_order.submit_acceptance','sales.service_order.accept','sales.service_order.time.create','sales.service_order.cost.create','sales.service_order.evidence.create')
    if purpose == 'production':
        permissions = ('hr.worker.read', 'production.order.validate', 'production.order.release', 'production.order.start', 'production.order.resume')
    elif purpose == 'maintenance':
        permissions = ('hr.worker.read', 'maintenance.order.assign', 'maintenance.order.start', 'maintenance.order.resume', 'maintenance.order.reopen', 'maintenance.time.create')
    return require_hr_organization(permissions)(x_tenant_id, authorization, x_actor_id, settings, client)

@router.get('/division-workers', response_model=EligibleWorkersResponse)
def eligible_workers(division_id: str=Query(min_length=1, max_length=40), purpose: Literal['all','production','maintenance']=Query('all'), resource_id: str | None=Query(None, min_length=1, max_length=40), q: str=Query('', max_length=240), limit: int=Query(20, ge=1, le=25), offset: int=Query(0, ge=0), access: OrganizationAccess=Depends(worker_lookup_access), repository: OrganizationStore=Depends(store)):
    return repository.eligible(access, 'worker', division_id, purpose, q, limit, offset, resource_id)

@router.get('/division-production-capacity', response_model=DivisionProductionCapacityResponse)
def division_production_capacity(division_id: str=Query(min_length=1, max_length=40), access: OrganizationAccess=Depends(require_hr_organization(('hr.position.read', 'production.order.validate', 'production.order.release'))), repository: OrganizationStore=Depends(store)):
    return repository.division_production_capacity(access, division_id)
