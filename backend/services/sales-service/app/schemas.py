import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


CustomerType = Literal["company", "individual", "government", "internal"]
CustomerStatus = Literal["prospect", "active", "inactive", "blocked"]
QuoteStatus = Literal["draft", "quoted", "approved", "expired", "cancelled"]
CurrencyCode = Annotated[str, Field(min_length=3, max_length=12, pattern=r"^[A-Z0-9._-]+$")]
PaymentTermsCode = Annotated[str, Field(min_length=1, max_length=40, pattern=r"^[a-z0-9._-]+$")]


def normalize_email(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise ValueError("invalid_email")
    return normalized


class ContactInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(min_length=7, max_length=30)
    role: str | None = Field(default=None, max_length=120)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def require_non_blank(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("required_text_blank")
        return value.strip()

    @field_validator("role")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return normalize_email(value)


class ContactRead(ContactInput):
    id: str
    is_primary: bool
    status: Literal["active", "inactive"]


class BillingAddress(BaseModel):
    street: str | None = Field(default=None, max_length=200)
    exterior_number: str | None = Field(default=None, max_length=40)
    interior_number: str | None = Field(default=None, max_length=40)
    neighborhood: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=12)
    country: str | None = Field(default=None, max_length=80)


class CustomerCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    commercial_name: str = Field(min_length=1, max_length=200)
    customer_type: CustomerType
    status: CustomerStatus = "prospect"
    responsible_worker_id: str = Field(min_length=1, max_length=40)
    primary_contact: ContactInput
    payment_terms: PaymentTermsCode
    currency: CurrencyCode = "MXN"
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0, max_digits=18, decimal_places=2)
    legal_name: str | None = Field(default=None, max_length=240)
    tax_id: str | None = Field(default=None, max_length=20)
    tax_regime: str | None = Field(default=None, max_length=120)
    cfdi_use: str | None = Field(default=None, max_length=10)
    billing_email: str | None = Field(default=None, max_length=254)
    billing_phone: str | None = Field(default=None, max_length=30)
    billing_address: BillingAddress | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value):
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,59}", value):
            raise ValueError("invalid_customer_code")
        return value

    @field_validator("commercial_name", "responsible_worker_id", mode="before")
    @classmethod
    def require_non_blank(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("required_text_blank")
        return value.strip()

    @field_validator("legal_name", "tax_regime", "cfdi_use", "billing_phone", "notes")
    @classmethod
    def trim_optional(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("tax_id")
    @classmethod
    def normalize_tax_id(cls, value):
        if value is None or not value.strip():
            return None
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", value):
            raise ValueError("invalid_tax_id")
        return value

    @field_validator("billing_email")
    @classmethod
    def normalize_billing_email(cls, value):
        return normalize_email(value)

    @model_validator(mode="after")
    def validate_billing_identity(self):
        supplied = any([self.legal_name, self.tax_id, self.tax_regime, self.cfdi_use, self.billing_email, self.billing_address])
        if supplied and not all([self.legal_name, self.tax_id, self.billing_email]):
            raise ValueError("incomplete_billing_profile")
        return self


class CustomerUpdateRequest(BaseModel):
    commercial_name: str | None = Field(default=None, min_length=1, max_length=200)
    customer_type: CustomerType | None = None
    status: CustomerStatus | None = None
    responsible_worker_id: str | None = Field(default=None, min_length=1, max_length=40)
    primary_contact: ContactInput | None = None
    payment_terms: PaymentTermsCode | None = None
    currency: CurrencyCode | None = None
    credit_limit: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    legal_name: str | None = Field(default=None, max_length=240)
    tax_id: str | None = Field(default=None, max_length=20)
    tax_regime: str | None = Field(default=None, max_length=120)
    cfdi_use: str | None = Field(default=None, max_length=10)
    billing_email: str | None = Field(default=None, max_length=254)
    billing_phone: str | None = Field(default=None, max_length=30)
    billing_address: BillingAddress | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("commercial_name", "responsible_worker_id", mode="before")
    @classmethod
    def reject_blank_when_supplied(cls, value):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError("required_text_blank")
        return value.strip() if isinstance(value, str) else value

    @field_validator("tax_id")
    @classmethod
    def normalize_tax_id(cls, value):
        if value is None or not value.strip():
            return None
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}", value):
            raise ValueError("invalid_tax_id")
        return value

    @field_validator("billing_email")
    @classmethod
    def normalize_billing_email(cls, value):
        return normalize_email(value)

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("empty_update")
        return self


class CustomerRead(BaseModel):
    id: str
    code: str
    commercial_name: str
    customer_type: CustomerType
    status: CustomerStatus
    responsible_worker_id: str
    responsible_worker_name: str
    payment_terms: PaymentTermsCode
    currency: CurrencyCode
    credit_limit: Decimal
    legal_name: str | None = None
    tax_id: str | None = None
    tax_regime: str | None = None
    cfdi_use: str | None = None
    billing_email: str | None = None
    billing_phone: str | None = None
    billing_address: BillingAddress | None = None
    notes: str | None = None
    contacts: list[ContactRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CustomerResponse(BaseModel):
    data: CustomerRead


class CustomerListResponse(BaseModel):
    data: list[CustomerRead]


class QuoteLineInput(BaseModel):
    product_service_id: str = Field(min_length=1, max_length=40)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    unit: str = Field(min_length=1, max_length=40)
    unit_price: Decimal = Field(ge=0, max_digits=18, decimal_places=2)
    discount_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100, max_digits=7, decimal_places=4)

    @field_validator("unit")
    @classmethod
    def normalize_unit(cls, value):
        return value.strip().upper()


class QuoteCreateRequest(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=60,
        description="Tenant-scoped business code supplied by the caller or a consecutive-code authority.",
        json_schema_extra={"x-code-source": "caller-or-authoritative-generator"},
    )
    customer_id: str = Field(min_length=1, max_length=40)
    responsible_worker_id: str | None = Field(default=None, max_length=40)
    currency: CurrencyCode | None = None
    payment_terms: PaymentTermsCode | None = None
    valid_until: date
    promised_delivery_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    lines: list[QuoteLineInput] = Field(min_length=1, max_length=100)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value):
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,59}", value):
            raise ValueError("invalid_quote_code")
        return value

    @model_validator(mode="after")
    def validate_dates_and_lines(self):
        if self.valid_until < date.today():
            raise ValueError("valid_until_in_past")
        if self.promised_delivery_date and self.promised_delivery_date < date.today():
            raise ValueError("promised_delivery_date_in_past")
        if len({line.product_service_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate_quote_product")
        return self


class QuoteUpdateRequest(BaseModel):
    customer_id: str | None = Field(default=None, min_length=1, max_length=40)
    responsible_worker_id: str | None = Field(default=None, min_length=1, max_length=40)
    currency: CurrencyCode | None = None
    payment_terms: PaymentTermsCode | None = None
    valid_until: date | None = None
    promised_delivery_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)
    lines: list[QuoteLineInput] | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("empty_update")
        if self.valid_until and self.valid_until < date.today():
            raise ValueError("valid_until_in_past")
        if self.promised_delivery_date and self.promised_delivery_date < date.today():
            raise ValueError("promised_delivery_date_in_past")
        if self.lines and len({line.product_service_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate_quote_product")
        return self


class QuoteLineRead(BaseModel):
    id: str
    line_number: int
    product_service_id: str
    product_service_code: str
    product_service_name: str
    product_service_type: Literal["product", "service"]
    unit: str
    quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    standard_unit_cost_snapshot: Decimal | None = None
    estimated_cost: Decimal | None = None


class QuoteRead(BaseModel):
    id: str
    code: str
    customer_id: str
    customer_code: str
    customer_name: str
    responsible_worker_id: str
    responsible_worker_name: str
    status: QuoteStatus
    currency: CurrencyCode
    payment_terms: PaymentTermsCode
    valid_until: date
    promised_delivery_date: date | None = None
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    estimated_cost: Decimal | None = None
    estimated_margin: Decimal | None = None
    notes: str | None = None
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    lines: list[QuoteLineRead]
    created_at: datetime
    updated_at: datetime


class QuoteResponse(BaseModel):
    data: QuoteRead


class QuoteListResponse(BaseModel):
    data: list[QuoteRead]


class ReferenceOption(BaseModel):
    code: str
    name_es: str
    name_en: str


class SalesReferenceDataRead(BaseModel):
    currencies: list[ReferenceOption]
    payment_terms: list[ReferenceOption]


class SalesReferenceDataResponse(BaseModel):
    data: SalesReferenceDataRead


OrderStatus = Literal["confirmed", "fulfillment_pending", "ready", "partially_delivered", "delivered", "cancelled"]
FulfillmentMode = Literal["pending", "stock", "production", "service"]
FulfillmentStatus = Literal["pending", "reserved", "production_requested", "ready", "partially_delivered", "delivered", "cancelled"]
DeliveryStatus = Literal["draft", "confirmed", "cancelled"]


class SalesOrderCreateRequest(BaseModel):
    code: str = Field(
        min_length=1,
        max_length=60,
        description="Tenant-scoped business code supplied by the caller or a consecutive-code authority.",
        json_schema_extra={"x-code-source": "caller-or-authoritative-generator"},
    )
    quote_id: str = Field(min_length=1, max_length=40)
    promised_delivery_date: date | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value):
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,59}", value):
            raise ValueError("invalid_sales_order_code")
        return value

    @field_validator("promised_delivery_date")
    @classmethod
    def validate_promise(cls, value):
        if value and value < date.today():
            raise ValueError("promised_delivery_date_in_past")
        return value


class StockAllocationInput(BaseModel):
    inventory_item_id: str = Field(min_length=1, max_length=40)
    warehouse_id: str = Field(min_length=1, max_length=40)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6)


class OrderLineFulfillmentInput(BaseModel):
    order_line_id: str = Field(min_length=1, max_length=40)
    mode: Literal["stock", "production", "service"]
    allocations: list[StockAllocationInput] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_mode(self):
        if self.mode == "stock" and not self.allocations:
            raise ValueError("stock_allocations_required")
        if self.mode != "stock" and self.allocations:
            raise ValueError("allocations_only_for_stock")
        return self


class SalesOrderFulfillmentRequest(BaseModel):
    lines: list[OrderLineFulfillmentInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_lines(self):
        if len({line.order_line_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate_order_fulfillment_line")
        return self


class OrderReservationRead(BaseModel):
    id: str
    reservation_ref_id: str
    warehouse_ref_id: str
    reserved_quantity: Decimal
    consumed_quantity: Decimal
    unit_cost_snapshot: Decimal
    status: Literal["active", "released", "consumed"]


class SalesOrderLineRead(BaseModel):
    id: str
    quote_line_id: str
    line_number: int
    product_service_id: str
    product_service_code: str
    product_service_name: str
    product_service_type: Literal["product", "service"]
    unit: str
    ordered_quantity: Decimal
    delivered_quantity: Decimal
    unit_price: Decimal
    discount_percentage: Decimal
    total: Decimal
    standard_unit_cost_snapshot: Decimal | None = None
    estimated_cost: Decimal | None = None
    fulfillment_mode: FulfillmentMode
    fulfillment_status: FulfillmentStatus
    inventory_item_id: str | None = None
    inventory_item_code: str | None = None
    inventory_item_name: str | None = None
    production_request_id: str | None = None
    reservations: list[OrderReservationRead] = Field(default_factory=list)


class SalesOrderRead(BaseModel):
    id: str
    code: str
    quote_id: str
    quote_code: str
    customer_id: str
    customer_code: str
    customer_name: str
    responsible_worker_id: str
    responsible_worker_name: str
    status: OrderStatus
    currency: CurrencyCode
    payment_terms: PaymentTermsCode
    promised_delivery_date: date | None = None
    subtotal: Decimal
    discount_total: Decimal
    total: Decimal
    estimated_cost: Decimal | None = None
    estimated_margin: Decimal | None = None
    actual_cost: Decimal | None = None
    actual_margin: Decimal | None = None
    notes: str | None = None
    fulfillment_state: Literal["idle", "processing", "completed", "needs_reconciliation"] = "idle"
    cancellation_state: Literal["idle", "processing", "completed", "needs_reconciliation"] = "idle"
    lines: list[SalesOrderLineRead]
    created_at: datetime
    updated_at: datetime


class SalesOrderResponse(BaseModel):
    data: SalesOrderRead


class SalesOrderListResponse(BaseModel):
    data: list[SalesOrderRead]


class DeliveryLineInput(BaseModel):
    order_line_id: str = Field(min_length=1, max_length=40)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    actual_unit_cost: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=6)


class DeliveryCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    order_id: str = Field(min_length=1, max_length=40)
    scheduled_date: date
    recipient_name: str | None = Field(default=None, max_length=200)
    evidence_reference: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)
    lines: list[DeliveryLineInput] = Field(min_length=1, max_length=100)

    @field_validator("recipient_name", "evidence_reference", "notes", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value):
        value = value.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,59}", value):
            raise ValueError("invalid_delivery_code")
        return value

    @model_validator(mode="after")
    def unique_lines(self):
        if len({line.order_line_id for line in self.lines}) != len(self.lines):
            raise ValueError("duplicate_delivery_line")
        return self


class DeliveryLineRead(BaseModel):
    id: str
    order_line_id: str
    line_number: int
    product_service_id: str
    product_service_code: str
    product_service_name: str
    unit: str
    quantity: Decimal
    actual_cost: Decimal | None = None
    actual_cost_source: Literal["inventory_consumption", "service_capture", "production_report"] | None = None


class DeliveryRead(BaseModel):
    id: str
    code: str
    order_id: str
    order_code: str
    customer_id: str
    customer_name: str
    status: DeliveryStatus
    scheduled_date: date
    delivered_at: datetime | None = None
    recipient_name: str | None = None
    evidence_reference: str | None = None
    notes: str | None = None
    confirmation_state: Literal["idle", "processing", "completed", "needs_reconciliation"] = "idle"
    lines: list[DeliveryLineRead]
    created_at: datetime
    updated_at: datetime


class DeliveryResponse(BaseModel):
    data: DeliveryRead


class DeliveryListResponse(BaseModel):
    data: list[DeliveryRead]


class ActionReasonRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def require_non_blank_reason(cls, value):
        if not isinstance(value, str) or len(value.strip()) < 3:
            raise ValueError("reason_too_short")
        return value.strip()


class WorkerReference(BaseModel):
    id: str
    employee_number: str
    full_name: str
    position_name: str
    labor_area_name: str
    status: str


class ProductReference(BaseModel):
    id: str
    code: str
    name: str
    type: Literal["product", "service"]
    base_unit: str
    status: str
    target_price: Decimal | None = None
    standard_cost: Decimal | None = None
    inventory_item_id: str | None = None


class ResolvedQuoteLine(BaseModel):
    product: ProductReference
    quantity: Decimal
    unit: str
    unit_price: Decimal
    discount_percentage: Decimal
