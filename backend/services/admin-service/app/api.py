from datetime import date, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, status

from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError

from .auth import (
    AuthenticatedActor,
    create_firebase_password_invitation,
    delete_firebase_user_by_email,
    ensure_firebase_user,
    get_authenticated_actor,
    require_backoffice_admin,
    require_permission_for_header_tenant,
    require_permission_for_path_tenant,
)
from .repositories import (
    AdminRepository,
    IdempotencyConflictError,
    RolePermissionConflictError,
    RolePermissionForbiddenError,
    RolePermissionValidationError,
    get_admin_repository,
)
from .seeds.catalog import get_module_seed
from .schemas import (
    BackofficeTenantDeleteResponse,
    BackofficeTenantListResponse,
    BackofficeTenantRead,
    BackofficeTenantStatusRequest,
    BackofficeUsageListResponse,
    BranchCreateRequest,
    BranchUpdateRequest,
    EntitlementListResponse,
    EntitlementResponse,
    EntitlementUpsertRequest,
    LegalEntityCreateRequest,
    LegalEntityUpdateRequest,
    OrganizationItemResponse,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    PermissionListResponse,
    RoleCreateRequest,
    RoleListResponse,
    RolePermissionsReplaceRequest,
    RoleResponse,
    RoleUpdateRequest,
    SessionContextResponse,
    SessionTenantListResponse,
    SessionTenantRead,
    SettingListResponse,
    SettingResponse,
    SettingUpsertRequest,
    TenantCreateRequest,
    TenantOnboardingRequest,
    TenantOnboardingResponse,
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


@router.get("/session/context", response_model=SessionContextResponse)
def get_session_context(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
    settings: Settings = Depends(get_settings),
    authenticated_actor: AuthenticatedActor | None = Depends(get_authenticated_actor),
    repository: AdminRepository = Depends(get_admin_repository),
) -> SessionContextResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if settings.auth_mode == "firebase":
        context = repository.get_session_context_by_email(x_tenant_id, authenticated_actor.email)
        if context is None:
            raise ErclaveError(
                "session_context_not_found",
                "Session context not found for tenant and authenticated email.",
                status_code=404,
                details={"tenant_id": x_tenant_id, "email": authenticated_actor.email},
            )
        return SessionContextResponse(data=context)

    if not x_actor_id:
        raise ErclaveError("actor_required", "X-Actor-Id header is required.", status_code=400)
    context = repository.get_session_context(x_tenant_id, x_actor_id)
    if context is None:
        raise ErclaveError(
            "session_context_not_found",
            "Session context not found for tenant and actor.",
            status_code=404,
            details={"tenant_id": x_tenant_id, "actor_id": x_actor_id},
        )
    return SessionContextResponse(data=context)


@router.get("/session/tenants", response_model=SessionTenantListResponse)
def list_session_tenants(
    settings: Settings = Depends(get_settings),
    authenticated_actor: AuthenticatedActor | None = Depends(get_authenticated_actor),
    repository: AdminRepository = Depends(get_admin_repository),
) -> SessionTenantListResponse:
    if settings.auth_mode != "firebase":
        raise ErclaveError("firebase_auth_required", "Session tenant discovery requires Firebase auth.", status_code=400)
    tenants = repository.list_session_tenants_by_email(authenticated_actor.email)
    return SessionTenantListResponse(data=[SessionTenantRead.model_validate(item) for item in tenants])


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    _authorization: None = Depends(require_permission_for_path_tenant("admin.tenant.read")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> TenantResponse:
    tenant = repository.get_tenant(tenant_id)
    if tenant is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": tenant_id})
    return TenantResponse(data=tenant)


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: TenantCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    repository: AdminRepository = Depends(get_admin_repository),
) -> TenantResponse:
    tenant = repository.create_tenant(
        slug=payload.slug,
        commercial_name=payload.commercial_name,
        legal_name=payload.legal_name,
        plan_id=payload.plan_id,
        timezone=payload.timezone,
        locale=payload.locale,
        source=payload.source.model_dump(),
        organization_profile=payload.organization_profile.model_dump() if payload.organization_profile else None,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    return TenantResponse(data=tenant)


@router.post("/provisioning/tenant-onboarding", response_model=TenantOnboardingResponse, status_code=status.HTTP_201_CREATED)
def onboard_tenant(
    payload: TenantOnboardingRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_backoffice_admin),
    settings: Settings = Depends(get_settings),
    repository: AdminRepository = Depends(get_admin_repository),
) -> TenantOnboardingResponse:
    resolved_idempotency_key = require_idempotency_key(idempotency_key)
    ensure_firebase_user(payload.owner.email, payload.owner.display_name, settings)
    result = repository.onboard_tenant(
        slug=payload.slug,
        commercial_name=payload.commercial_name,
        legal_name=payload.legal_name,
        plan_id=payload.plan_id,
        timezone=payload.timezone,
        locale=payload.locale,
        source=payload.source.model_dump(),
        owner=payload.owner.model_dump(),
        organization_profile=payload.organization_profile.model_dump() if payload.organization_profile else None,
        modules=[item.model_dump() for item in payload.modules],
        idempotency_key=resolved_idempotency_key,
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    result["invitation"] = create_firebase_password_invitation(payload.owner.email, settings)
    return TenantOnboardingResponse(data=result)


@router.get("/backoffice/tenants", response_model=BackofficeTenantListResponse)
def list_backoffice_tenants(
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    _authorization: None = Depends(require_backoffice_admin),
    repository: AdminRepository = Depends(get_admin_repository),
) -> BackofficeTenantListResponse:
    tenants = repository.list_backoffice_tenants(search=search, limit=limit)
    return BackofficeTenantListResponse(data=[BackofficeTenantRead.model_validate(item) for item in tenants])


@router.patch("/backoffice/tenants/{tenant_id}/status", response_model=TenantResponse)
def set_backoffice_tenant_status(
    tenant_id: str,
    payload: BackofficeTenantStatusRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_backoffice_admin),
    repository: AdminRepository = Depends(get_admin_repository),
) -> TenantResponse:
    tenant = repository.set_backoffice_tenant_status(
        tenant_id=tenant_id,
        new_status=payload.status,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if tenant is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": tenant_id})
    return TenantResponse(data=tenant)


@router.delete("/backoffice/tenants/{tenant_id}", response_model=BackofficeTenantDeleteResponse)
def delete_backoffice_tenant(
    tenant_id: str,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_backoffice_admin),
    settings: Settings = Depends(get_settings),
    repository: AdminRepository = Depends(get_admin_repository),
) -> BackofficeTenantDeleteResponse:
    result = repository.delete_backoffice_tenant(
        tenant_id=tenant_id,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if result is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": tenant_id})
    for email in result.get("firebase_emails", []):
        delete_firebase_user_by_email(email, settings)
    return BackofficeTenantDeleteResponse(data=result)


@router.get("/backoffice/usage", response_model=BackofficeUsageListResponse)
def list_backoffice_usage(
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    _authorization: None = Depends(require_backoffice_admin),
    repository: AdminRepository = Depends(get_admin_repository),
) -> BackofficeUsageListResponse:
    resolved_to_date = to_date or date.today()
    resolved_from_date = from_date or (resolved_to_date - timedelta(days=29))
    if resolved_from_date > resolved_to_date:
        raise ErclaveError(
            "invalid_usage_date_range",
            "from_date must be earlier than or equal to to_date.",
            status_code=400,
            details={"from_date": resolved_from_date.isoformat(), "to_date": resolved_to_date.isoformat()},
        )
    metrics, summary = repository.list_backoffice_usage(
        from_date=resolved_from_date,
        to_date=resolved_to_date,
        tenant_id=tenant_id,
        limit=limit,
    )
    return BackofficeUsageListResponse(data=metrics, summary=summary)


@router.get("/tenants/{tenant_id}/entitlements", response_model=EntitlementListResponse)
def list_tenant_entitlements(
    tenant_id: str,
    _authorization: None = Depends(require_permission_for_path_tenant("admin.tenant.read")),
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
    _authorization: None = Depends(require_permission_for_path_tenant("admin.entitlement.manage")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> EntitlementResponse:
    if get_module_seed(module_code) is None:
        raise ErclaveError("module_not_found", "Module is not part of the ERClave catalog.", status_code=404, details={"module_code": module_code})
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


@router.get("/settings", response_model=SettingListResponse)
def list_settings(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    module_code: str | None = Query(default=None),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.read")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> SettingListResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    return SettingListResponse(data=repository.list_settings(x_tenant_id, module_code=module_code))


@router.put("/settings/{key}", response_model=SettingResponse)
def upsert_setting(
    key: str,
    payload: SettingUpsertRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> SettingResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    setting = repository.upsert_setting(
        tenant_id=x_tenant_id,
        key=key,
        module_code=payload.module_code,
        value=payload.value,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if setting is None:
        raise ErclaveError("setting_not_updated", "Setting could not be updated.", status_code=409, details={"key": key})
    return SettingResponse(data=setting)


@router.post("/organization/legal-entities", response_model=OrganizationItemResponse, status_code=status.HTTP_201_CREATED)
def create_legal_entity(
    payload: LegalEntityCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    item = repository.create_legal_entity(
        tenant_id=x_tenant_id,
        payload=payload.model_dump(),
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("legal_entity_not_created", "Legal entity could not be created.", status_code=409)
    return OrganizationItemResponse(data=item)


@router.patch("/organization/legal-entities/{legal_entity_id}", response_model=OrganizationItemResponse)
def update_legal_entity(
    legal_entity_id: str,
    payload: LegalEntityUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    item = repository.update_legal_entity(
        tenant_id=x_tenant_id,
        legal_entity_id=legal_entity_id,
        payload=payload.model_dump(),
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("legal_entity_not_found", "Legal entity not found for tenant.", status_code=404, details={"legal_entity_id": legal_entity_id})
    return OrganizationItemResponse(data=item)


@router.post("/organization/legal-entities/{legal_entity_id}/activate", response_model=OrganizationItemResponse)
def activate_legal_entity(
    legal_entity_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    item = repository.set_legal_entity_status(
        tenant_id=x_tenant_id,
        legal_entity_id=legal_entity_id,
        status="active",
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("legal_entity_not_found", "Legal entity not found for tenant.", status_code=404, details={"legal_entity_id": legal_entity_id})
    return OrganizationItemResponse(data=item)


@router.post("/organization/legal-entities/{legal_entity_id}/deactivate", response_model=OrganizationItemResponse)
def deactivate_legal_entity(
    legal_entity_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    item = repository.set_legal_entity_status(
        tenant_id=x_tenant_id,
        legal_entity_id=legal_entity_id,
        status="inactive",
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("legal_entity_not_found", "Legal entity not found for tenant.", status_code=404, details={"legal_entity_id": legal_entity_id})
    return OrganizationItemResponse(data=item)


@router.post("/organization/branches", response_model=OrganizationItemResponse, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    item = repository.create_branch(
        tenant_id=x_tenant_id,
        payload=payload.model_dump(),
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("branch_not_created", "Branch could not be created.", status_code=409)
    return OrganizationItemResponse(data=item)


@router.patch("/organization/branches/{branch_id}", response_model=OrganizationItemResponse)
def update_branch(
    branch_id: str,
    payload: BranchUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    item = repository.update_branch(
        tenant_id=x_tenant_id,
        branch_id=branch_id,
        payload=payload.model_dump(),
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("branch_not_found", "Branch not found for tenant.", status_code=404, details={"branch_id": branch_id})
    return OrganizationItemResponse(data=item)


@router.post("/organization/branches/{branch_id}/activate", response_model=OrganizationItemResponse)
def activate_branch(
    branch_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    item = repository.set_branch_status(
        tenant_id=x_tenant_id,
        branch_id=branch_id,
        status="active",
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("branch_not_found", "Branch not found for tenant.", status_code=404, details={"branch_id": branch_id})
    return OrganizationItemResponse(data=item)


@router.post("/organization/branches/{branch_id}/deactivate", response_model=OrganizationItemResponse)
def deactivate_branch(
    branch_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.setting.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> OrganizationItemResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    item = repository.set_branch_status(
        tenant_id=x_tenant_id,
        branch_id=branch_id,
        status="inactive",
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if item is None:
        raise ErclaveError("branch_not_found", "Branch not found for tenant.", status_code=404, details={"branch_id": branch_id})
    return OrganizationItemResponse(data=item)


@router.post("/policy/evaluate", response_model=PolicyEvaluateResponse)
def evaluate_policy(
    payload: PolicyEvaluateRequest,
    settings: Settings = Depends(get_settings),
    authenticated_actor: AuthenticatedActor | None = Depends(get_authenticated_actor),
    repository: AdminRepository = Depends(get_admin_repository),
) -> PolicyEvaluateResponse:
    if settings.auth_mode == "firebase":
        context = repository.get_session_context_by_email(payload.tenant_id, authenticated_actor.email)
        if context is None:
            raise ErclaveError(
                "session_context_not_found",
                "Session context not found for tenant and authenticated email.",
                status_code=404,
                details={"tenant_id": payload.tenant_id, "email": authenticated_actor.email},
            )
        if "internal.policy.evaluate" not in context.permissions:
            raise ErclaveError(
                "permission_denied",
                "Authenticated actor does not have the required permission.",
                status_code=403,
                details={"tenant_id": payload.tenant_id, "permission": "internal.policy.evaluate"},
            )
        if payload.actor_id != context.user.id:
            raise ErclaveError(
                "actor_mismatch",
                "Policy evaluation actor must match the authenticated session.",
                status_code=403,
                details={"tenant_id": payload.tenant_id, "actor_id": payload.actor_id},
            )
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
    _authorization: None = Depends(require_permission_for_header_tenant("admin.user.read")),
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
    _authorization: None = Depends(require_permission_for_header_tenant("admin.user.invite")),
    settings: Settings = Depends(get_settings),
    repository: AdminRepository = Depends(get_admin_repository),
) -> UserResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if repository.get_tenant(x_tenant_id) is None:
        raise ErclaveError("tenant_not_found", "Tenant not found.", status_code=404, details={"tenant_id": x_tenant_id})
    resolved_idempotency_key = require_idempotency_key(idempotency_key)
    ensure_firebase_user(payload.email, payload.display_name, settings)
    return UserResponse(
        data=repository.invite_user(
            tenant_id=x_tenant_id,
            email=payload.email,
            display_name=payload.display_name,
            role_ids=payload.role_ids,
            idempotency_key=resolved_idempotency_key,
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
    _authorization: None = Depends(require_permission_for_header_tenant("admin.user.update")),
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
    _authorization: None = Depends(require_permission_for_header_tenant("admin.user.disable")),
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


@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.user.delete")),
    settings: Settings = Depends(get_settings),
    repository: AdminRepository = Depends(get_admin_repository),
) -> UserResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    user = repository.get_user_for_tenant(x_tenant_id, user_id)
    if user is None:
        raise ErclaveError("user_not_found", "User not found for tenant.", status_code=404, details={"user_id": user_id})
    delete_firebase_user_by_email(user.email, settings)
    deleted_user = repository.delete_user(
        tenant_id=x_tenant_id,
        user_id=user_id,
        idempotency_key=require_idempotency_key(idempotency_key),
        correlation_id=resolve_correlation_id(x_correlation_id),
    )
    if deleted_user is None:
        raise ErclaveError("user_not_found", "User not found for tenant.", status_code=404, details={"user_id": user_id})
    return UserResponse(data=deleted_user)


@router.get("/roles", response_model=RoleListResponse)
def list_roles(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=100),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.role.read")),
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
    _authorization: None = Depends(require_permission_for_header_tenant("admin.role.create")),
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
    _authorization: None = Depends(require_permission_for_header_tenant("admin.role.update")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    try:
        role = repository.update_role(
            tenant_id=x_tenant_id,
            role_id=role_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            idempotency_key=require_idempotency_key(idempotency_key),
            correlation_id=resolve_correlation_id(x_correlation_id),
        )
    except RolePermissionForbiddenError as exc:
        raise ErclaveError(str(exc), "The system role cannot be inactivated.", status_code=403) from exc
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
    authorization_actor: AuthenticatedActor | None = Depends(require_permission_for_header_tenant("admin.role.permissions.manage")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> RoleResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    if payload.assignments is not None and payload.permission_ids is not None:
        raise ErclaveError(
            "permission_assignments_required",
            "assignments and legacy permission_ids cannot be combined.",
            status_code=422,
        )
    current_role = None
    if payload.assignments is None and payload.permission_ids is None:
        raise ErclaveError("permission_assignments_required", "assignments are required.", status_code=422)
    if payload.assignments is not None and payload.expected_revision is None:
        raise ErclaveError(
            "permission_revision_required",
            "expected_revision is required.",
            status_code=422,
        )
    if payload.assignments is not None:
        assignments = [assignment.model_dump() for assignment in payload.assignments]
        expected_revision = payload.expected_revision
    else:
        current_role = repository.get_role(x_tenant_id, role_id)
        if current_role is None:
            raise ErclaveError("role_not_found", "Role not found for tenant.", status_code=404, details={"role_id": role_id})
        assignments = [
            {"permission_id": permission_id, "scope": payload.scope}
            for permission_id in (payload.permission_ids or [])
        ]
        expected_revision = payload.expected_revision or current_role.permission_revision
    try:
        role = repository.replace_role_permissions(
            tenant_id=x_tenant_id,
            role_id=role_id,
            assignments=assignments,
            expected_revision=expected_revision,
            idempotency_key=require_idempotency_key(idempotency_key),
            correlation_id=resolve_correlation_id(x_correlation_id),
            actor_email=authorization_actor.email if authorization_actor else None,
        )
    except (RolePermissionConflictError, IdempotencyConflictError) as exc:
        raise ErclaveError(str(exc), "The role permissions changed; reload before retrying.", status_code=409) from exc
    except RolePermissionValidationError as exc:
        raise ErclaveError(str(exc), "The permission assignment is invalid.", status_code=422) from exc
    except RolePermissionForbiddenError as exc:
        raise ErclaveError(str(exc), "The permission assignment is not allowed.", status_code=403) from exc
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
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=200, ge=1, le=500),
    _authorization: None = Depends(require_permission_for_header_tenant("admin.role.read")),
    repository: AdminRepository = Depends(get_admin_repository),
) -> PermissionListResponse:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    return PermissionListResponse(data=repository.list_permissions(x_tenant_id, limit=limit))
