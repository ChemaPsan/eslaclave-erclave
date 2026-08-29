from datetime import date, datetime
from decimal import Decimal
from typing import Literal
import re
from pydantic import BaseModel, Field, field_validator, model_validator

LineType = Literal["inventory_item", "service"]

class PurchaseLineInput(BaseModel):
    line_type: LineType
    inventory_item_id: str | None = None
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    unit_code: str = Field(min_length=1, max_length=20)
    unit_price: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    @model_validator(mode="after")
    def reference(self):
        if self.line_type == "inventory_item" and not self.inventory_item_id: raise ValueError("inventory_item_required")
        return self

def normalize_optional(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

def validate_fiscal_profile(values) -> None:
    getter = values.get if isinstance(values, dict) else lambda name: getattr(values, name, None)
    required = ("legal_name", "tax_id", "tax_regime", "billing_email", "fiscal_postal_code")
    started = any(getter(name) for name in required)
    missing = [name for name in required if started and not getter(name)]
    if missing: raise ValueError(f"incomplete_supplier_fiscal_profile:{','.join(missing)}")

class SupplierWrite(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    commercial_name: str = Field(min_length=1, max_length=240)
    legal_name: str | None = Field(default=None, max_length=240)
    tax_id: str | None = Field(default=None, max_length=40)
    tax_regime: str | None = Field(default=None, pattern=r"^\d{3}$")
    billing_email: str | None = Field(default=None, max_length=254)
    contact_name: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=300)
    fiscal_street: str | None = Field(default=None, max_length=200)
    fiscal_exterior_number: str | None = Field(default=None, max_length=40)
    fiscal_interior_number: str | None = Field(default=None, max_length=40)
    fiscal_neighborhood: str | None = Field(default=None, max_length=160)
    fiscal_municipality: str | None = Field(default=None, max_length=160)
    fiscal_state: str | None = Field(default=None, max_length=120)
    fiscal_postal_code: str | None = Field(default=None, max_length=12)
    fiscal_country: str | None = Field(default="MX", min_length=2, max_length=2)
    currency: str = Field(min_length=3, max_length=12)
    payment_terms: str = Field(min_length=1, max_length=40)
    lead_time_days: int = Field(default=0, ge=0, le=3650)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    status: Literal["active", "inactive"] = "active"
    @field_validator("legal_name", "tax_id", "tax_regime", "billing_email", "contact_name", "website", "fiscal_street", "fiscal_exterior_number", "fiscal_interior_number", "fiscal_neighborhood", "fiscal_municipality", "fiscal_state", "fiscal_postal_code", "fiscal_country", "email", "phone", mode="before")
    @classmethod
    def trim_optional(cls,value): return normalize_optional(value)
    @field_validator("tax_id")
    @classmethod
    def validate_rfc(cls,value):
        if value is None:return None
        value=value.upper().replace(" ","").replace("-","")
        if not re.fullmatch(r"[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}",value):raise ValueError("invalid_mexican_rfc")
        return value
    @field_validator("billing_email", "email")
    @classmethod
    def validate_email(cls,value):
        if value and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",value.lower()):raise ValueError("invalid_email")
        return value.lower() if value else None
    @field_validator("fiscal_country")
    @classmethod
    def normalize_country(cls,value): return value.upper() if value else None
    @model_validator(mode="after")
    def fiscal_complete(self):
        if not self.tax_id:raise ValueError("supplier_fiscal_profile_required")
        validate_fiscal_profile(self)
        if self.fiscal_country=="MX" and self.fiscal_postal_code and not re.fullmatch(r"\d{5}",self.fiscal_postal_code):raise ValueError("invalid_mexican_postal_code")
        return self

class SupplierUpdate(BaseModel):
    commercial_name: str | None = Field(default=None, min_length=1, max_length=240)
    legal_name: str | None = Field(default=None, max_length=240)
    tax_id: str | None = Field(default=None, max_length=40)
    tax_regime: str | None = Field(default=None, pattern=r"^\d{3}$")
    billing_email: str | None = Field(default=None, max_length=254)
    contact_name: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=300)
    fiscal_street: str | None = Field(default=None, max_length=200)
    fiscal_exterior_number: str | None = Field(default=None, max_length=40)
    fiscal_interior_number: str | None = Field(default=None, max_length=40)
    fiscal_neighborhood: str | None = Field(default=None, max_length=160)
    fiscal_municipality: str | None = Field(default=None, max_length=160)
    fiscal_state: str | None = Field(default=None, max_length=120)
    fiscal_postal_code: str | None = Field(default=None, max_length=12)
    fiscal_country: str | None = Field(default=None, min_length=2, max_length=2)
    currency: str | None = Field(default=None, min_length=3, max_length=12)
    payment_terms: str | None = Field(default=None, min_length=1, max_length=40)
    lead_time_days: int | None = Field(default=None, ge=0, le=3650)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    status: Literal["active", "inactive"] | None = None
    @field_validator("legal_name", "tax_id", "tax_regime", "billing_email", "contact_name", "website", "fiscal_street", "fiscal_exterior_number", "fiscal_interior_number", "fiscal_neighborhood", "fiscal_municipality", "fiscal_state", "fiscal_postal_code", "fiscal_country", "email", "phone", mode="before")
    @classmethod
    def trim_optional(cls,value): return normalize_optional(value)
    @field_validator("tax_id")
    @classmethod
    def validate_rfc(cls,value):
        if value is None:return None
        value=value.upper().replace(" ","").replace("-","")
        if not re.fullmatch(r"[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}",value):raise ValueError("invalid_mexican_rfc")
        return value
    @field_validator("billing_email", "email")
    @classmethod
    def validate_email(cls,value):
        if value and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",value.lower()):raise ValueError("invalid_email")
        return value.lower() if value else None
    @field_validator("fiscal_country")
    @classmethod
    def normalize_country(cls,value): return value.upper() if value else None
    @model_validator(mode="after")
    def non_nullable_updates(self):
        for name in ("commercial_name","currency","payment_terms","lead_time_days","status"):
            if name in self.model_fields_set and getattr(self,name) is None:raise ValueError(f"{name}_cannot_be_null")
        return self

class RequisitionWrite(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    required_date: date
    priority: Literal["normal", "urgent"] = "normal"
    source_type: Literal["manual", "inventory_shortage", "production_shortage"] = "manual"
    source_id: str | None = Field(default=None, max_length=40)
    lines: list[PurchaseLineInput] = Field(min_length=1)
    @model_validator(mode="after")
    def unique_inventory_items(self):
        item_ids=[line.inventory_item_id for line in self.lines if line.line_type=="inventory_item"]
        if len(item_ids)!=len(set(item_ids)):raise ValueError("duplicate_requisition_item")
        return self

class ReasonRequest(BaseModel): reason: str = Field(min_length=3, max_length=500)

class PurchaseOrderWrite(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    requisition_id: str | None = None
    direct_purchase_reason: str | None = Field(default=None, max_length=500)
    supplier_id: str
    currency: str = Field(min_length=3, max_length=12)
    payment_terms: str = Field(min_length=1, max_length=40)
    lines: list[PurchaseLineInput] = Field(min_length=1)
    @model_validator(mode="after")
    def origin(self):
        if not self.requisition_id and not self.direct_purchase_reason: raise ValueError("purchase_origin_required")
        if any(line.unit_price is None for line in self.lines): raise ValueError("unit_price_required")
        return self

class ReceiptLineInput(BaseModel):
    order_line_id: str
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    warehouse_id: str | None = None

class ReceiptWrite(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    purchase_order_id: str
    received_at: datetime
    supplier_document_reference: str | None = Field(default=None, max_length=120)
    lines: list[ReceiptLineInput] = Field(min_length=1)

class DataResponse(BaseModel): data: dict
class ListResponse(BaseModel): data: list[dict]
