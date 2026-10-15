"""Admin owns the cost-center numbering authority, not the cost-center records."""
from fastapi import APIRouter, Depends, Header
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError
from .auth import AuthenticatedActor, require_permission_for_header_tenant
from .capabilities import capability_availability
from .api import require_idempotency_key, resolve_correlation_id
from .repositories import AdminRepository, IdempotencyConflictError, get_admin_repository
from .schemas import CodeSequenceNextRequest, CodeSequenceAllocationResponse
router = APIRouter(prefix='/v1', tags=['Code sequences'])

@router.post('/cost-center-codes/next', response_model=CodeSequenceAllocationResponse)
def allocate_cost_center_code(x_tenant_id: str=Header(alias='X-Tenant-Id'), idempotency_key: str | None=Header(None, alias='Idempotency-Key', max_length=160), x_correlation_id: str | None=Header(None, alias='X-Correlation-Id', max_length=160), x_actor_id: str | None=Header(None, alias='X-Actor-Id'), settings: Settings=Depends(get_settings), actor: AuthenticatedActor | None=Depends(require_permission_for_header_tenant('costing.cost_center.create')), repository: AdminRepository=Depends(get_admin_repository)):
    if not settings.cost_center_catalog_enabled:
        raise ErclaveError('module_not_enabled', 'Basic cost-center catalog is not enabled.', 403)
    context = repository.get_session_context_by_email(x_tenant_id, actor.email) if actor else repository.get_session_context(x_tenant_id, x_actor_id) if x_actor_id else None
    if context is None or not capability_availability(context, catalog_enabled=settings.cost_center_catalog_enabled)['cost_center_catalog']['available']:
        raise ErclaveError('module_not_enabled', 'Catalog authority is unavailable for this identity.', 403)
    if 'costing.cost_center.create' not in context.permissions:
        raise ErclaveError('permission_denied', 'Catalog creation permission is required.', 403)
    try:
        result = repository.allocate_business_code(x_tenant_id, 'costing.cost_center', CodeSequenceNextRequest(), require_idempotency_key(idempotency_key), resolve_correlation_id(x_correlation_id), actor.email if actor else None)
        return {'data': result}
    except IdempotencyConflictError as exc:
        raise ErclaveError('idempotency_key_reused', 'Command conflicts with previous request.', 409) from exc
    except ValueError as exc:
        raise ErclaveError('cost_center_managed_code_required', 'Configure an active managed cost-center sequence.', 409) from exc
