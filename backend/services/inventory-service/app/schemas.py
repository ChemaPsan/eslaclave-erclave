from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

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
    id: str; code: str; name: str; type: str; category: str | None = None; base_unit: str; inventory_policy: str; suggested_warehouse_id: str | None = None; minimum_stock: float = 0; maximum_stock: float | None = None; status: Status; description: str | None = None
class ItemCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80); name: str = Field(min_length=1, max_length=240); type: str; category: str | None = None; base_unit: str; inventory_policy: Literal["standard","lot","serial","restricted"] = "standard"; suggested_warehouse_id: str | None = None; minimum_stock: float = Field(default=0, ge=0); maximum_stock: float | None = Field(default=None, ge=0); description: str | None = None
class ItemUpdate(BaseModel):
    name: str | None = None; type: str | None = None; category: str | None = None; base_unit: str | None = None; suggested_warehouse_id: str | None = None; minimum_stock: float | None = Field(default=None, ge=0); maximum_stock: float | None = Field(default=None, ge=0); status: Status | None = None; description: str | None = None
class ItemResponse(BaseModel): data: ItemRead
class ItemListResponse(BaseModel): data: list[ItemRead]

class SourceRef(BaseModel): type: str = Field(min_length=1); id: str = Field(min_length=1)
class MovementCreate(BaseModel):
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
class BalanceRead(BaseModel):
    inventory_item_id: str; item_code: str; item_name: str; item_type: str
    category: str | None = None; item_status: Status; inventory_policy: str
    warehouse_id: str; warehouse_code: str; warehouse_name: str
    on_hand_quantity: float; reserved_quantity: float = 0; available_quantity: float; unit: str
    minimum_stock: float = 0; maximum_stock: float | None = None
    stock_status: Literal["negative", "out_of_stock", "below_minimum", "normal", "above_maximum"]
    last_movement_at: datetime | None = None
class Page(BaseModel): limit: int; next_cursor: str | None = None; has_more: bool
class BalanceListResponse(BaseModel): data: list[BalanceRead]; page: Page
