from typing import Any

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


class RoleRead(BaseModel):
    id: str
    code: str
    name: str
    status: str


class RoleListResponse(BaseModel):
    data: list[RoleRead]
    page: Page = Field(default_factory=Page)
