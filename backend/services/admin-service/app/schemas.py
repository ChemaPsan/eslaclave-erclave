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


class RoleRead(BaseModel):
    id: str
    code: str
    name: str
    status: str
    permissions: list[str] = Field(default_factory=list)


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


class RolePermissionsReplaceRequest(BaseModel):
    permission_ids: list[str]
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


class PermissionListResponse(BaseModel):
    data: list[PermissionRead]
    page: Page = Field(default_factory=Page)
