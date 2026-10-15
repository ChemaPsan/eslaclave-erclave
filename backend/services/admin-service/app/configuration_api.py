from fastapi import APIRouter, Depends, Header
from erclave_common.errors import ErclaveError
from .api import require_idempotency_key, resolve_correlation_id
from .auth import AuthenticatedActor, require_permission_for_header_tenant
from .repositories import AdminRepository, IdempotencyConflictError, get_admin_repository
from .scoped_configuration import ScopeKind, ScopedConfigurationStore, ScopedTemplateCommand, ScopedTemplateResponse, DocumentPresentationResponse, authorize_scope

router = APIRouter(prefix="/v1", tags=["Configuration"])


@router.get("/configuration/document-presentation/division/{division_id}", response_model=DocumentPresentationResponse)
def read_document_presentation(division_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant((
        "sales.quote.read", "sales.quote.approve", "production.order.read", "production.order.release"))),
    repository: AdminRepository = Depends(get_admin_repository)):
    check_scope(repository, actor, x_tenant_id, "division", division_id)
    return {"data": ScopedConfigurationStore(repository).presentation(x_tenant_id, division_id)}


def check_scope(repository, actor, tenant, kind, scope_id):
    if actor is not None:
        authorize_scope(repository.get_session_context_by_email(tenant, actor.email), kind, scope_id)


@router.get("/configuration/document-template/{scope_type}/{scope_id}", response_model=ScopedTemplateResponse)
def read_scoped_template(scope_type: ScopeKind, scope_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.setting.read")),
    repository: AdminRepository = Depends(get_admin_repository)):
    check_scope(repository, actor, x_tenant_id, scope_type, scope_id)
    return {"data": ScopedConfigurationStore(repository).read(x_tenant_id, scope_type, scope_id)}


@router.put("/configuration/document-template/{scope_type}/{scope_id}", response_model=ScopedTemplateResponse)
def write_scoped_template(scope_type: ScopeKind, scope_id: str, payload: ScopedTemplateCommand,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository)):
    check_scope(repository, actor, x_tenant_id, scope_type, scope_id)
    try:
        return {"data": ScopedConfigurationStore(repository).update(x_tenant_id, scope_type, scope_id,
            payload.model_dump(mode="json"), require_idempotency_key(idempotency_key),
            resolve_correlation_id(x_correlation_id), actor.email if actor else None)}
    except IdempotencyConflictError as exc:
        raise ErclaveError("idempotency_key_reused", "Command key conflicts with an earlier request.", 409) from exc
