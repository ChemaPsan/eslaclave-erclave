import hashlib
import json

from fastapi import APIRouter, Depends, Header, Query, status

from erclave_common.errors import ErclaveError

from .authorization import AuthorizedContext, require_production_access
from .repositories import ProductionRepository, get_production_repository
from .schemas import (
    ProductServiceCreateRequest,
    ProductServiceListResponse,
    ProductServiceResponse,
    ProductServiceUpdateRequest,
    RecipeApprovalRequest,
    RecipeCreateRequest,
    RecipeListResponse,
    RecipeResponse,
    RecipeVersionCreateRequest,
    RecipeVersionResponse,
    RecipeVersionUpdateRequest,
    StatusChangeRequest,
    MachineCreateRequest, MachineListResponse, MachineResponse, MachineUpdateRequest,
    OrderStageResponse, OrderStageUpdateRequest, ProductionOrderCreateRequest,
    ProductionOrderListResponse, ProductionOrderResponse, ProductionOrderStatusRequest,
    ResourceValidationRequest, ResourceValidationResponse,
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


def request_fingerprint(payload=None, path: dict | None = None) -> str:
    document = {"path": path or {}, "body": payload.model_dump(mode="json") if payload is not None else {}}
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@router.get("/product-services", response_model=ProductServiceListResponse)
def list_product_services(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=200),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    type_filter: str | None = Query(default=None, alias="type"),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access("production.product_service.read")),
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
    access: AuthorizedContext = Depends(require_production_access("production.product_service.create")),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    resolved_key = require_idempotency_key(idempotency_key)
    product_service = repository.create_product_service(
        tenant_id=tenant_id,
        code=payload.code,
        name=payload.name,
        type_=payload.type,
        category=payload.category,
        base_unit=payload.base_unit,
        target_price=payload.target_price,
        responsible_area=payload.responsible_area,
        cost_center=payload.cost_center,
        expected_margin=payload.expected_margin,
        description=payload.description,
        idempotency_key=resolved_key,
        request_hash=request_fingerprint(payload),
        actor_id=access.actor_id,
    )
    if product_service is None:
        raise ErclaveError("product_service_conflict", "Product or service code already exists.", status_code=409)
    return ProductServiceResponse(data=product_service)


@router.get("/product-services/{product_service_id}", response_model=ProductServiceResponse)
def get_product_service(
    product_service_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access("production.product_service.read")),
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
    _access: AuthorizedContext = Depends(require_production_access("production.product_service.update")),
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
        cost_center=payload.cost_center,
        expected_margin=payload.expected_margin,
        description=payload.description,
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
    access: AuthorizedContext = Depends(require_production_access("production.product_service.status.update")),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    resolved_key = require_idempotency_key(idempotency_key)
    product_service = repository.update_product_service_status(
        tenant_id=tenant_id,
        product_service_id=product_service_id,
        status=payload.status,
        idempotency_key=resolved_key,
        request_hash=request_fingerprint(payload, {"product_service_id": product_service_id}),
        actor_id=access.actor_id,
    )
    if product_service is None:
        raise ErclaveError("product_service_not_found", "Product or service not found.", status_code=404)
    return ProductServiceResponse(data=product_service)


@router.get("/recipes", response_model=RecipeListResponse)
def list_recipes(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    limit: int = Query(default=50, ge=1, le=200),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access("production.recipe.read")),
) -> RecipeListResponse:
    return RecipeListResponse(data=repository.list_recipes(require_tenant_id(x_tenant_id), limit))


@router.post("/recipes", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
def create_recipe(
    payload: RecipeCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.recipe.create")),
) -> RecipeResponse:
    recipe = repository.create_recipe(require_tenant_id(x_tenant_id), payload, require_idempotency_key(idempotency_key), request_fingerprint(payload), access.actor_id)
    if recipe is None:
        raise ErclaveError("recipe_conflict", "Product/service does not exist or recipe code already exists.", status_code=409)
    return RecipeResponse(data=recipe)


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access("production.recipe.read")),
) -> RecipeResponse:
    recipe = repository.get_recipe(require_tenant_id(x_tenant_id), recipe_id)
    if recipe is None:
        raise ErclaveError("recipe_not_found", "Recipe not found.", status_code=404)
    return RecipeResponse(data=recipe)


@router.post("/recipes/{recipe_id}/versions", response_model=RecipeVersionResponse, status_code=status.HTTP_201_CREATED)
def create_recipe_version(
    recipe_id: str,
    payload: RecipeVersionCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.recipe.update")),
) -> RecipeVersionResponse:
    version = repository.create_recipe_version(require_tenant_id(x_tenant_id), recipe_id, payload, require_idempotency_key(idempotency_key), request_fingerprint(payload, {"recipe_id": recipe_id}), access.actor_id)
    if version is None:
        raise ErclaveError("recipe_not_found", "Recipe not found.", status_code=404)
    return RecipeVersionResponse(data=version)


@router.patch("/recipe-versions/{version_id}", response_model=RecipeVersionResponse)
def update_recipe_version(
    version_id: str,
    payload: RecipeVersionUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.recipe.update")),
) -> RecipeVersionResponse:
    version = repository.update_recipe_version(require_tenant_id(x_tenant_id), version_id, payload, require_idempotency_key(idempotency_key), request_fingerprint(payload, {"version_id": version_id}), access.actor_id)
    if version is None:
        raise ErclaveError("recipe_version_not_editable", "Recipe version was not found or is no longer a draft.", status_code=409)
    return RecipeVersionResponse(data=version)


def _transition_version(version_id: str, action: str, tenant_id: str, repository: ProductionRepository, idempotency_key: str, request_hash: str, actor_id: str, approval_notes: str | None = None, effective_from: str | None = None) -> RecipeVersionResponse:
    try:
        version = repository.transition_recipe_version(tenant_id, version_id, action, actor_id, approval_notes, effective_from, idempotency_key, request_hash)
    except ValueError as error:
        if str(error) == "recipe_version_incomplete":
            raise ErclaveError("recipe_version_incomplete", "Approval requires at least one resource and one active stage.", status_code=422) from error
        raise
    if version is None:
        raise ErclaveError("invalid_status_transition", "Recipe version does not exist or cannot perform this transition.", status_code=409)
    return RecipeVersionResponse(data=version)


@router.post("/recipe-versions/{version_id}/submit", response_model=RecipeVersionResponse)
def submit_recipe_version(version_id: str, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: ProductionRepository = Depends(get_production_repository), access: AuthorizedContext = Depends(require_production_access("production.recipe.submit"))) -> RecipeVersionResponse:
    key = require_idempotency_key(idempotency_key)
    return _transition_version(version_id, "submit", require_tenant_id(x_tenant_id), repository, key, request_fingerprint(path={"version_id": version_id, "action": "submit"}), access.actor_id)


@router.post("/recipe-versions/{version_id}/approve", response_model=RecipeVersionResponse)
def approve_recipe_version(version_id: str, payload: RecipeApprovalRequest, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: ProductionRepository = Depends(get_production_repository), access: AuthorizedContext = Depends(require_production_access("production.recipe.approve"))) -> RecipeVersionResponse:
    key = require_idempotency_key(idempotency_key)
    return _transition_version(version_id, "approve", require_tenant_id(x_tenant_id), repository, key, request_fingerprint(payload, {"version_id": version_id, "action": "approve"}), access.actor_id, payload.approval_notes, payload.effective_from)


@router.post("/recipe-versions/{version_id}/obsolete", response_model=RecipeVersionResponse)
def obsolete_recipe_version(version_id: str, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: ProductionRepository = Depends(get_production_repository), access: AuthorizedContext = Depends(require_production_access("production.recipe.obsolete"))) -> RecipeVersionResponse:
    key = require_idempotency_key(idempotency_key)
    return _transition_version(version_id, "obsolete", require_tenant_id(x_tenant_id), repository, key, request_fingerprint(path={"version_id": version_id, "action": "obsolete"}), access.actor_id)


@router.get("/machines", response_model=MachineListResponse)
def list_machines(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),q:str|None=None,status_filter:str|None=Query(None,alias="status"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.machine.read"))):
    return MachineListResponse(data=repository.list_machines(require_tenant_id(x_tenant_id),q,status_filter))


@router.post("/machines",response_model=MachineResponse,status_code=201)
def create_machine(payload:MachineCreateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.machine.create"))):
    key=require_idempotency_key(idempotency_key); value=repository.create_machine(require_tenant_id(x_tenant_id),payload,key,request_fingerprint(payload),access.actor_id)
    if value is None: raise ErclaveError("machine_conflict","Machine code already exists.",status_code=409)
    return MachineResponse(data=value)


@router.patch("/machines/{machine_id}",response_model=MachineResponse)
def update_machine(machine_id:str,payload:MachineUpdateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.machine.update"))):
    key=require_idempotency_key(idempotency_key); value=repository.update_machine(require_tenant_id(x_tenant_id),machine_id,payload,key,request_fingerprint(payload,{"machine_id":machine_id}),access.actor_id)
    if value is None: raise ErclaveError("machine_not_found","Machine not found.",status_code=404)
    return MachineResponse(data=value)


@router.post("/resource-validations",response_model=ResourceValidationResponse)
def validate_resources(payload:ResourceValidationRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.order.validate"))):
    key=require_idempotency_key(idempotency_key); value=repository.validate_resources(require_tenant_id(x_tenant_id),payload,key,request_fingerprint(payload),access.actor_id)
    if value is None: raise ErclaveError("approved_recipe_required","An approved recipe version with the requested unit is required.",status_code=422)
    return ResourceValidationResponse(data=value)


@router.get("/orders",response_model=ProductionOrderListResponse)
def list_orders(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),limit:int=Query(50,ge=1,le=200),status_filter:str|None=Query(None,alias="status"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.order.read"))):
    return ProductionOrderListResponse(data=repository.list_orders(require_tenant_id(x_tenant_id),limit,status_filter))


@router.post("/orders",response_model=ProductionOrderResponse,status_code=201)
def create_order(payload:ProductionOrderCreateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.order.create"))):
    key=require_idempotency_key(idempotency_key)
    try: value=repository.create_order(require_tenant_id(x_tenant_id),payload,key,request_fingerprint(payload),access.actor_id)
    except ValueError as exc: raise ErclaveError(str(exc),"Order cannot be released with the observed resources.",status_code=422) from exc
    return ProductionOrderResponse(data=value)


@router.get("/orders/{order_id}",response_model=ProductionOrderResponse)
def get_order(order_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.order.read"))):
    value=repository.get_order(require_tenant_id(x_tenant_id),order_id)
    if value is None: raise ErclaveError("production_order_not_found","Production order not found.",status_code=404)
    return ProductionOrderResponse(data=value)


@router.patch("/orders/{order_id}/status",response_model=ProductionOrderResponse)
def update_order_status(order_id:str,payload:ProductionOrderStatusRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.order.status.update"))):
    key=require_idempotency_key(idempotency_key)
    try: value=repository.update_order_status(require_tenant_id(x_tenant_id),order_id,payload,key,request_fingerprint(payload,{"order_id":order_id}),access.actor_id)
    except ValueError as exc: raise ErclaveError(str(exc),"Production order status transition is invalid.",status_code=409) from exc
    if value is None: raise ErclaveError("production_order_not_found","Production order not found.",status_code=404)
    return ProductionOrderResponse(data=value)


@router.patch("/order-stages/{stage_id}",response_model=OrderStageResponse)
def update_order_stage(stage_id:str,payload:OrderStageUpdateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.order_stage.update"))):
    key=require_idempotency_key(idempotency_key)
    try: value=repository.update_order_stage(require_tenant_id(x_tenant_id),stage_id,payload,key,request_fingerprint(payload,{"stage_id":stage_id}),access.actor_id)
    except ValueError as exc: raise ErclaveError(str(exc),"Production order stage transition is invalid.",status_code=409) from exc
    if value is None: raise ErclaveError("production_order_stage_not_found","Production order stage not found.",status_code=404)
    return OrderStageResponse(data=value)
