from decimal import Decimal
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class WorkerDivisionCommand(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_revision: int = Field(ge=0)
    status: Literal['active', 'inactive'] = 'active'

class PositionDivisionCommand(WorkerDivisionCommand):
    hourly_cost: Decimal = Field(ge=0, max_digits=18, decimal_places=6, allow_inf_nan=False)
    hourly_cost_currency_code: str | None = Field(None, pattern=r"^[A-Z]{3}$")
    cost_center_ref_id: str | None = Field(None, min_length=1, max_length=40)

class WorkerDivisionRead(BaseModel):
    worker_id: str
    division_ref_id: str
    labor_position_id: str
    status: Literal['active', 'inactive']
    revision: int

class PositionDivisionRead(BaseModel):
    position_id: str
    division_ref_id: str
    hourly_cost: Decimal
    hourly_cost_currency_code: str | None = None
    hourly_cost_society_ref_id: str | None = None
    hourly_cost_confirmed_at: datetime | None = None
    cost_center_ref_id: str | None = None
    cost_center_snapshot: dict | None = None
    status: Literal['active', 'inactive']
    revision: int

class AssignmentPage(BaseModel):
    total: int
    limit: int
    offset: int
class WorkerDivisionResponse(BaseModel):
    data: WorkerDivisionRead
class PositionDivisionResponse(BaseModel):
    data: PositionDivisionRead
class WorkerDivisionListResponse(BaseModel):
    data: list[WorkerDivisionRead]
    meta: AssignmentPage
class PositionDivisionListResponse(BaseModel):
    data: list[PositionDivisionRead]
    meta: AssignmentPage
class DivisionChoice(BaseModel):
    id: str
    code: str
    name: str
    society_id: str
class DivisionChoicesResponse(BaseModel):
    data: list[DivisionChoice]
    meta: AssignmentPage
class EligiblePosition(BaseModel):
    id: str
    code: str | None = None
    name: str
    recipe_name: str
    labor_area_id: str
    labor_area_name: str
    division_ref_id: str
    hourly_cost: Decimal
    hourly_cost_currency_code: str | None = None
    hourly_cost_society_ref_id: str | None = None
    hourly_cost_confirmed_at: datetime | None = None
    cost_center_ref_id: str | None = None
    intervenes_in_production: bool
    intervenes_in_maintenance: bool
class EligiblePositionsResponse(BaseModel):
    data: list[EligiblePosition]
    meta: AssignmentPage
class EligibleWorker(BaseModel):
    id: str
    employee_number: str
    full_name: str
    labor_position_id: str
    position_name: str
    position_code: str | None = None
    division_ref_id: str
    worker_assignment_revision: int | None = None
    position_assignment_revision: int | None = None
    hourly_cost: Decimal | None = None
    hourly_cost_currency_code: str | None = None
    hourly_cost_society_ref_id: str | None = None
    society_ref_id: str | None = None
    hourly_cost_confirmed_at: datetime | None = None
    minutes_per_worker: int | None = None
class EligibleWorkersResponse(BaseModel):
    data: list[EligibleWorker]
    meta: AssignmentPage

class DivisionProductionCapacityRead(BaseModel):
    position_id: str
    position_name: str
    recipe_name: str
    labor_area_id: str
    labor_area_name: str
    division_ref_id: str
    society_ref_id: str
    active_worker_count: int
    minutes_per_worker: int
    available_minutes: int
    hourly_cost: Decimal
    cost_per_minute: Decimal
    hourly_cost_currency_code: str
    eligible_worker_ids: list[str]
    capacity_pool_key: str

class DivisionCapacityMeta(BaseModel):
    capacity_scope: Literal['shared_workers'] = 'shared_workers'
    commitments_included: Literal[False] = False

class DivisionProductionCapacityResponse(BaseModel):
    data: list[DivisionProductionCapacityRead]
    meta: DivisionCapacityMeta = Field(default_factory=DivisionCapacityMeta)
