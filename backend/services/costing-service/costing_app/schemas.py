from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class CostCenterCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=240)
    division_ref_id: str = Field(min_length=1, max_length=40)

class CostCenterUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    expected_revision: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=240)

class CostCenterStatus(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=1)

class CostCenterRead(BaseModel):
    id: str
    code: str
    name: str
    division_ref_id: str
    status: Literal['active', 'inactive']
    revision: int

class CostCenterResponse(BaseModel):
    data: CostCenterRead

class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int

class CostCenterListResponse(BaseModel):
    data: list[CostCenterRead]
    meta: PageMeta
