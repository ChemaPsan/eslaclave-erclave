from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
class AssignmentCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=0)
    status: Literal['active','inactive'] = 'active'
class AssignmentRead(BaseModel):
    customer_id: str
    division_ref_id: str
    society_ref_id: str
    status: Literal['active','inactive']
    revision: int
class AssignmentResponse(BaseModel):
    data: AssignmentRead
class AssignmentPage(BaseModel):
    total: int
    limit: int
    offset: int
class AssignmentListResponse(BaseModel):
    data: list[AssignmentRead]
    meta: AssignmentPage
class DivisionChoice(BaseModel):
    id: str
    code: str
    name: str
    society_id: str
class DivisionChoicesResponse(BaseModel):
    data: list[DivisionChoice]
    meta: AssignmentPage
class EligibleParty(BaseModel):
    id: str
    code: str
    name: str
    division_ref_id: str
    society_ref_id: str
class EligiblePartiesResponse(BaseModel):
    data: list[EligibleParty]
    meta: AssignmentPage
