from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=240)]
Ref = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FiscalIssuerFields(StrictRequest):
    tax_id: str | None = Field(default=None, max_length=80)
    fiscal_regime: str | None = Field(default=None, max_length=80)
    cfdi_usage: str | None = Field(default=None, max_length=80)
    fiscal_address: str | None = Field(default=None, max_length=2000)
    postal_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    contact_name: str | None = Field(default=None, max_length=240)
    contact_email: str | None = Field(default=None, max_length=240)
    contact_phone: str | None = Field(default=None, max_length=80)
    contact_position: str | None = Field(default=None, max_length=240)


class FiscalIssuerCreate(FiscalIssuerFields):
    code: Code | None = None
    legal_name: Name


class FiscalIssuerUpdate(FiscalIssuerFields):
    legal_name: Name | None = None

    @model_validator(mode="after")
    def validate_patch(self):
        if "legal_name" in self.model_fields_set and self.legal_name is None:
            raise ValueError("organization_required_value")
        return self


class SocietyCreate(StrictRequest):
    code: Code | None = None
    name: Name
    issuer_id: Ref
    base_currency: Ref = "MXN"


class SocietyUpdate(StrictRequest):
    name: Name | None = None
    issuer_id: Ref | None = None
    base_currency: Ref | None = None

    @model_validator(mode="after")
    def non_null_patch(self):
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("organization_required_value")
        return self


class DivisionCreate(StrictRequest):
    code: Code | None = None
    name: Name
    society_id: Ref
    address: str | None = Field(default=None, max_length=2000)
    phone: str | None = Field(default=None, max_length=80)


class DivisionUpdate(StrictRequest):
    name: Name | None = None
    society_id: Ref | None = None
    address: str | None = Field(default=None, max_length=2000)
    phone: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def non_null_identity(self):
        if any(key in self.model_fields_set and getattr(self, key) is None for key in ("name", "society_id")):
            raise ValueError("organization_required_value")
        return self


class FiscalIssuerRead(FiscalIssuerCreate):
    id: str
    code: str
    status: Literal["active", "inactive"]


class SocietyRead(SocietyCreate):
    id: str
    code: str
    status: Literal["active", "inactive"]
    issuer_name: str


class DivisionRead(DivisionCreate):
    id: str
    code: str
    status: Literal["active", "inactive"]
    society_name: str


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int
    code_mode: Literal["managed", "manual"] = "managed"


class FiscalIssuerResponse(BaseModel):
    data: FiscalIssuerRead


class SocietyResponse(BaseModel):
    data: SocietyRead


class DivisionResponse(BaseModel):
    data: DivisionRead


class FiscalIssuerList(BaseModel):
    data: list[FiscalIssuerRead]
    meta: PageMeta


class SocietyList(BaseModel):
    data: list[SocietyRead]
    meta: PageMeta


class DivisionList(BaseModel):
    data: list[DivisionRead]
    meta: PageMeta
