from fastapi import APIRouter, Depends, Header, Query

from erclave_common.errors import ErclaveError

from .repositories import AdminRepository, get_admin_repository
from .schemas import (
    EntitlementListResponse,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    RoleListResponse,
    TenantResponse,
    UserListResponse,
)


router = APIRouter(prefix="/v1")


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, repository: AdminRepository = Depends(get_admin_repository)) -> TenantResponse:
    tenant = repository.get_tenant(tenant_id)
    if tenant is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": tenant_id})
    return TenantResponse(data=tenant)


@router.get("/tenants/{tenant_id}/entitlements", response_model=EntitlementListResponse)
def list_tenant_entitlements(
    tenant_id: str,
    repository: AdminRepository = Depends(get_admin_repository),
) -> EntitlementListResponse:
    if repository.get_tenant(tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": tenant_id})
    return EntitlementListResponse(data=repository.list_entitlements(tenant_id))


@router.post("/policy/evaluate", response_model=PolicyEvaluateResponse)
def evaluate_policy(
    payload: PolicyEvaluateRequest,
    repository: AdminRepository = Depends(get_admin_repository),
) -> PolicyEvaluateResponse:
    return PolicyEvaluateResponse(
        data=repository.evaluate_policy(
            tenant_id=payload.tenant_id,
            actor_id=payload.actor_id,
            module=payload.module,
            resource=payload.resource,
            action=payload.action,
        )
    )


@router.get("/users", response_model=UserListResponse)
def list_users(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=100),
    repository: AdminRepository = Depends(get_admin_repository),
) -> UserListResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    return UserListResponse(data=repository.list_users(x_tenant_id, limit=limit))


@router.get("/roles", response_model=RoleListResponse)
def list_roles(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=100),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleListResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    return RoleListResponse(data=repository.list_roles(x_tenant_id, limit=limit))
