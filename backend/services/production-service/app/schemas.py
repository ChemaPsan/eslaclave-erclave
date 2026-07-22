from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Page(BaseModel):
    next_cursor: str | None = None


ProductServiceType = Literal["product", "service"]
ProductServiceStatus = Literal["active", "inactive", "pending_approval"]


class ProductServiceRead(BaseModel):
    id: str
    code: str
    name: str
    type: ProductServiceType
    category: str | None = None
    base_unit: str
    status: ProductServiceStatus
    target_price: float | None = None
    standard_cost: float | None = None
    responsible_area: str | None = None


class ProductServiceListResponse(BaseModel):
    data: list[ProductServiceRead]
    page: Page = Field(default_factory=Page)


class ProductServiceResponse(BaseModel):
    data: ProductServiceRead


class ProductServiceCreateRequest(BaseModel):
    code: str
    name: str
    type: ProductServiceType
    category: str | None = None
    base_unit: str
    target_price: float | None = None
    responsible_area: str | None = None


class ProductServiceUpdateRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    base_unit: str | None = None
    target_price: float | None = None
    responsible_area: str | None = None


class StatusChangeRequest(BaseModel):
    status: ProductServiceStatus
    reason: str | None = None


RecipeStatus = Literal["draft", "active", "inactive"]
RecipeVersionStatus = Literal["draft", "pending_approval", "approved", "obsolete"]
ResourceType = Literal["material", "labor", "machine", "other"]


class RecipeResourceInput(BaseModel):
    resource_type: ResourceType
    resource_ref_id: str | None = None
    resource_code: str = Field(min_length=1, max_length=80)
    resource_name: str = Field(min_length=1, max_length=240)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)
    unit_cost: float = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)


class RecipeStageInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    expected_minutes: float | None = Field(default=None, ge=0)
    sort_order: int = Field(default=0, ge=0)
    status: Literal["active", "inactive"] = "active"


class RecipeVersionPayload(BaseModel):
    base_quantity: float = Field(gt=0)
    base_unit: str = Field(min_length=1, max_length=40)
    change_reason: str | None = None
    resources: list[RecipeResourceInput] = Field(default_factory=list)
    stages: list[RecipeStageInput] = Field(default_factory=list)


class RecipeCreateRequest(RecipeVersionPayload):
    product_service_id: str
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=240)


class RecipeVersionCreateRequest(RecipeVersionPayload):
    change_reason: str = Field(min_length=3)


class RecipeVersionUpdateRequest(RecipeVersionPayload):
    pass


class RecipeApprovalRequest(BaseModel):
    approval_notes: str | None = None
    effective_from: str | None = None


class RecipeResourceRead(RecipeResourceInput):
    id: str
    total_cost: float


class RecipeStageRead(RecipeStageInput):
    id: str


class RecipeVersionRead(BaseModel):
    id: str
    recipe_id: str
    version_number: int
    status: RecipeVersionStatus
    base_quantity: float
    base_unit: str
    standard_cost: float
    change_reason: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    resources: list[RecipeResourceRead] = Field(default_factory=list)
    stages: list[RecipeStageRead] = Field(default_factory=list)


class RecipeRead(BaseModel):
    id: str
    product_service_id: str
    code: str
    name: str
    status: RecipeStatus
    current_version_id: str | None = None
    versions: list[RecipeVersionRead] = Field(default_factory=list)


class RecipeListResponse(BaseModel):
    data: list[RecipeRead]
    page: Page = Field(default_factory=Page)


class RecipeResponse(BaseModel):
    data: RecipeRead


class RecipeVersionResponse(BaseModel):
    data: RecipeVersionRead
