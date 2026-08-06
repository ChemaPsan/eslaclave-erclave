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
    cost_center: str | None = None
    expected_margin: float | None = None
    description: str | None = None


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
    cost_center: str | None = None
    expected_margin: float | None = Field(default=None, ge=0, le=100)
    description: str | None = None


class ProductServiceUpdateRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    base_unit: str | None = None
    target_price: float | None = None
    responsible_area: str | None = None
    cost_center: str | None = None
    expected_margin: float | None = Field(default=None, ge=0, le=100)
    description: str | None = None


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
    labor_area_ref_id: str = Field(min_length=1, max_length=40)
    labor_area_name: str = Field(min_length=1, max_length=200)
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


class RecipeStageRead(BaseModel):
    id: str
    labor_area_ref_id: str | None = None
    labor_area_name: str | None = None
    name: str
    description: str | None = None
    expected_minutes: float | None = None
    sort_order: int = 0
    status: Literal["active", "inactive"] = "active"


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


MachineStatus = Literal["active", "inactive", "maintenance"]
OrderStatus = Literal["released", "waiting_resources", "in_progress", "paused", "in_validation", "completed", "cancelled"]
OrderStageStatus = Literal["pending", "in_progress", "completed", "skipped", "blocked"]


class MachineCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    machine_type: str = Field(min_length=1, max_length=120)
    area_name: str | None = Field(default=None, max_length=200)
    available_minutes_per_day: float = Field(gt=0)
    cost_per_minute: float = Field(ge=0)


class MachineUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    machine_type: str | None = Field(default=None, min_length=1, max_length=120)
    area_name: str | None = Field(default=None, max_length=200)
    available_minutes_per_day: float | None = Field(default=None, gt=0)
    cost_per_minute: float | None = Field(default=None, ge=0)
    status: MachineStatus | None = None


class MachineRead(BaseModel):
    id: str
    code: str
    name: str
    machine_type: str
    area_name: str | None = None
    available_minutes_per_day: float
    cost_per_minute: float
    status: MachineStatus


class MachineResponse(BaseModel):
    data: MachineRead


class MachineListResponse(BaseModel):
    data: list[MachineRead]


class ResourceAvailabilityInput(BaseModel):
    resource_ref_id: str
    resource_type: ResourceType
    available_quantity: float = Field(ge=0)
    unit: str
    unit_cost: float | None = Field(default=None, ge=0)
    source: str = Field(min_length=1, max_length=120)


class ResourceValidationRequest(BaseModel):
    recipe_version_id: str
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)
    observed_resources: list[ResourceAvailabilityInput] = Field(default_factory=list)


class ResourceValidationRow(BaseModel):
    resource_type: ResourceType
    resource_ref_id: str | None = None
    resource_code: str
    resource_name: str
    unit: str
    required_quantity: float
    available_quantity: float
    unit_cost: float
    total_cost: float
    source: str
    ok: bool
    blocker_code: str | None = None


class ResourceValidationRead(BaseModel):
    recipe_version_id: str
    quantity: float
    unit: str
    can_release: bool
    planned_cost: float
    validated_at: datetime
    rows: list[ResourceValidationRow]
    blockers: list[str]


class ResourceValidationResponse(BaseModel):
    data: ResourceValidationRead


class OrderStageAssignment(BaseModel):
    recipe_stage_id: str | None = None
    responsible_name: str | None = Field(default=None, max_length=200)


class ProductionOrderCreateRequest(ResourceValidationRequest):
    planned_start_at: datetime | None = None
    required_at: datetime | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    responsible_name: str = Field(min_length=1, max_length=200)
    stage_assignments: list[OrderStageAssignment] = Field(default_factory=list)
    source_type: Literal["manual", "sales_order", "integration"] = "manual"
    source_id: str | None = None
    source_line_id: str | None = None


class ProductionOrderStatusRequest(BaseModel):
    status: OrderStatus
    reason: str = Field(min_length=3, max_length=500)
    actual_cost: float | None = Field(default=None, ge=0)


class OrderStageUpdateRequest(BaseModel):
    status: OrderStageStatus
    actual_minutes: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class ProductionOrderStageRead(BaseModel):
    id: str
    recipe_stage_id: str | None = None
    name: str
    sort_order: int
    status: OrderStageStatus
    planned_minutes: float | None = None
    actual_minutes: float | None = None
    responsible_name: str | None = None
    progress_percent: float
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class ProductionOrderRead(BaseModel):
    id: str
    code: str
    product_service_id: str
    recipe_id: str
    recipe_version_id: str
    quantity: float
    unit: str
    status: OrderStatus
    priority: Literal["low", "medium", "high"]
    required_at: datetime | None = None
    planned_start_at: datetime | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    responsible_name: str
    source_type: str
    source_id: str | None = None
    planned_cost: float
    actual_cost: float | None = None
    recipe_snapshot: dict
    resource_validation_snapshot: dict
    stages: list[ProductionOrderStageRead] = Field(default_factory=list)
    created_at: datetime


class ProductionOrderResponse(BaseModel):
    data: ProductionOrderRead


class ProductionOrderListResponse(BaseModel):
    data: list[ProductionOrderRead]
    page: Page = Field(default_factory=Page)


class OrderStageResponse(BaseModel):
    data: ProductionOrderStageRead
