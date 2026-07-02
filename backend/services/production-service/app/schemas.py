from typing import Literal

from pydantic import BaseModel, Field


class Page(BaseModel):
    next_cursor: str | None = None


ProductServiceType = Literal["product", "service"]
ProductServiceStatus = Literal["active", "inactive", "pending_approval"]


class ProductServiceRead(BaseModel):
    id: str
    code: str
    name: str
    type: ProductServiceType
    category: str | None = None
    base_unit: str
    status: ProductServiceStatus
    target_price: float | None = None
    standard_cost: float | None = None
    responsible_area: str | None = None


class ProductServiceListResponse(BaseModel):
    data: list[ProductServiceRead]
    page: Page = Field(default_factory=Page)


class ProductServiceResponse(BaseModel):
    data: ProductServiceRead


class ProductServiceCreateRequest(BaseModel):
    code: str
    name: str
    type: ProductServiceType
    category: str | None = None
    base_unit: str
    target_price: float | None = None
    responsible_area: str | None = None


class ProductServiceUpdateRequest(BaseModel):
    name: str | None = None
    category: str | None = None
    base_unit: str | None = None
    target_price: float | None = None
    responsible_area: str | None = None


class StatusChangeRequest(BaseModel):
    status: ProductServiceStatus
    reason: str | None = None
