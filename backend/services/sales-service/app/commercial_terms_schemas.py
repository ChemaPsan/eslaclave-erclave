from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class CommercialTerms(BaseModel):
    model_config = ConfigDict(extra='forbid')
    currency: str = Field(min_length=3, max_length=12, pattern=r'^[A-Z0-9._-]+$')
    payment_terms: str = Field(min_length=1, max_length=40, pattern=r'^[a-z0-9._-]+$')
    credit_limit: Decimal = Field(ge=0, max_digits=18, decimal_places=2, allow_inf_nan=False)

class CommercialTermsCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=0)
    values: CommercialTerms

class CommercialTermsRead(BaseModel):
    resource_id: str
    division_ref_id: str
    confirmed_society_ref_id: str | None
    current_society_ref_id: str | None
    revision: int
    values: CommercialTerms | None
    requires_confirmation: bool
    assignment_active: bool

class CommercialTermsResponse(BaseModel):
    data: CommercialTermsRead
