from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class UnitCodeMixin:
    @field_validator("base_unit", "unit", check_fields=False, mode="before")
    @classmethod
    def normalize_unit_code(cls, value): return value.strip().upper() if isinstance(value,str) else value

Status = Literal["active", "inactive", "blocked"]

class WarehouseRead(BaseModel):
    id: str; code: str; name: str; type: str; status: Status; business_center: str; location: str; owner: str; capacity: str | None = None; inventory_policy: str = "standard"; zone: str | None = None; aisle: str | None = None; rack: str | None = None; level: str | None = None; position: str | None = None; description: str | None = None
class WarehouseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80); name: str = Field(min_length=1, max_length=200); type: str = Field(min_length=1, max_length=40); business_center: str; location: str; owner: str; capacity: str | None = None; inventory_policy: str = "standard"; zone: str | None = None; aisle: str | None = None; rack: str | None = None; level: str | None = None; position: str | None = None; description: str | None = None
class WarehouseUpdate(BaseModel):
    name: str | None = None; type: str | None = None; status: Status | None = None; business_center: str | None = None; location: str | None = None; owner: str | None = None; capacity: str | None = None; inventory_policy: str | None = None; zone: str | None = None; aisle: str | None = None; rack: str | None = None; level: str | None = None; position: str | None = None; description: str | None = None
class WarehouseResponse(BaseModel): data: WarehouseRead
class WarehouseListResponse(BaseModel): data: list[WarehouseRead]

class ItemRead(BaseModel):
    id: str; code: str; name: str; type: str; category: str | None = None; base_unit: str; inventory_policy: str; suggested_warehouse_id: str | None = None; minimum_stock: float = 0; maximum_stock: float | None = None; default_unit_cost: float = 0; default_unit_cost_per_base_unit: float = 0; use_in_recipe: bool = False; status: Status; description: str | None = None
class ItemCreate(UnitCodeMixin, BaseModel):
    code: str = Field(min_length=1, max_length=80); name: str = Field(min_length=1, max_length=240); type: str; category: str | None = None; base_unit: str; inventory_policy: Literal["standard","lot","serial","restricted"] = "standard"; suggested_warehouse_id: str | None = None; minimum_stock: float = Field(default=0, ge=0); maximum_stock: float | None = Field(default=None, ge=0); default_unit_cost: float = Field(default=0, ge=0); use_in_recipe: bool = False; description: str | None = None

    @model_validator(mode="after")
    def validate_stock_limits(self):
        if self.maximum_stock is not None and self.maximum_stock < self.minimum_stock:
            raise ValueError("maximum_stock_must_be_greater_than_or_equal_to_minimum_stock")
        return self
class ItemUpdate(UnitCodeMixin, BaseModel):
    name: str | None = None; type: str | None = None; category: str | None = None; base_unit: str | None = None; suggested_warehouse_id: str | None = None; minimum_stock: float | None = Field(default=None, ge=0); maximum_stock: float | None = Field(default=None, ge=0); default_unit_cost: float | None = Field(default=None, ge=0); use_in_recipe: bool | None = None; status: Status | None = None; description: str | None = None
class ItemResponse(BaseModel): data: ItemRead
class ItemListResponse(BaseModel): data: list[ItemRead]

class UnitConversionRequest(UnitCodeMixin, BaseModel):
    source_unit: str = Field(min_length=1, max_length=40)
    quantity: float = Field(gt=0)
    source_unit_cost: float | None = Field(default=None, ge=0)

class UnitConversionRead(BaseModel):
    inventory_item_id: str
    source_unit: str
    base_unit: str
    conversion_factor: float
    source_quantity: float
    base_quantity: float
    source_unit_cost: float | None = None
    unit_cost_per_base_unit: float | None = None

class UnitConversionResponse(BaseModel): data: UnitConversionRead

class SourceRef(BaseModel): type: str = Field(min_length=1); id: str = Field(min_length=1); line_id: str | None = None
class MovementCreate(UnitCodeMixin, BaseModel):
    movement_type: Literal["entry","exit","positive_adjustment","negative_adjustment","transfer"]
    inventory_item_id: str; warehouse_id: str; destination_warehouse_id: str | None = None
    quantity: float = Field(gt=0); unit: str; unit_cost: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=3); source: SourceRef; occurred_at: datetime
    @model_validator(mode="after")
    def validate_transfer(self):
        if self.movement_type == "transfer" and (not self.destination_warehouse_id or self.destination_warehouse_id == self.warehouse_id):
            raise ValueError("Transfer requires a different destination warehouse")
        return self
class MovementRead(BaseModel):
    id: str; movement_code: str; movement_type: str; inventory_item_id: str; warehouse_id: str; direction: Literal["in","out"]; quantity: float; unit: str; unit_cost: float | None = None; reason: str; source_type: str; source_id: str; transfer_group_id: str | None = None; reversal_of_id: str | None = None; status: Literal["recorded","reversed"]; occurred_at: datetime
class MovementResponse(BaseModel): data: MovementRead
class MovementListResponse(BaseModel): data: list[MovementRead]
class ReverseRequest(BaseModel): reason: str = Field(min_length=3)

class FinishedGoodsReceiptCreate(BaseModel):
    production_order_id: str = Field(min_length=1, max_length=80)
    warehouse_id: str = Field(min_length=1, max_length=80)
    quantity: float = Field(gt=0)
    received_at: datetime
    notes: str | None = Field(default=None, max_length=1000)

class FinishedGoodsReceiptRead(BaseModel):
    production_order_id: str
    production_order_code: str
    product_service_id: str
    product_service_code: str
    product_service_name: str
    inventory_item_id: str
    inventory_item_code: str
    inventory_item_name: str
    warehouse_id: str
    unit: str
    ordered_quantity: float
    received_quantity: float
    cumulative_received_quantity: float
    remaining_quantity: float
    movement: MovementRead

class FinishedGoodsReceiptSummaryRead(BaseModel):
    production_order_id: str
    received_quantity: float
    last_received_at: datetime | None = None

class FinishedGoodsReceiptResponse(BaseModel): data: FinishedGoodsReceiptRead
class FinishedGoodsReceiptListResponse(BaseModel): data: list[FinishedGoodsReceiptSummaryRead]
class BalanceRead(BaseModel):
    inventory_item_id: str; item_code: str; item_name: str; item_type: str
    category: str | None = None; item_status: Status; inventory_policy: str
    warehouse_id: str; warehouse_code: str; warehouse_name: str
    on_hand_quantity: float; reserved_quantity: float = 0; available_quantity: float; unit: str; average_unit_cost: float = 0; inventory_value: float = 0
    minimum_stock: float = 0; maximum_stock: float | None = None
    stock_status: Literal["negative", "out_of_stock", "below_minimum", "normal", "above_maximum"]
    last_movement_at: datetime | None = None
class Page(BaseModel): limit: int; next_cursor: str | None = None; has_more: bool
class BalanceListResponse(BaseModel): data: list[BalanceRead]; page: Page

class AvailabilityItemRequest(UnitCodeMixin, BaseModel):
    inventory_item_id: str = Field(min_length=1, max_length=40)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=40)

class AvailabilityCheckRequest(BaseModel):
    source: SourceRef
    items: list[AvailabilityItemRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_items(self):
        keys=[(item.inventory_item_id,item.unit) for item in self.items]
        if len(keys)!=len(set(keys)): raise ValueError("duplicate_availability_item")
        return self

class AvailabilityAllocation(BaseModel):
    warehouse_id: str
    warehouse_name: str
    quantity: float
    unit_cost: float

class AvailabilityItemRead(BaseModel):
    inventory_item_id: str
    item_code: str
    item_name: str
    unit: str
    required_quantity: float
    on_hand_quantity: float
    reserved_quantity: float
    available_quantity: float
    unit_cost: float
    total_cost: float
    ok: bool
    blocker_code: str | None = None
    allocations: list[AvailabilityAllocation] = Field(default_factory=list)

class AvailabilityCheckRead(BaseModel):
    source: SourceRef
    available: bool
    items: list[AvailabilityItemRead]

class AvailabilityCheckResponse(BaseModel): data: AvailabilityCheckRead

ReservationStatus=Literal["active","released","consumed","expired"]
class ReservationCreateRequest(UnitCodeMixin, BaseModel):
    inventory_item_id: str
    warehouse_id: str
    quantity: float = Field(gt=0)
    unit: str
    source: SourceRef
    expires_at: datetime | None = None

class ReservationRead(BaseModel):
    id: str
    inventory_item_id: str
    warehouse_id: str
    quantity: float
    unit: str
    unit_cost_snapshot: float
    source_type: str
    source_id: str
    source_line_id: str | None = None
    status: ReservationStatus
    expires_at: datetime | None = None
    created_at: datetime

class ReservationResponse(BaseModel): data: ReservationRead
class ReservationActionRequest(BaseModel):
    reason: str = Field(min_length=3,max_length=500)
    quantity: float | None = Field(default=None, gt=0)
