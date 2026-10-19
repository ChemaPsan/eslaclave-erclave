"""Membership scope editor. No organization grant is inferred from a role name."""
from fastapi import APIRouter, Depends, Header
from erclave_common.errors import ErclaveError
from .api import require_idempotency_key, resolve_correlation_id
from .auth import AuthenticatedActor, require_permission_for_header_tenant
from .repositories import AdminRepository, IdempotencyConflictError, get_admin_repository
from .organization_scope import ScopeStore, ScopeUpdate, ScopeResponse

router = APIRouter(prefix="/v1", tags=["Users"])


@router.get("/users/{user_id}/organization-scope", response_model=ScopeResponse)
def get_user_organization_scope(user_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.user.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return {"data": ScopeStore(repository).read(x_tenant_id, user_id)}


@router.put("/users/{user_id}/organization-scope", response_model=ScopeResponse)
def update_user_organization_scope(user_id: str, payload: ScopeUpdate,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.user.update")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    try:
        return {"data": ScopeStore(repository).update(x_tenant_id, user_id, payload.model_dump(),
            require_idempotency_key(idempotency_key), resolve_correlation_id(x_correlation_id), actor.email if actor else None)}
    except IdempotencyConflictError as exc:
        raise ErclaveError("idempotency_key_reused", "Command key conflicts with an earlier request.", 409) from exc
