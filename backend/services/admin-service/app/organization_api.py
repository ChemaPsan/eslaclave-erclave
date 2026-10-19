"""CONT-02 organization contracts. All commands are permissioned and idempotent."""
from typing import Literal
from fastapi import APIRouter, Depends, Header, Query
from erclave_common.errors import ErclaveError
from .api import require_idempotency_key, resolve_correlation_id
from .auth import AuthenticatedActor, require_permission_for_header_tenant
from .repositories import AdminRepository, IdempotencyConflictError, get_admin_repository
from .organization_migration import OrganizationMigrationError
from .organization_store import OrganizationStore
from .organization_schemas import (
    FiscalIssuerCreate, FiscalIssuerUpdate, FiscalIssuerResponse, FiscalIssuerList,
    SocietyCreate, SocietyUpdate, SocietyResponse, SocietyList,
    DivisionCreate, DivisionUpdate, DivisionResponse, DivisionList,
)

router = APIRouter(prefix="/v1/organization", tags=["Organization"])


def command(repository, tenant, kind, payload, record_id, action, key, correlation, actor):
    try:
        return {"data": OrganizationStore(repository).command(tenant, kind, payload, record_id, action,
            require_idempotency_key(key), resolve_correlation_id(correlation), actor.email if actor else None)}
    except IdempotencyConflictError as exc:
        raise ErclaveError("idempotency_key_reused", "Use the same request with its command key.", 409) from exc
    except OrganizationMigrationError as exc:
        raise ErclaveError("organization_review_required", "Organization requires a reviewed transition.", 409) from exc


@router.get("/fiscal-issuers", response_model=FiscalIssuerList)
def list_fiscal_issuers(
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    q: str = Query(default="", max_length=240),
    status: Literal["active", "inactive"] | None = None,
    parent_id: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100), offset: int = Query(default=0, ge=0),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.fiscal_issuer.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return OrganizationStore(repository).list(x_tenant_id, "fiscal-issuers", q=q, status=status, parent_id=parent_id, limit=limit, offset=offset)


@router.get("/fiscal-issuers/{record_id}", response_model=FiscalIssuerResponse)
def get_fiscal_issuer(record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.fiscal_issuer.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return {"data": OrganizationStore(repository).get(x_tenant_id, "fiscal-issuers", record_id)}


@router.post("/fiscal-issuers", response_model=FiscalIssuerResponse, status_code=201)
def create_fiscal_issuer(
    payload: FiscalIssuerCreate,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.fiscal_issuer.create")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "fiscal-issuers", payload.model_dump(), None, "create", idempotency_key, x_correlation_id, actor)


@router.patch("/fiscal-issuers/{record_id}", response_model=FiscalIssuerResponse)
def update_fiscal_issuer(
    payload: FiscalIssuerUpdate,
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.fiscal_issuer.update")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "fiscal-issuers", payload.model_dump(exclude_unset=True), record_id, "update", idempotency_key, x_correlation_id, actor)


@router.post("/fiscal-issuers/{record_id}/activate", response_model=FiscalIssuerResponse)
def activate_fiscal_issuer(
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.fiscal_issuer.status")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "fiscal-issuers", {"status": "active"}, record_id, "activate", idempotency_key, x_correlation_id, actor)


@router.post("/fiscal-issuers/{record_id}/deactivate", response_model=FiscalIssuerResponse)
def deactivate_fiscal_issuer(
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.fiscal_issuer.status")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "fiscal-issuers", {"status": "inactive"}, record_id, "deactivate", idempotency_key, x_correlation_id, actor)


@router.get("/societies", response_model=SocietyList)
def list_societys(
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    q: str = Query(default="", max_length=240),
    status: Literal["active", "inactive"] | None = None,
    parent_id: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100), offset: int = Query(default=0, ge=0),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.society.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return OrganizationStore(repository).list(x_tenant_id, "societies", q=q, status=status, parent_id=parent_id, limit=limit, offset=offset)


@router.get("/societies/{record_id}", response_model=SocietyResponse)
def get_society(record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.society.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return {"data": OrganizationStore(repository).get(x_tenant_id, "societies", record_id)}


@router.post("/societies", response_model=SocietyResponse, status_code=201)
def create_society(
    payload: SocietyCreate,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.society.create")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "societies", payload.model_dump(), None, "create", idempotency_key, x_correlation_id, actor)


@router.patch("/societies/{record_id}", response_model=SocietyResponse)
def update_society(
    payload: SocietyUpdate,
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.society.update")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "societies", payload.model_dump(exclude_unset=True), record_id, "update", idempotency_key, x_correlation_id, actor)


@router.post("/societies/{record_id}/activate", response_model=SocietyResponse)
def activate_society(
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.society.status")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "societies", {"status": "active"}, record_id, "activate", idempotency_key, x_correlation_id, actor)


@router.post("/societies/{record_id}/deactivate", response_model=SocietyResponse)
def deactivate_society(
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.society.status")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "societies", {"status": "inactive"}, record_id, "deactivate", idempotency_key, x_correlation_id, actor)


@router.get("/divisions", response_model=DivisionList)
def list_divisions(
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    q: str = Query(default="", max_length=240),
    status: Literal["active", "inactive"] | None = None,
    parent_id: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100), offset: int = Query(default=0, ge=0),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.division.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return OrganizationStore(repository).list(x_tenant_id, "divisions", q=q, status=status, parent_id=parent_id, limit=limit, offset=offset)


@router.get("/divisions/{record_id}", response_model=DivisionResponse)
def get_division(record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    _actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.division.read")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return {"data": OrganizationStore(repository).get(x_tenant_id, "divisions", record_id)}


@router.post("/divisions", response_model=DivisionResponse, status_code=201)
def create_division(
    payload: DivisionCreate,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.division.create")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "divisions", payload.model_dump(), None, "create", idempotency_key, x_correlation_id, actor)


@router.patch("/divisions/{record_id}", response_model=DivisionResponse)
def update_division(
    payload: DivisionUpdate,
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.division.update")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "divisions", payload.model_dump(exclude_unset=True), record_id, "update", idempotency_key, x_correlation_id, actor)


@router.post("/divisions/{record_id}/activate", response_model=DivisionResponse)
def activate_division(
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.division.status")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "divisions", {"status": "active"}, record_id, "activate", idempotency_key, x_correlation_id, actor)


@router.post("/divisions/{record_id}/deactivate", response_model=DivisionResponse)
def deactivate_division(
    record_id: str,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.division.status")),
    repository: AdminRepository = Depends(get_admin_repository),
):
    return command(repository, x_tenant_id, "divisions", {"status": "inactive"}, record_id, "deactivate", idempotency_key, x_correlation_id, actor)
