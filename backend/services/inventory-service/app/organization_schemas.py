from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class WarehouseDivisionCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    division_ref_id: str = Field(min_length=1, max_length=40)
    expected_revision: int = Field(ge=0)

class WarehouseDivisionRead(BaseModel):
    warehouse_id: str
    division_ref_id: str | None = None
    revision: int

class WarehouseDivisionResponse(BaseModel):
    data: WarehouseDivisionRead

class ItemDivisionCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_revision: int = Field(ge=0)
    status: Literal['active', 'inactive'] = 'active'
    cost_center_ref_id: str | None = Field(None, min_length=1, max_length=40)

class ItemDivisionRead(BaseModel):
    item_id: str
    division_ref_id: str
    cost_center_ref_id: str | None = None
    cost_center_snapshot: dict | None = None
    status: Literal['active', 'inactive']
    revision: int

class ItemDivisionResponse(BaseModel):
    data: ItemDivisionRead

class AssignmentPage(BaseModel):
    total: int
    limit: int
    offset: int

class ItemDivisionListResponse(BaseModel):
    data: list[ItemDivisionRead]
    meta: AssignmentPage

class DivisionChoice(BaseModel):
    id: str
    code: str
    name: str
    society_id: str

class DivisionChoicesResponse(BaseModel):
    data: list[DivisionChoice]
    meta: AssignmentPage

class EligibleItem(BaseModel):
    id: str
    code: str
    name: str
    base_unit: str
    division_ref_id: str
    cost_center_ref_id: str | None = None

class EligibleItemsResponse(BaseModel):
    data: list[EligibleItem]
    meta: AssignmentPage
