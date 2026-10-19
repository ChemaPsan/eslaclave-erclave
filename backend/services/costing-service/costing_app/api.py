from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, Header, Query, Path
from .authority import Access, AdminClient, get_admin_client, require_cost_center_access, fail
from .repository import Repository, get_repository
from .schemas import CostCenterCreate, CostCenterUpdate, CostCenterStatus, CostCenterResponse, CostCenterListResponse
router = APIRouter(prefix='/v1', tags=['Cost centers'])

def command_meta(idempotency_key: str | None=Header(None, alias='Idempotency-Key', max_length=160), correlation: str | None=Header(None, alias='X-Correlation-Id', max_length=160)):
    if not idempotency_key or not idempotency_key.strip():
        fail('idempotency_key_required', 400)
    return (idempotency_key, correlation or str(uuid4()))

@router.get('/cost-centers', response_model=CostCenterListResponse)
def list_cost_centers(division_id: str | None=Query(None, min_length=1, max_length=40), q: str=Query('', max_length=240), status: Literal['active', 'inactive'] | None=None, limit: int=Query(25, ge=1, le=100), offset: int=Query(0, ge=0), access: Access=Depends(require_cost_center_access('costing.cost_center.read')), repository: Repository=Depends(get_repository)):
    return repository.list(access, division_id, q, status, limit, offset)

@router.get('/cost-centers/eligible', response_model=CostCenterListResponse)
def eligible_cost_centers(division_id: str=Query(min_length=1, max_length=40), q: str=Query('', max_length=240), limit: int=Query(10, ge=1, le=25), offset: int=Query(0, ge=0), access: Access=Depends(require_cost_center_access('costing.cost_center.read')), repository: Repository=Depends(get_repository)):
    access.require_division(division_id, active=True)
    return repository.list(access, division_id, q, 'active', limit, offset)

@router.post('/cost-centers', response_model=CostCenterResponse, status_code=201)
def create_cost_center(payload: CostCenterCreate, meta: tuple=Depends(command_meta), access: Access=Depends(require_cost_center_access('costing.cost_center.create')), repository: Repository=Depends(get_repository), client: AdminClient=Depends(get_admin_client)):
    return {'data': repository.command(access, 'create', payload.model_dump(), *meta, client)}

@router.get('/cost-centers/{cost_center_id}', response_model=CostCenterResponse)
def get_cost_center(cost_center_id: str=Path(max_length=40), access: Access=Depends(require_cost_center_access('costing.cost_center.read')), repository: Repository=Depends(get_repository)):
    return {'data': repository.read(access, cost_center_id)}

@router.patch('/cost-centers/{cost_center_id}', response_model=CostCenterResponse)
def update_cost_center(payload: CostCenterUpdate, cost_center_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: Access=Depends(require_cost_center_access('costing.cost_center.update')), repository: Repository=Depends(get_repository), client: AdminClient=Depends(get_admin_client)):
    return {'data': repository.command(access, 'update', payload.model_dump(), *meta, client, id_=cost_center_id)}

@router.post('/cost-centers/{cost_center_id}/activate', response_model=CostCenterResponse)
def activate_cost_center(payload: CostCenterStatus, cost_center_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: Access=Depends(require_cost_center_access('costing.cost_center.status')), repository: Repository=Depends(get_repository), client: AdminClient=Depends(get_admin_client)):
    return {'data': repository.command(access, 'activate', payload.model_dump(), *meta, client, id_=cost_center_id)}

@router.post('/cost-centers/{cost_center_id}/deactivate', response_model=CostCenterResponse)
def deactivate_cost_center(payload: CostCenterStatus, cost_center_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: Access=Depends(require_cost_center_access('costing.cost_center.status')), repository: Repository=Depends(get_repository), client: AdminClient=Depends(get_admin_client)):
    return {'data': repository.command(access, 'deactivate', payload.model_dump(), *meta, client, id_=cost_center_id)}
