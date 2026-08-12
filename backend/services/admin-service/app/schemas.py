from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class TenantRead(BaseModel):
    id: str
    slug: str
    legal_name: str | None = None
    commercial_name: str
    status: str
    plan_id: str | None = None
    timezone: str
    locale: str


class TenantResponse(BaseModel):
    data: TenantRead


class BackofficeTenantRead(TenantRead):
    owner_email: str | None = None
    active_memberships: int = 0
    total_memberships: int = 0
    modules: list[str] = Field(default_factory=list)
    legal_entities_count: int = 0
    branches_count: int = 0


class BackofficeTenantListResponse(BaseModel):
    data: list[BackofficeTenantRead]


class BackofficeUsageDailyRead(BaseModel):
    tenant_id: str
    tenant_slug: str
    tenant_name: str
    usage_date: date
    active_users: int = 0
    api_requests: int = 0
    storage_mb: Decimal = Decimal("0")
    estimated_cost_mxn: Decimal = Decimal("0")
    source: str | None = None


class BackofficeUsageSummaryRead(BaseModel):
    tenants: int = 0
    days: int = 0
    active_users: int = 0
    api_requests: int = 0
    storage_mb: Decimal = Decimal("0")
    estimated_cost_mxn: Decimal = Decimal("0")


class BackofficeUsageListResponse(BaseModel):
    data: list[BackofficeUsageDailyRead]
    summary: BackofficeUsageSummaryRead = Field(default_factory=BackofficeUsageSummaryRead)


class BackofficeTenantStatusRequest(BaseModel):
    status: Literal["active", "suspended"]


class BackofficeTenantDeleteResponse(BaseModel):
    data: dict[str, Any]


class SourceRef(BaseModel):
    type: str
    id: str


class OrganizationProfile(BaseModel):
    corporate: dict[str, Any]
    legal_entities: list[dict[str, Any]] = Field(default_factory=list)
    branches: list[dict[str, Any]] = Field(default_factory=list)


class TenantCreateRequest(BaseModel):
    slug: str
    commercial_name: str
    legal_name: str | None = None
    plan_id: str | None = None
    timezone: str = "America/Mexico_City"
    locale: str = "es-MX"
    source: SourceRef
    organization_profile: OrganizationProfile | None = None


class TenantOnboardingOwnerRequest(BaseModel):
    email: str
    display_name: str
    status: Literal["invited", "active"] = "invited"
    branch_ids: list[str] = Field(default_factory=lambda: ["*"])


class TenantOnboardingModuleRequest(BaseModel):
    module_code: str
    status: Literal["active", "inactive", "suspended"] = "active"
    limits: dict[str, Any] = Field(default_factory=dict)
    source: Literal["subscription", "manual", "trial", "provisioning"] = "provisioning"


class TenantOnboardingRequest(BaseModel):
    slug: str
    commercial_name: str
    legal_name: str | None = None
    plan_id: str | None = None
    timezone: str = "America/Mexico_City"
    locale: str = "es-MX"
    source: SourceRef
    owner: TenantOnboardingOwnerRequest
    organization_profile: OrganizationProfile | None = None
    modules: list[TenantOnboardingModuleRequest] = Field(default_factory=lambda: [TenantOnboardingModuleRequest(module_code="admin")])


class EntitlementRead(BaseModel):
    module_code: str
    status: str
    limits: dict[str, Any] = Field(default_factory=dict)


class EntitlementListResponse(BaseModel):
    data: list[EntitlementRead]


class EntitlementUpsertRequest(BaseModel):
    status: Literal["active", "inactive", "suspended"]
    limits: dict[str, Any] = Field(default_factory=dict)
    source: Literal["subscription", "manual", "trial"] = "manual"


class EntitlementResponse(BaseModel):
    data: EntitlementRead


class SettingRead(BaseModel):
    key: str
    module_code: str | None = None
    value: dict[str, Any] = Field(default_factory=dict)


class SettingListResponse(BaseModel):
    data: list[SettingRead]


class SettingUpsertRequest(BaseModel):
    module_code: str | None = None
    value: dict[str, Any]


class SettingResponse(BaseModel):
    data: SettingRead


class LegalEntityCreateRequest(BaseModel):
    legal_name: str
    tax_id: str | None = None
    fiscal_regime: str | None = None
    cfdi_usage: str | None = None
    fiscal_address: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    contact_position: str | None = None


class LegalEntityUpdateRequest(BaseModel):
    legal_name: str | None = None
    tax_id: str | None = None
    fiscal_regime: str | None = None
    cfdi_usage: str | None = None
    fiscal_address: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    contact_position: str | None = None


class BranchCreateRequest(BaseModel):
    name: str
    code: str | None = None
    legal_entity_id: str | None = None
    address: str | None = None
    phone: str | None = None


class BranchUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    legal_entity_id: str | None = None
    address: str | None = None
    phone: str | None = None


class OrganizationItemResponse(BaseModel):
    data: dict[str, Any]


class PolicyEvaluateRequest(BaseModel):
    tenant_id: str
    actor_id: str
    module: str
    resource: str
    action: str
    scope: dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    matched_permissions: list[str] = Field(default_factory=list)


class PolicyEvaluateResponse(BaseModel):
    data: PolicyDecision


class Page(BaseModel):
    next_cursor: str | None = None


class UserRead(BaseModel):
    id: str
    email: str
    display_name: str
    status: str
    roles: list[str] = Field(default_factory=list)


class UserListResponse(BaseModel):
    data: list[UserRead]
    page: Page = Field(default_factory=Page)


class UserInvitationRequest(BaseModel):
    email: str
    display_name: str
    role_ids: list[str]


class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    role_ids: list[str] | None = None


class UserResponse(BaseModel):
    data: UserRead


class PermissionAssignmentRead(BaseModel):
    permission_id: str
    code: str
    scope: dict[str, Any] = Field(default_factory=dict)


class RoleRead(BaseModel):
    id: str
    code: str
    name: str
    status: str
    permissions: list[str] = Field(default_factory=list)
    permission_assignments: list[PermissionAssignmentRead] = Field(default_factory=list)
    system_role: bool = False
    permission_revision: int = 1


class RoleListResponse(BaseModel):
    data: list[RoleRead]
    page: Page = Field(default_factory=Page)


class RoleCreateRequest(BaseModel):
    code: str
    name: str
    description: str | None = None


class RoleUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: Literal["active", "inactive"] | None = None


class PermissionAssignmentWrite(BaseModel):
    permission_id: str
    scope: dict[str, Any] = Field(default_factory=dict)


class RolePermissionsReplaceRequest(BaseModel):
    assignments: list[PermissionAssignmentWrite] | None = None
    expected_revision: int | None = Field(default=None, ge=1)
    permission_ids: list[str] | None = None
    scope: dict[str, Any] = Field(default_factory=dict)


class RoleResponse(BaseModel):
    data: RoleRead


class PermissionRead(BaseModel):
    id: str
    code: str
    module_code: str
    resource: str
    action: str
    status: str
    display_name_es: str
    display_name_en: str
    description_es: str
    description_en: str
    classification: Literal["tenant", "internal", "public", "integration"]
    assignable_to_tenant_role: bool
    risk_level: Literal["low", "standard", "high", "critical"]
    sort_order: int = 1000
    entitlement_status: Literal["active", "inactive", "suspended"] | None = None
    available: bool = False


class PermissionListResponse(BaseModel):
    data: list[PermissionRead]
    page: Page = Field(default_factory=Page)


class SessionBranchRead(BaseModel):
    id: str
    name: str
    code: str | None = None
    status: str = "active"
    legal_entity_id: str | None = None


class SessionScopeRead(BaseModel):
    branch_ids: list[str] = Field(default_factory=list)
    branches: list[SessionBranchRead] = Field(default_factory=list)
    all_branches: bool = True


class SessionContextRead(BaseModel):
    tenant: TenantRead
    user: UserRead
    roles: list[RoleRead] = Field(default_factory=list)
    entitlements: list[EntitlementRead] = Field(default_factory=list)
    entitlement_limits: dict[str, dict[str, Any]] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    active_modules: list[str] = Field(default_factory=list)
    scope: SessionScopeRead = Field(default_factory=SessionScopeRead)


class SessionContextResponse(BaseModel):
    data: SessionContextRead


class SessionTenantRead(BaseModel):
    tenant: TenantRead
    user_status: str
    membership_status: str
    roles: list[str] = Field(default_factory=list)


class SessionTenantListResponse(BaseModel):
    data: list[SessionTenantRead]
    page: Page = Field(default_factory=Page)


class TenantOnboardingResponse(BaseModel):
    data: dict[str, Any]
