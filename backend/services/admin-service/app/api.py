from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, status

from erclave_common.errors import ErclaveError

from .repositories import AdminRepository, get_admin_repository
from .schemas import (
    EntitlementListResponse,
    EntitlementResponse,
    EntitlementUpsertRequest,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    PermissionListResponse,
    RoleCreateRequest,
    RoleListResponse,
    RolePermissionsReplaceRequest,
    RoleResponse,
    RoleUpdateRequest,
    TenantResponse,
    UserInvitationRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)


router = APIRouter(prefix="/v1")


def require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key or len(idempotency_key.strip()) < 8:
        raise ErclaveError(
            "idempotency_key_required",
            "Idempotency-Key header is required for this command.",
            status_code=400,
        )
    return idempotency_key.strip()


def resolve_correlation_id(correlation_id: str | None) -> str:
    return correlation_id.strip() if correlation_id else f"cor_{uuid4().hex[:26]}"


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


@router.put("/tenants/{tenant_id}/entitlements/{module_code}", response_model=EntitlementResponse)
def upsert_tenant_entitlement(
    tenant_id: str,
    module_code: str,
    payload: EntitlementUpsertRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> EntitlementResponse:
    if repository.get_tenant(tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": tenant_id})
    entitlement = repository.upsert_entitlement(
        tenant_id=tenant_id,
        module_code=module_code,
        status=payload.status,
        limits=payload.limits,
        source=payload.source,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if entitlement is None:
        raise ErclaveError(
            "entitlement_not_updated",
            "Entitlement could not be updated.",
            status_code=409,
            details={"tenant_id": tenant_id, "module_code": module_code},
        )
    return EntitlementResponse(data=entitlement)


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


@router.post("/users/invitations", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: UserInvitationRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> UserResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    return UserResponse(
        data=repository.invite_user(
            tenant_id=x_tenant_id,
            email=payload.email,
            display_name=payload.display_name,
            role_ids=payload.role_ids,
            idempotency_key=require_idempotency_key(idempotency_key),
            correlation_id=resolve_correlation_id(x_correlation_id),
        )
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> UserResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    user = repository.update_user(
        tenant_id=x_tenant_id,
        user_id=user_id,
        display_name=payload.display_name,
        role_ids=payload.role_ids,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if user is None:
        raise ErclaveError("user_not_found", "User not found for tenant.", status_code=404, details={"user_id": user_id})
    return UserResponse(data=user)


@router.post("/users/{user_id}/disable", response_model=UserResponse)
def disable_user(
    user_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> UserResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    user = repository.disable_user(
        tenant_id=x_tenant_id,
        user_id=user_id,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if user is None:
        raise ErclaveError("user_not_found", "User not found for tenant.", status_code=404, details={"user_id": user_id})
    return UserResponse(data=user)


@router.get("/roles", response_model=RoleListResponse)
def list_roles(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=100),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleListResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    return RoleListResponse(data=repository.list_roles(x_tenant_id, limit=limit))


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    role = repository.create_role(
        tenant_id=x_tenant_id,
        code=payload.code,
        name=payload.name,
        description=payload.description,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if role is None:
        raise ErclaveError("role_conflict", "Role code already exists for tenant.", status_code=409)
    return RoleResponse(data=role)


@router.patch("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: str,
    payload: RoleUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    role = repository.update_role(
        tenant_id=x_tenant_id,
        role_id=role_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if role is None:
        raise ErclaveError("role_not_found", "Role not found for tenant.", status_code=404, details={"role_id": role_id})
    return RoleResponse(data=role)


@router.put("/roles/{role_id}/permissions", response_model=RoleResponse)
def replace_role_permissions(
    role_id: str,
    payload: RolePermissionsReplaceRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    role = repository.replace_role_permissions(
        tenant_id=x_tenant_id,
        role_id=role_id,
        permission_ids=payload.permission_ids,
        scope=payload.scope,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if role is None:
        raise ErclaveError(
            "role_permissions_not_updated",
            "Role or permission not found for tenant.",
            status_code=404,
            details={"role_id": role_id},
        )
    return RoleResponse(data=role)


@router.get("/permissions", response_model=PermissionListResponse)
def list_permissions(
    limit: int = Query(default=200, ge=1, le=500),
    repository: AdminRepository = Depends(get_admin_repository),
) -> PermissionListResponse:
    return PermissionListResponse(data=repository.list_permissions(limit=limit))
