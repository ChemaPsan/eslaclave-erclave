from fastapi import APIRouter, Depends, Header, Query, status

from erclave_common.errors import ErclaveError

from .repositories import ProductionRepository, get_production_repository
from .schemas import (
    ProductServiceCreateRequest,
    ProductServiceListResponse,
    ProductServiceResponse,
    ProductServiceUpdateRequest,
    StatusChangeRequest,
)


router = APIRouter(prefix="/v1/production")


def require_tenant_id(x_tenant_id: str | None) -> str:
    if not x_tenant_id:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    return x_tenant_id


def require_idempotency_key(idempotency_key: str | None) -> str:
    if not idempotency_key or len(idempotency_key.strip()) < 8:
        raise ErclaveError(
            "idempotency_key_required",
            "Idempotency-Key header is required for this command.",
            status_code=400,
        )
    return idempotency_key.strip()


@router.get("/product-services", response_model=ProductServiceListResponse)
def list_product_services(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=200),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    type_filter: str | None = Query(default=None, alias="type"),
    repository: ProductionRepository = Depends(get_production_repository),
) -> ProductServiceListResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    return ProductServiceListResponse(
        data=repository.list_product_services(
            tenant_id=tenant_id,
            limit=limit,
            status=status_filter,
            q=q,
            type_=type_filter,
        )
    )


@router.post("/product-services", response_model=ProductServiceResponse, status_code=status.HTTP_201_CREATED)
def create_product_service(
    payload: ProductServiceCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    require_idempotency_key(idempotency_key)
    product_service = repository.create_product_service(
        tenant_id=tenant_id,
        code=payload.code,
        name=payload.name,
        type_=payload.type,
        category=payload.category,
        base_unit=payload.base_unit,
        target_price=payload.target_price,
        responsible_area=payload.responsible_area,
    )
    if product_service is None:
        raise ErclaveError("product_service_conflict", "Product or service code already exists.", status_code=409)
    return ProductServiceResponse(data=product_service)


@router.get("/product-services/{product_service_id}", response_model=ProductServiceResponse)
def get_product_service(
    product_service_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    repository: ProductionRepository = Depends(get_production_repository),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    product_service = repository.get_product_service(tenant_id, product_service_id)
    if product_service is None:
        raise ErclaveError("product_service_not_found", "Product or service not found.", status_code=404)
    return ProductServiceResponse(data=product_service)


@router.patch("/product-services/{product_service_id}", response_model=ProductServiceResponse)
def update_product_service(
    product_service_id: str,
    payload: ProductServiceUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    repository: ProductionRepository = Depends(get_production_repository),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    product_service = repository.update_product_service(
        tenant_id=tenant_id,
        product_service_id=product_service_id,
        name=payload.name,
        category=payload.category,
        base_unit=payload.base_unit,
        target_price=payload.target_price,
        responsible_area=payload.responsible_area,
    )
    if product_service is None:
        raise ErclaveError("product_service_not_found", "Product or service not found.", status_code=404)
    return ProductServiceResponse(data=product_service)


@router.patch("/product-services/{product_service_id}/status", response_model=ProductServiceResponse)
def update_product_service_status(
    product_service_id: str,
    payload: StatusChangeRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    require_idempotency_key(idempotency_key)
    product_service = repository.update_product_service_status(
        tenant_id=tenant_id,
        product_service_id=product_service_id,
        status=payload.status,
    )
    if product_service is None:
        raise ErclaveError("product_service_not_found", "Product or service not found.", status_code=404)
    return ProductServiceResponse(data=product_service)
