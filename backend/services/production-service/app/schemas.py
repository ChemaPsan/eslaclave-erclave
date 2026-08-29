from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class UnitCodeMixin:
    @field_validator("base_unit", "unit", check_fields=False, mode="before")
    @classmethod
    def normalize_unit_code(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


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
    inventory_item_id: str | None = None


class ProductServiceListResponse(BaseModel):
    data: list[ProductServiceRead]
    page: Page = Field(default_factory=Page)


class ProductServiceResponse(BaseModel):
    data: ProductServiceRead

class FinishedGoodItemCreate(UnitCodeMixin, BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=240)
    type: Literal["finishedGood"] = "finishedGood"
    category: str | None = None
    base_unit: str = Field(min_length=1, max_length=40)
    inventory_policy: Literal["standard", "lot", "serial", "restricted"] = "standard"
    suggested_warehouse_id: str | None = None
    minimum_stock: float = Field(default=0, ge=0)
    maximum_stock: float = Field(default=0, ge=0)
    default_unit_cost: float = Field(default=0, ge=0)
    use_in_recipe: bool = False
    description: str | None = None

class FinishedGoodLinkRequest(BaseModel):
    inventory_item: FinishedGoodItemCreate

class FinishedGoodLinkRead(BaseModel):
    product_service: ProductServiceRead
    inventory_item: dict
    link_status: Literal["linked"] = "linked"

class FinishedGoodLinkResponse(BaseModel):
    data: FinishedGoodLinkRead


class ProductServiceCreateRequest(UnitCodeMixin, BaseModel):
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
    inventory_item_id: str | None = Field(default=None, min_length=1, max_length=40)

    @field_validator("inventory_item_id", mode="before")
    @classmethod
    def normalize_inventory_item_id(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @model_validator(mode="after")
    def validate_inventory_mapping(self):
        if self.type == "product" and not self.inventory_item_id:
            raise ValueError("product_inventory_item_required")
        if self.type == "service" and self.inventory_item_id:
            raise ValueError("service_inventory_item_forbidden")
        return self


class ProductServiceUpdateRequest(UnitCodeMixin, BaseModel):
    name: str | None = None
    category: str | None = None
    base_unit: str | None = None
    target_price: float | None = None
    responsible_area: str | None = None
    cost_center: str | None = None
    expected_margin: float | None = Field(default=None, ge=0, le=100)
    description: str | None = None
    inventory_item_id: str | None = Field(default=None, min_length=1, max_length=40)

    @field_validator("inventory_item_id", mode="before")
    @classmethod
    def normalize_inventory_item_id(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class StatusChangeRequest(BaseModel):
    status: ProductServiceStatus
    reason: str | None = None


RecipeStatus = Literal["draft", "active", "inactive"]
RecipeVersionStatus = Literal["draft", "pending_approval", "approved", "obsolete"]
ResourceType = Literal["material", "labor", "machine", "other"]


class RecipeResourceInput(UnitCodeMixin, BaseModel):
    resource_type: ResourceType
    resource_ref_id: str | None = None
    resource_code: str = Field(min_length=1, max_length=80)
    resource_name: str = Field(min_length=1, max_length=240)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)
    unit_cost: float = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)


class RecipeStageInput(BaseModel):
    weight_percent: float = Field(gt=0, le=100, multiple_of=0.01)
    labor_area_ref_id: str = Field(min_length=1, max_length=40)
    labor_area_name: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    expected_minutes: float | None = Field(default=None, ge=0)
    sort_order: int = Field(default=0, ge=0)
    status: Literal["active", "inactive"] = "active"


class RecipeVersionPayload(UnitCodeMixin, BaseModel):
    base_quantity: float = Field(gt=0)
    base_unit: str = Field(min_length=1, max_length=40)
    suggested_duration_days: int = Field(default=1, ge=1, le=365)
    change_reason: str | None = None
    resources: list[RecipeResourceInput] = Field(default_factory=list)
    stages: list[RecipeStageInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_references(self):
        resource_keys=[(item.resource_type,item.resource_ref_id,item.unit) for item in self.resources]
        if any(not item.resource_ref_id for item in self.resources):raise ValueError("resource_reference_required")
        if len(resource_keys)!=len(set(resource_keys)):raise ValueError("duplicate_recipe_resource")
        stage_keys=[item.labor_area_ref_id for item in self.stages]
        if len(stage_keys)!=len(set(stage_keys)):raise ValueError("duplicate_recipe_stage_area")
        phase_numbers=sorted(item.sort_order for item in self.stages if item.status == "active")
        if phase_numbers and phase_numbers != list(range(1, len(phase_numbers) + 1)):
            raise ValueError("active_recipe_stage_phase_numbers_must_be_contiguous")
        active_weight = sum(item.weight_percent for item in self.stages if item.status == "active")
        if self.stages and abs(active_weight - 100) > 0.000001:
            raise ValueError("active_recipe_stage_weight_must_total_100")
        return self


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
    weight_percent: float
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
    suggested_duration_days: int = 1
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
ORDER_STATUS_TRANSITIONS = {
    "released": {"waiting_resources", "in_progress", "cancelled"},
    "waiting_resources": {"released", "in_progress", "cancelled"},
    "in_progress": {"paused", "in_validation", "cancelled"},
    "paused": {"in_progress", "cancelled"},
    "in_validation": {"in_progress", "completed"},
    "completed": set(),
    "cancelled": set(),
}


class MachineCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    machine_type: str = Field(min_length=1, max_length=120)
    area_ref_id: str = Field(min_length=1,max_length=40)
    area_name: str = Field(min_length=1, max_length=200)
    available_minutes_per_day: float = Field(gt=0)
    cost_per_minute: float = Field(ge=0)


class MachineUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    machine_type: str | None = Field(default=None, min_length=1, max_length=120)
    area_ref_id: str | None = Field(default=None,min_length=1,max_length=40)
    area_name: str | None = Field(default=None, min_length=1,max_length=200)
    available_minutes_per_day: float | None = Field(default=None, gt=0)
    cost_per_minute: float | None = Field(default=None, ge=0)
    status: MachineStatus | None = None

    @model_validator(mode="after")
    def area_name_is_authoritative(self):
        if self.area_name is not None and self.area_ref_id is None:raise ValueError("area_reference_required")
        return self


class MachineRead(BaseModel):
    id: str
    code: str
    name: str
    machine_type: str
    area_ref_id: str | None = None
    area_name: str | None = None
    available_minutes_per_day: float
    cost_per_minute: float
    status: MachineStatus


class MachineResponse(BaseModel):
    data: MachineRead


class MachineListResponse(BaseModel):
    data: list[MachineRead]

class MaintenanceMachineCommand(BaseModel):
    maintenance_order_id: str = Field(min_length=1,max_length=40)
    production_order_id: str | None = Field(default=None,max_length=40)

class MaintenanceMachineCommandResponse(BaseModel):
    data: dict


class ResourceAvailabilityInput(BaseModel):
    resource_ref_id: str
    resource_type: ResourceType
    available_quantity: float = Field(ge=0)
    unit: str
    unit_cost: float | None = Field(default=None, ge=0)
    source: str = Field(min_length=1, max_length=120)
    allocations: list[dict] = Field(default_factory=list)


class ResourceValidationRequest(UnitCodeMixin, BaseModel):
    model_config={"extra":"forbid"}
    recipe_version_id: str
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)
    planned_for: date | None = None
    planned_start_date: date | None = None
    planned_duration_days: int = Field(default=1, ge=1, le=365)

    @model_validator(mode="after")
    def consistent_planning_start(self):
        if self.planned_for and self.planned_start_date and self.planned_for!=self.planned_start_date:
            raise ValueError("planning_start_dates_must_match")
        return self


class ResourceDailyAllocation(BaseModel):
    planned_date: date
    gross_capacity: float
    committed_quantity: float
    available_quantity: float
    allocated_quantity: float
    remaining_capacity: float


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
    allocations: list[dict] = Field(default_factory=list)
    daily_allocations: list[ResourceDailyAllocation] = Field(default_factory=list)


class ResourceValidationRead(BaseModel):
    recipe_version_id: str
    quantity: float
    unit: str
    can_release: bool
    planned_cost: float
    planned_start_date: date
    planned_end_date: date
    planned_duration_days: int
    minimum_duration_days: int
    validated_at: datetime
    rows: list[ResourceValidationRow]
    blockers: list[str]


class ResourceValidationResponse(BaseModel):
    data: ResourceValidationRead


class OrderStageAssignment(BaseModel):
    recipe_stage_id: str
    responsible_worker_id: str
    responsible_name: str | None = Field(default=None, max_length=200, exclude=True)


class ProductionOrderCreateRequest(ResourceValidationRequest):
    code: str | None = Field(default=None, min_length=1, max_length=80)
    planned_start_at: datetime | None = None
    required_at: datetime | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    responsible_worker_id: str
    responsible_name: str | None = Field(default=None, max_length=200, exclude=True)
    stage_assignments: list[OrderStageAssignment] = Field(default_factory=list)
    source_type: Literal["manual", "sales_order", "integration"] = "manual"
    source_id: str | None = None
    source_line_id: str | None = None

    @model_validator(mode="after")
    def unique_stage_assignments(self):
        stage_ids=[item.recipe_stage_id for item in self.stage_assignments]
        if len(stage_ids)!=len(set(stage_ids)):raise ValueError("duplicate_stage_assignment")
        return self

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value):
        return value.strip() if value is not None else None


class ProductionOrderStatusRequest(BaseModel):
    model_config={"extra":"forbid"}
    status: OrderStatus
    reason: str = Field(min_length=3, max_length=500)


class OrderStageUpdateRequest(BaseModel):
    status: OrderStageStatus
    progress_percent: float = Field(ge=0, le=100)
    actual_minutes: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def status_matches_progress(self):
        if self.status=="pending" and self.progress_percent!=0:raise ValueError("pending_stage_requires_zero_progress")
        if self.status=="in_progress" and not 0<self.progress_percent<100:raise ValueError("in_progress_stage_requires_partial_progress")
        if self.status in {"completed","skipped"} and self.progress_percent!=100:raise ValueError("terminal_stage_requires_full_progress")
        return self

class ProductionOrderResourceRead(BaseModel):
    id:str
    resource_type:ResourceType
    resource_ref_id:str
    resource_code:str
    resource_name:str
    unit:str
    planned_quantity:float
    actual_quantity:float|None=None
    unit_cost:float
    planned_cost:float
    actual_cost:float|None=None
    reservation_ref_id:str|None=None
    reservation_ref_ids:list[str]=Field(default_factory=list)

class ProductionOrderResourceUpdateRequest(BaseModel):
    actual_quantity:float=Field(ge=0)

class ProductionOrderResourceResponse(BaseModel):data:ProductionOrderResourceRead


class ProductionOrderStageRead(BaseModel):
    id: str
    weight_percent: float
    recipe_stage_id: str | None = None
    labor_area_ref_id: str | None = None
    labor_area_name: str | None = None
    name: str
    sort_order: int
    status: OrderStageStatus
    planned_minutes: float | None = None
    actual_minutes: float | None = None
    responsible_name: str | None = None
    responsible_worker_id: str | None = None
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
    planned_end_date: date | None = None
    planned_duration_days: int = 1
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    responsible_name: str
    responsible_worker_id: str | None = None
    source_type: str
    source_id: str | None = None
    planned_cost: float
    actual_cost: float | None = None
    overall_progress_percent: float = 0
    recipe_snapshot: dict
    resource_validation_snapshot: dict
    stages: list[ProductionOrderStageRead] = Field(default_factory=list)
    resources: list[ProductionOrderResourceRead] = Field(default_factory=list)
    created_at: datetime


class ProductionOrderResponse(BaseModel):
    data: ProductionOrderRead


class ProductionOrderListResponse(BaseModel):
    data: list[ProductionOrderRead]
    page: Page = Field(default_factory=Page)


class FinishedGoodsOrderProjection(BaseModel):
    id: str
    code: str
    product_service_id: str
    quantity: float
    unit: str
    status: Literal["completed"]
    unit_cost: float


class FinishedGoodsProductProjection(BaseModel):
    id: str
    code: str
    name: str
    type: Literal["product"]
    status: ProductServiceStatus
    base_unit: str
    inventory_item_id: str | None = None


class FinishedGoodsCandidateRead(BaseModel):
    order: FinishedGoodsOrderProjection
    product: FinishedGoodsProductProjection


class FinishedGoodsCandidateResponse(BaseModel):
    data: FinishedGoodsCandidateRead


class FinishedGoodsCandidateListResponse(BaseModel):
    data: list[FinishedGoodsCandidateRead]
    page: Page = Field(default_factory=Page)


class ProductionSalesRequestCreate(BaseModel):
    sales_order_id: str = Field(min_length=1, max_length=40)
    sales_order_line_id: str = Field(min_length=1, max_length=40)
    product_service_id: str = Field(min_length=1, max_length=40)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)
    requested_due_date: date | None = None


class ProductionSalesRequestRead(BaseModel):
    id: str
    sales_order_id: str
    sales_order_line_id: str
    product_service_id: str
    product_service_code: str
    product_service_name: str
    recipe_version_id: str
    quantity: float
    unit: str
    requested_due_date: date | None = None
    status: Literal["pending_configuration", "converted", "cancelled"]
    created_at: datetime


class ProductionSalesRequestResponse(BaseModel): data: ProductionSalesRequestRead
class ProductionSalesRequestListResponse(BaseModel): data: list[ProductionSalesRequestRead]


class OrderStageResponse(BaseModel):
    data: ProductionOrderStageRead
