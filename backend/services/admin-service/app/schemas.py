import base64
import binascii
from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


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


class EntitlementRead(BaseModel):
    module_code: str
    status: str
    source: str = "manual"
    tenant_enabled: bool = True
    effective_active: bool = False
    limits: dict[str, Any] = Field(default_factory=dict)


class BackofficeTenantRead(TenantRead):
    owner_email: str | None = None
    active_memberships: int = 0
    total_memberships: int = 0
    modules: list[str] = Field(default_factory=list)
    entitlements: list[EntitlementRead] = Field(default_factory=list)
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


class BackofficeTenantUpdateRequest(BaseModel):
    commercial_name: str | None = Field(default=None, min_length=1, max_length=240)
    legal_name: str | None = Field(default=None, max_length=240)
    plan_id: str | None = Field(default=None, max_length=40)
    timezone: str | None = Field(default=None, min_length=1, max_length=80)
    locale: str | None = Field(default=None, min_length=2, max_length=20)


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


class EntitlementListResponse(BaseModel):
    data: list[EntitlementRead]


class EntitlementPreferenceUpdateRequest(BaseModel):
    enabled: bool


class BackofficeEntitlementUpdateRequest(BaseModel):
    status: Literal["active", "inactive", "suspended"]
    limits: dict[str, Any] = Field(default_factory=dict)
    source: Literal["subscription", "manual", "trial"] = "manual"


class EntitlementResponse(BaseModel):
    data: EntitlementRead


class ModuleCatalogRead(BaseModel):
    code: str
    name: str
    description: str
    owner_service: str
    public_feature: bool
    implementation_status: Literal["implemented", "planned"]
    dependencies: list[str] = Field(default_factory=list)


class ModuleCatalogListResponse(BaseModel):
    data: list[ModuleCatalogRead]


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


class UnitOfMeasureRead(BaseModel):
    id: str
    code: str
    name_es: str
    name_en: str
    symbol: str
    category: str
    decimal_places: int
    system_default: bool
    status: Literal["active", "inactive"]


class UnitOfMeasureCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    name_es: str = Field(min_length=1, max_length=120)
    name_en: str = Field(min_length=1, max_length=120)
    symbol: str = Field(min_length=1, max_length=24)
    category: str = Field(min_length=1, max_length=40)
    decimal_places: int = Field(default=3, ge=0, le=6)


class UnitOfMeasureUpdateRequest(BaseModel):
    name_es: str | None = Field(default=None, min_length=1, max_length=120)
    name_en: str | None = Field(default=None, min_length=1, max_length=120)
    symbol: str | None = Field(default=None, min_length=1, max_length=24)
    category: str | None = Field(default=None, min_length=1, max_length=40)
    decimal_places: int | None = Field(default=None, ge=0, le=6)
    status: Literal["active", "inactive"] | None = None


class UnitOfMeasureResponse(BaseModel):
    data: UnitOfMeasureRead


class UnitOfMeasureListResponse(BaseModel):
    data: list[UnitOfMeasureRead]


CatalogCode = Literal["currencies", "payment_terms"]


class CatalogItemRead(BaseModel):
    id: str
    catalog_code: CatalogCode
    code: str
    name_es: str
    name_en: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    system_default: bool
    status: Literal["active", "inactive"]


class CatalogItemCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    name_es: str = Field(min_length=1, max_length=160)
    name_en: str = Field(min_length=1, max_length=160)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogItemUpdateRequest(BaseModel):
    name_es: str | None = Field(default=None, min_length=1, max_length=160)
    name_en: str | None = Field(default=None, min_length=1, max_length=160)
    metadata: dict[str, Any] | None = None
    status: Literal["active", "inactive"] | None = None


class CatalogItemResponse(BaseModel):
    data: CatalogItemRead


class CatalogItemListResponse(BaseModel):
    data: list[CatalogItemRead]


class CodeSequenceRead(BaseModel):
    id: str
    document_type: str
    module_code: str
    name_es: str
    name_en: str
    prefix: str
    separator: str
    next_number: int
    padding: int
    mode: Literal["managed", "manual"]
    system_default: bool
    status: Literal["active", "inactive"]


class CodeSequenceUpdateRequest(BaseModel):
    prefix: str | None = Field(default=None, min_length=1, max_length=24, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    separator: str | None = Field(default=None, max_length=3, pattern=r"^[._/-]*$")
    next_number: int | None = Field(default=None, ge=1)
    padding: int | None = Field(default=None, ge=1, le=12)
    mode: Literal["managed", "manual"] | None = None
    status: Literal["active", "inactive"] | None = None


class CodeSequenceNextRequest(BaseModel):
    manual_code: str | None = Field(default=None, min_length=1, max_length=60, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


class CodeSequenceAllocationRead(BaseModel):
    document_type: str
    mode: Literal["managed", "manual"]
    code: str
    sequence_number: int | None = None


class CodeSequenceResponse(BaseModel):
    data: CodeSequenceRead


class CodeSequenceListResponse(BaseModel):
    data: list[CodeSequenceRead]


class CodeSequenceAllocationResponse(BaseModel):
    data: CodeSequenceAllocationRead


class DocumentTemplateRead(BaseModel):
    logo_data_url: str | None = None
    primary_color: str = Field(default="#6106A0", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(default="#F557D3", pattern=r"^#[0-9A-Fa-f]{6}$")
    text_color: str = Field(default="#190F34", pattern=r"^#[0-9A-Fa-f]{6}$")
    footer_text: str | None = Field(default=None, max_length=300)
    show_page_number: bool = True

    @field_validator("logo_data_url")
    @classmethod
    def validate_logo(cls, value):
        if value is None or value == "":
            return None
        prefixes = {
            "data:image/png;base64,": b"\x89PNG\r\n\x1a\n",
            "data:image/jpeg;base64,": b"\xff\xd8\xff",
            "data:image/webp;base64,": b"RIFF",
        }
        prefix = next((candidate for candidate in prefixes if value.startswith(candidate)), None)
        if prefix is None or len(value) > 1_500_000:
            raise ValueError("invalid_document_logo")
        try:
            decoded = base64.b64decode(value[len(prefix) :], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("invalid_document_logo") from None
        signature = prefixes[prefix]
        if len(decoded) > 1_000_000 or not decoded.startswith(signature):
            raise ValueError("invalid_document_logo")
        if prefix == "data:image/webp;base64," and (len(decoded) < 12 or decoded[8:12] != b"WEBP"):
            raise ValueError("invalid_document_logo")
        return value


class DocumentTemplateResponse(BaseModel):
    data: DocumentTemplateRead
