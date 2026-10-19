from typing import Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class MachineDivisionCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    division_ref_id: str = Field(min_length=1, max_length=40)
    expected_revision: int = Field(ge=0)

class MachineDivisionRead(BaseModel):
    machine_id: str
    division_ref_id: str | None = None
    revision: int

class MachineDivisionResponse(BaseModel):
    data: MachineDivisionRead

class ProductServiceDivisionCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_revision: int = Field(ge=0)
    status: Literal['active', 'inactive'] = 'active'
    cost_center_ref_id: str | None = Field(None, min_length=1, max_length=40)

class ProductServiceDivisionRead(BaseModel):
    product_service_id: str
    division_ref_id: str
    cost_center_ref_id: str | None = None
    cost_center_snapshot: dict | None = None
    status: Literal['active', 'inactive']
    revision: int
    estimated_unit_cost: Decimal | None = None
    cost_currency: str | None = None
    cost_society_ref_id: str | None = None
    cost_confirmed_at: datetime | None = None

class ProductServiceEstimatedCostCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_revision: int = Field(ge=1)
    estimated_unit_cost: Decimal | None = Field(..., ge=0, lt=Decimal('1000000000000'), max_digits=18, decimal_places=6)
    cost_currency: str | None = Field(..., pattern=r'^[A-Z]{3}$')

    @model_validator(mode='after')
    def complete_cost(self):
        if (self.estimated_unit_cost is None) != (self.cost_currency is None):
            raise ValueError('estimated_cost_currency_required')
        if self.estimated_unit_cost is not None and not self.estimated_unit_cost.is_finite():
            raise ValueError('estimated_cost_invalid')
        return self

class ProductServiceEstimatedCostRead(BaseModel):
    product_service_id: str
    division_ref_id: str
    society_ref_id: str
    cost_currency: str
    estimated_unit_cost: Decimal
    assignment_revision: int
    confirmed_at: datetime

class ProductServiceEstimatedCostResponse(BaseModel):
    data: ProductServiceEstimatedCostRead | None

class ProductServiceDivisionResponse(BaseModel):
    data: ProductServiceDivisionRead

class AssignmentPage(BaseModel):
    total: int
    limit: int
    offset: int

class ProductServiceDivisionListResponse(BaseModel):
    data: list[ProductServiceDivisionRead]
    meta: AssignmentPage

class DivisionChoice(BaseModel):
    id: str
    code: str
    name: str
    society_id: str

class DivisionChoicesResponse(BaseModel):
    data: list[DivisionChoice]
    meta: AssignmentPage

class EligibleProductService(BaseModel):
    id: str
    code: str
    name: str
    base_unit: str
    division_ref_id: str
    cost_center_ref_id: str | None = None

class EligibleProductServicesResponse(BaseModel):
    data: list[EligibleProductService]
    meta: AssignmentPage

from datetime import date, datetime
from decimal import Decimal

class EligibleMachine(BaseModel):
    id: str
    code: str
    name: str
    division_ref_id: str
    cost_society_ref_id: str
    cost_currency: str
    cost_per_minute: Decimal
    cost_confirmed_at: datetime
    available_minutes_per_day: Decimal
    committed_minutes: Decimal
    available_minutes: Decimal
    planned_date: date
    capacity_pool_key: str

class MachineCapacityPage(AssignmentPage):
    capacity_scope: Literal['physical_machine'] = 'physical_machine'
    commitments_included: bool = True

class EligibleMachinesResponse(BaseModel):
    data: list[EligibleMachine]
    meta: MachineCapacityPage

from .schemas import RecipeRead
class EligibleRecipesResponse(BaseModel):
    data: list[RecipeRead]
    meta: AssignmentPage
