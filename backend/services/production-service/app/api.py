import hashlib
import json
from urllib import error,request

from fastapi import APIRouter, Depends, Header, Query, status

from erclave_common.errors import ErclaveError
from erclave_common.config import Settings,get_settings

from .authorization import AuthorizedContext, require_production_access
from .repositories import ProductionRepository, get_production_repository
from .schemas import (
    ProductServiceCreateRequest,
    ProductServiceListResponse,
    ProductServiceResponse,
    ProductServiceUpdateRequest,
    FinishedGoodLinkRequest, FinishedGoodLinkRead, FinishedGoodLinkResponse,
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
    ProductionSalesRequestCreate, ProductionSalesRequestListResponse, ProductionSalesRequestResponse,
    ResourceAvailabilityInput, ResourceValidationRequest, ResourceValidationResponse,
    ProductionOrderResourceResponse, ProductionOrderResourceUpdateRequest,
)


router = APIRouter(prefix="/v1/production")

class HrWorkerClient:
    def __init__(self,settings):self.base_url=settings.hr_service_url.rstrip("/");self.timeout=settings.authorization_timeout_seconds
    def eligible(self,tenant_id,authorization):
        req=request.Request(f"{self.base_url}/v1/hr/workers/production-eligible",headers={"Authorization":authorization or "","X-Tenant-Id":tenant_id},method="GET")
        try:
            with request.urlopen(req,timeout=self.timeout) as response:return json.loads(response.read())["data"]
        except error.HTTPError as exc:raise ErclaveError("hr_worker_validation_denied","HR rejected worker validation.",status_code=403 if exc.code in (401,403) else 503) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc:raise ErclaveError("hr_service_unavailable","HR worker catalog is unavailable.",status_code=503) from exc
def get_hr_worker_client(settings:Settings=Depends(get_settings)):return HrWorkerClient(settings)

class UnitCatalogClient:
    def __init__(self,settings):self.base_url=settings.admin_service_url.rstrip("/");self.timeout=settings.authorization_timeout_seconds
    def require_active(self,tenant_id,code,authorization=None):
        req=request.Request(f"{self.base_url}/v1/catalogs/units-of-measure/by-code/{code}",headers={"Authorization":authorization or "","X-Tenant-Id":tenant_id},method="GET")
        try:
            with request.urlopen(req,timeout=self.timeout): return code.upper()
        except error.HTTPError as exc:
            if exc.code==404: raise ErclaveError("unit_of_measure_invalid","Unit of measure is not active in the tenant catalog.",status_code=422,details={"code":code}) from exc
            raise ErclaveError("unit_catalog_validation_denied","Unit catalog rejected validation.",status_code=403 if exc.code in (401,403) else 503) from exc
        except (error.URLError,TimeoutError) as exc: raise ErclaveError("unit_catalog_unavailable","Unit-of-measure catalog is unavailable.",status_code=503) from exc
def get_unit_catalog_client(settings:Settings=Depends(get_settings)):return UnitCatalogClient(settings)


RECIPE_NORMALIZATION_ERRORS = {
    "active_product_service_required": "Recipe requires an active product or service.",
    "recipe_unit_must_match_product_base_unit": "Recipe base unit must match the product or service base unit.",
    "machine_resource_invalid": "Recipe machinery must be active and linked to an active Human Resources area.",
    "timed_resource_unit_must_be_minute": "Labor and machinery resources must be measured in minutes.",
    "resource_type_not_authoritative": "Recipe resources must come from Inventory, Human Resources, or Machinery catalogs.",
}


def normalize_recipe_payload(repository, tenant_id, payload, *, product_service_id=None, recipe_id=None):
    try:
        return repository.normalize_recipe_payload(
            tenant_id,
            payload,
            product_service_id=product_service_id,
            recipe_id=recipe_id,
        )
    except ValueError as exc:
        raw_code = str(exc)
        code = raw_code if raw_code in RECIPE_NORMALIZATION_ERRORS else "recipe_resource_invalid"
        raise ErclaveError(
            code,
            RECIPE_NORMALIZATION_ERRORS.get(code, "Recipe contains a resource that is no longer eligible."),
            status_code=422,
        ) from exc


class ResourceAuthorityClient:
    def __init__(self,settings):
        self.inventory_url=settings.inventory_service_url.rstrip("/")
        self.hr_url=settings.hr_service_url.rstrip("/")
        self.timeout=settings.authorization_timeout_seconds

    def _call(self,base_url,path,tenant_id,authorization,method="GET",payload=None,idempotency_key=None):
        headers={"Authorization":authorization or "","X-Tenant-Id":tenant_id,"Content-Type":"application/json"}
        if idempotency_key:headers["Idempotency-Key"]=idempotency_key
        body=json.dumps(payload).encode("utf-8") if payload is not None else None
        call=request.Request(f"{base_url}{path}",headers=headers,data=body,method=method)
        try:
            with request.urlopen(call,timeout=self.timeout) as response:return json.loads(response.read()).get("data")
        except error.HTTPError as exc:
            try:detail=json.loads(exc.read()).get("error",{});code=detail.get("code","resource_authority_rejected")
            except (ValueError,AttributeError):code="resource_authority_rejected"
            raise ErclaveError(code,"An authoritative resource service rejected the operation.",status_code=exc.code if exc.code<500 else 503) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc:raise ErclaveError("resource_authority_unavailable","An authoritative resource service is unavailable.",status_code=503) from exc

    def normalize_recipe(self,tenant_id,payload,authorization):
        items={item["id"]:item for item in self._call(self.inventory_url,"/v1/inventory/items?use_in_recipe=true&status=active",tenant_id,authorization)}
        positions={item["position_id"]:item for item in self._call(self.hr_url,"/v1/hr/production-capacity",tenant_id,authorization)}
        areas={item["id"]:item for item in self._call(self.hr_url,"/v1/hr/areas",tenant_id,authorization) if item["status"]=="active"}
        resources=[]
        for item in payload.resources:
            if item.resource_type=="material":
                source=items.get(item.resource_ref_id)
                if not source or source["base_unit"]!=item.unit:raise ErclaveError("inventory_resource_invalid","Recipe material must be an active recipe-eligible inventory item in its base unit.",status_code=422)
                resources.append(item.model_copy(update={"resource_code":source["code"],"resource_name":source["name"],"unit":source["base_unit"],"unit_cost":float(source.get("default_unit_cost") or 0)}))
            elif item.resource_type=="labor":
                source=positions.get(item.resource_ref_id)
                if not source or item.unit!="MIN":raise ErclaveError("labor_resource_invalid","Recipe labor must be an active productive position measured in minutes.",status_code=422)
                resources.append(item.model_copy(update={"resource_code":source["position_id"],"resource_name":source["recipe_name"],"unit":"MIN","unit_cost":float(source["cost_per_minute"])}))
            else:resources.append(item)
        stages=[]
        for stage in payload.stages:
            area=areas.get(stage.labor_area_ref_id)
            if not area:raise ErclaveError("labor_area_invalid","Every recipe stage must reference an active HR area.",status_code=422)
            stages.append(stage.model_copy(update={"labor_area_name":area["name"]}))
        return payload.model_copy(update={"resources":resources,"stages":stages})

    def normalize_machine(self,tenant_id,payload,authorization):
        areas={item["id"]:item for item in self._call(self.hr_url,"/v1/hr/areas",tenant_id,authorization) if item["status"]=="active"}
        if payload.area_ref_id is None:return payload
        area=areas.get(payload.area_ref_id)
        if not area:raise ErclaveError("labor_area_invalid","Machine area must reference an active HR area.",status_code=422)
        return payload.model_copy(update={"area_name":area["name"]})

    def validate_product_inventory_mapping(self, tenant_id, inventory_item_id, base_unit, authorization):
        item = self._call(self.inventory_url, f"/v1/inventory/items/{inventory_item_id}", tenant_id, authorization)
        if item.get("status") != "active" or item.get("type") != "finishedGood" or item.get("base_unit", "").upper() != base_unit.upper():
            raise ErclaveError(
                "product_inventory_mapping_invalid",
                "A product must map to one active Inventory item with the same base unit.",
                status_code=422,
            )
        return item

    def create_finished_good_item(self, tenant_id, payload, authorization, idempotency_key):
        return self._call(self.inventory_url, "/v1/inventory/items", tenant_id, authorization, "POST", payload, idempotency_key)

    def observations(self,tenant_id,version,payload,authorization,idempotency_key):
        scale=payload.quantity/version.base_quantity
        materials=[{"inventory_item_id":item.resource_ref_id,"quantity":item.quantity*scale,"unit":item.unit} for item in version.resources if item.resource_type=="material"]
        inventory=self._call(self.inventory_url,"/v1/inventory/availability-checks",tenant_id,authorization,"POST",{"items":materials,"source":{"type":"production_validation","id":version.id}},f"{idempotency_key}-availability") if materials else {"items":[]}
        capacity={item["position_id"]:item for item in self._call(self.hr_url,"/v1/hr/production-capacity",tenant_id,authorization)}
        values=[]
        for item in inventory.get("items",[]):values.append(ResourceAvailabilityInput(resource_ref_id=item["inventory_item_id"],resource_type="material",available_quantity=item["available_quantity"],unit=item["unit"],unit_cost=item["unit_cost"],source="inventory.availability",allocations=item.get("allocations",[])))
        for item in version.resources:
            if item.resource_type=="labor":
                source=capacity.get(item.resource_ref_id)
                values.append(ResourceAvailabilityInput(resource_ref_id=item.resource_ref_id,resource_type="labor",available_quantity=float(source["available_minutes"]) if source else 0,unit="MIN",unit_cost=float(source["cost_per_minute"]) if source else 0,source="hr.production_capacity" if source else "hr.position_ineligible"))
        return values

    def reserve(self,tenant_id,order_id,row,authorization,idempotency_key):
        refs=[]
        for index,allocation in enumerate(row.allocations):
            value=self._call(self.inventory_url,"/v1/inventory/reservation-requests",tenant_id,authorization,"POST",{"inventory_item_id":row.resource_ref_id,"warehouse_id":allocation["warehouse_id"],"quantity":allocation["quantity"],"unit":row.unit,"source":{"type":"production_order","id":order_id,"line_id":f"{row.resource_ref_id}:{index}"}},f"{idempotency_key}-reserve-{row.resource_ref_id}-{index}")
            refs.append(value["id"])
        return refs

    def reservation_action(self,tenant_id,reservation_id,action,authorization,idempotency_key,reason):
        return self._call(self.inventory_url,f"/v1/inventory/reservations/{reservation_id}/{action}",tenant_id,authorization,"POST",{"reason":reason},f"{idempotency_key}-{action}-{reservation_id}")


def get_resource_authority_client(settings:Settings=Depends(get_settings)):return ResourceAuthorityClient(settings)


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
    inventory_mapping: str | None = Query(default=None, pattern="^(missing|linked)$"),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access(("production.product_service.read", "sales.quote.create", "sales.quote.update", "sales.order.create", "sales.order.fulfill"))),
) -> ProductServiceListResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    return ProductServiceListResponse(
        data=repository.list_product_services(
            tenant_id=tenant_id,
            limit=limit,
            status=status_filter,
            q=q,
            type_=type_filter,
            inventory_mapping=inventory_mapping,
        )
    )


@router.post("/product-services", response_model=ProductServiceResponse, status_code=status.HTTP_201_CREATED)
def create_product_service(
    payload: ProductServiceCreateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.product_service.create")),
    unit_catalog: UnitCatalogClient = Depends(get_unit_catalog_client),
    authorities: ResourceAuthorityClient = Depends(get_resource_authority_client),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    unit_catalog.require_active(tenant_id,payload.base_unit,authorization)
    if payload.inventory_item_id:
        authorities.validate_product_inventory_mapping(tenant_id, payload.inventory_item_id, payload.base_unit, authorization)
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
        inventory_item_id=payload.inventory_item_id,
        idempotency_key=resolved_key,
        request_hash=request_fingerprint(payload),
        actor_id=access.actor_id,
    )
    if product_service is None:
        raise ErclaveError("product_service_conflict", "Product or service code, or Inventory item mapping, already exists.", status_code=409)
    return ProductServiceResponse(data=product_service)

@router.put("/product-services/{product_service_id}/finished-good-link", response_model=FinishedGoodLinkResponse)
def create_and_link_finished_good(product_service_id: str, payload: FinishedGoodLinkRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access("production.product_service.update")), authorities: ResourceAuthorityClient = Depends(get_resource_authority_client)) -> FinishedGoodLinkResponse:
    tenant_id=require_tenant_id(x_tenant_id); command_key=require_idempotency_key(idempotency_key)
    product=repository.get_product_service(tenant_id,product_service_id)
    if product is None: raise ErclaveError("product_service_not_found","Product or service not found.",status_code=404)
    if product.type!="product" or product.status!="active": raise ErclaveError("product_not_linkable","Only active Production products can be linked.",status_code=422)
    if payload.inventory_item.base_unit.upper()!=product.base_unit.upper(): raise ErclaveError("product_inventory_unit_mismatch","Production and Inventory base units must match.",status_code=422)
    child_scope=f"{tenant_id}:{product_service_id}:{command_key}"
    item=authorities.create_finished_good_item(tenant_id,payload.inventory_item.model_dump(mode="json"),authorization,f"prod-fg-{hashlib.sha256(child_scope.encode()).hexdigest()[:32]}")
    authorities.validate_product_inventory_mapping(tenant_id,item["id"],product.base_unit,authorization)
    try: linked=repository.link_product_inventory_item(tenant_id,product_service_id,item["id"])
    except ValueError as exc: raise ErclaveError(str(exc),"The article was created, but its Production link is pending.",status_code=409,details={"inventory_item_id":item["id"],"link_status":"pending"}) from exc
    return FinishedGoodLinkResponse(data=FinishedGoodLinkRead(product_service=linked,inventory_item=item))


@router.get("/product-services/{product_service_id}", response_model=ProductServiceResponse)
def get_product_service(
    product_service_id: str,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access(("production.product_service.read", "sales.quote.create", "sales.quote.update", "sales.order.create", "sales.order.fulfill"))),
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    repository: ProductionRepository = Depends(get_production_repository),
    _access: AuthorizedContext = Depends(require_production_access("production.product_service.update")),
    unit_catalog: UnitCatalogClient = Depends(get_unit_catalog_client),
    authorities: ResourceAuthorityClient = Depends(get_resource_authority_client),
) -> ProductServiceResponse:
    tenant_id = require_tenant_id(x_tenant_id)
    current = repository.get_product_service(tenant_id, product_service_id)
    if current is None:
        raise ErclaveError("product_service_not_found", "Product or service not found.", status_code=404)
    if payload.base_unit: unit_catalog.require_active(tenant_id,payload.base_unit,authorization)
    mapping_id = payload.inventory_item_id if "inventory_item_id" in payload.model_fields_set else current.inventory_item_id
    mapping_unit = payload.base_unit or current.base_unit
    if current.type == "product" and not mapping_id:
        raise ErclaveError("product_inventory_item_required", "Products require an authoritative Inventory item mapping.", status_code=422)
    if current.type == "service" and mapping_id:
        raise ErclaveError("service_inventory_item_forbidden", "Services cannot map to Inventory items.", status_code=422)
    if mapping_id:
        authorities.validate_product_inventory_mapping(tenant_id, mapping_id, mapping_unit, authorization)
    try:
        product_service = repository.update_product_service(
            tenant_id=tenant_id,product_service_id=product_service_id,name=payload.name,category=payload.category,
            base_unit=payload.base_unit,target_price=payload.target_price,responsible_area=payload.responsible_area,
            cost_center=payload.cost_center,expected_margin=payload.expected_margin,description=payload.description,
            inventory_item_id=mapping_id,
        )
    except ValueError as exc:
        messages = {
            "product_base_unit_locked_by_recipe": "Product base unit cannot change after recipes exist.",
            "product_inventory_item_already_mapped": "Inventory item is already mapped to another product.",
        }
        raise ErclaveError(str(exc), messages.get(str(exc), "Product or service update conflicts with current state."), status_code=409) from exc
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.recipe.create")),
    unit_catalog: UnitCatalogClient = Depends(get_unit_catalog_client),
    authorities: ResourceAuthorityClient = Depends(get_resource_authority_client),
) -> RecipeResponse:
    resolved_tenant=require_tenant_id(x_tenant_id)
    fingerprint=request_fingerprint(payload)
    for code in {payload.base_unit,*(item.unit for item in payload.resources)}: unit_catalog.require_active(resolved_tenant,code,authorization)
    payload=normalize_recipe_payload(repository,resolved_tenant,authorities.normalize_recipe(resolved_tenant,payload,authorization),product_service_id=payload.product_service_id)
    recipe = repository.create_recipe(resolved_tenant, payload, require_idempotency_key(idempotency_key), fingerprint, access.actor_id)
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
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.recipe.update")),
    unit_catalog: UnitCatalogClient = Depends(get_unit_catalog_client),
    authorities: ResourceAuthorityClient = Depends(get_resource_authority_client),
) -> RecipeVersionResponse:
    resolved_tenant=require_tenant_id(x_tenant_id)
    fingerprint=request_fingerprint(payload,{"recipe_id":recipe_id})
    for code in {payload.base_unit,*(item.unit for item in payload.resources)}: unit_catalog.require_active(resolved_tenant,code,authorization)
    payload=normalize_recipe_payload(repository,resolved_tenant,authorities.normalize_recipe(resolved_tenant,payload,authorization),recipe_id=recipe_id)
    version = repository.create_recipe_version(resolved_tenant, recipe_id, payload, require_idempotency_key(idempotency_key), fingerprint, access.actor_id)
    if version is None:
        raise ErclaveError("recipe_not_found", "Recipe not found.", status_code=404)
    return RecipeVersionResponse(data=version)


@router.patch("/recipe-versions/{version_id}", response_model=RecipeVersionResponse)
def update_recipe_version(
    version_id: str,
    payload: RecipeVersionUpdateRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    repository: ProductionRepository = Depends(get_production_repository),
    access: AuthorizedContext = Depends(require_production_access("production.recipe.update")),
    unit_catalog: UnitCatalogClient = Depends(get_unit_catalog_client),
    authorities: ResourceAuthorityClient = Depends(get_resource_authority_client),
) -> RecipeVersionResponse:
    resolved_tenant=require_tenant_id(x_tenant_id)
    fingerprint=request_fingerprint(payload,{"version_id":version_id})
    for code in {payload.base_unit,*(item.unit for item in payload.resources)}: unit_catalog.require_active(resolved_tenant,code,authorization)
    current=repository.get_recipe_version(resolved_tenant,version_id)
    if current is None:raise ErclaveError("recipe_version_not_editable","Recipe version was not found or is no longer a draft.",status_code=409)
    payload=normalize_recipe_payload(repository,resolved_tenant,authorities.normalize_recipe(resolved_tenant,payload,authorization),recipe_id=current.recipe_id)
    version = repository.update_recipe_version(resolved_tenant, version_id, payload, require_idempotency_key(idempotency_key), fingerprint, access.actor_id)
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
def approve_recipe_version(version_id: str, payload: RecipeApprovalRequest, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), authorization:str|None=Header(default=None,alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: ProductionRepository = Depends(get_production_repository), authorities:ResourceAuthorityClient=Depends(get_resource_authority_client), unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client), access: AuthorizedContext = Depends(require_production_access("production.recipe.approve"))) -> RecipeVersionResponse:
    key = require_idempotency_key(idempotency_key)
    tenant_id=require_tenant_id(x_tenant_id);version=repository.get_recipe_version(tenant_id,version_id)
    if version is None:raise ErclaveError("recipe_version_not_found","Recipe version not found.",status_code=404)
    validation_payload=RecipeVersionUpdateRequest(base_quantity=version.base_quantity,base_unit=version.base_unit,change_reason=version.change_reason,resources=[{"resource_type":item.resource_type,"resource_ref_id":item.resource_ref_id,"resource_code":item.resource_code,"resource_name":item.resource_name,"quantity":item.quantity,"unit":item.unit,"unit_cost":item.unit_cost,"sort_order":item.sort_order} for item in version.resources],stages=[{"labor_area_ref_id":item.labor_area_ref_id,"labor_area_name":item.labor_area_name or item.name,"name":item.name,"description":item.description,"expected_minutes":item.expected_minutes,"sort_order":item.sort_order,"weight_percent":item.weight_percent,"status":item.status} for item in version.stages])
    for code in {validation_payload.base_unit,*(item.unit for item in validation_payload.resources)}:unit_catalog.require_active(tenant_id,code,authorization)
    repository.normalize_recipe_payload(tenant_id,authorities.normalize_recipe(tenant_id,validation_payload,authorization),recipe_id=version.recipe_id)
    return _transition_version(version_id, "approve", tenant_id, repository, key, request_fingerprint(payload, {"version_id": version_id, "action": "approve"}), access.actor_id, payload.approval_notes, payload.effective_from)


@router.post("/recipe-versions/{version_id}/obsolete", response_model=RecipeVersionResponse)
def obsolete_recipe_version(version_id: str, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: ProductionRepository = Depends(get_production_repository), access: AuthorizedContext = Depends(require_production_access("production.recipe.obsolete"))) -> RecipeVersionResponse:
    key = require_idempotency_key(idempotency_key)
    return _transition_version(version_id, "obsolete", require_tenant_id(x_tenant_id), repository, key, request_fingerprint(path={"version_id": version_id, "action": "obsolete"}), access.actor_id)


@router.get("/machines", response_model=MachineListResponse)
def list_machines(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),q:str|None=None,status_filter:str|None=Query(None,alias="status"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.machine.read"))):
    return MachineListResponse(data=repository.list_machines(require_tenant_id(x_tenant_id),q,status_filter))


@router.post("/machines",response_model=MachineResponse,status_code=201)
def create_machine(payload:MachineCreateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),access:AuthorizedContext=Depends(require_production_access("production.machine.create"))):
    fingerprint=request_fingerprint(payload);tenant_id=require_tenant_id(x_tenant_id);payload=authorities.normalize_machine(tenant_id,payload,authorization)
    key=require_idempotency_key(idempotency_key); value=repository.create_machine(tenant_id,payload,key,fingerprint,access.actor_id)
    if value is None: raise ErclaveError("machine_conflict","Machine code already exists.",status_code=409)
    return MachineResponse(data=value)


@router.patch("/machines/{machine_id}",response_model=MachineResponse)
def update_machine(machine_id:str,payload:MachineUpdateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),access:AuthorizedContext=Depends(require_production_access("production.machine.update"))):
    fingerprint=request_fingerprint(payload,{"machine_id":machine_id});tenant_id=require_tenant_id(x_tenant_id);payload=authorities.normalize_machine(tenant_id,payload,authorization)
    key=require_idempotency_key(idempotency_key); value=repository.update_machine(tenant_id,machine_id,payload,key,fingerprint,access.actor_id)
    if value is None: raise ErclaveError("machine_not_found","Machine not found.",status_code=404)
    return MachineResponse(data=value)


@router.post("/resource-validations",response_model=ResourceValidationResponse)
def validate_resources(payload:ResourceValidationRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),access:AuthorizedContext=Depends(require_production_access("production.order.validate"))):
    key=require_idempotency_key(idempotency_key);tenant_id=require_tenant_id(x_tenant_id);version=repository.get_recipe_version(tenant_id,payload.recipe_version_id)
    if version is None:raise ErclaveError("approved_recipe_required","An approved recipe version with the requested unit is required.",status_code=422)
    observations=authorities.observations(tenant_id,version,payload,authorization,key)
    value=repository.validate_resources(tenant_id,payload,observations,key,request_fingerprint(payload),access.actor_id)
    if value is None: raise ErclaveError("approved_recipe_required","An approved recipe version with the requested unit is required.",status_code=422)
    return ResourceValidationResponse(data=value)


@router.get("/orders",response_model=ProductionOrderListResponse)
def list_orders(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),limit:int=Query(50,ge=1,le=200),status_filter:str|None=Query(None,alias="status"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.order.read"))):
    return ProductionOrderListResponse(data=repository.list_orders(require_tenant_id(x_tenant_id),limit,status_filter))


@router.get("/order-requests",response_model=ProductionSalesRequestListResponse)
def list_sales_order_requests(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),status_filter:str|None=Query(None,alias="status"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.order.read"))):
    return ProductionSalesRequestListResponse(data=repository.list_sales_order_requests(require_tenant_id(x_tenant_id),status_filter))


@router.post("/order-requests",response_model=ProductionSalesRequestResponse,status_code=201)
def create_sales_order_request(payload:ProductionSalesRequestCreate,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),unit_catalog:UnitCatalogClient=Depends(get_unit_catalog_client),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("sales.order.fulfill"))):
    key=require_idempotency_key(idempotency_key);tenant_id=require_tenant_id(x_tenant_id);unit_catalog.require_active(tenant_id,payload.unit,authorization)
    try:value=repository.create_sales_order_request(tenant_id,payload,key,request_fingerprint(payload),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Production request requires an active product with an approved current recipe and matching unit.",status_code=422) from exc
    return ProductionSalesRequestResponse(data=value)


@router.post("/orders",response_model=ProductionOrderResponse,status_code=201)
def create_order(payload:ProductionOrderCreateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),hr_client:HrWorkerClient=Depends(get_hr_worker_client),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),access:AuthorizedContext=Depends(require_production_access("production.order.create"))):
    key=require_idempotency_key(idempotency_key)
    tenant_id=require_tenant_id(x_tenant_id);eligible={item["id"]:item for item in hr_client.eligible(tenant_id,authorization)}
    worker=eligible.get(payload.responsible_worker_id)
    if not worker:raise ErclaveError("responsible_worker_not_eligible","General responsible must be an active production-eligible worker.",status_code=422)
    assignments=[]
    for item in payload.stage_assignments:
        assignee=eligible.get(item.responsible_worker_id)
        if not assignee:raise ErclaveError("stage_worker_not_eligible","Every stage responsible must be an active production-eligible worker.",status_code=422)
        assignments.append(item.model_copy(update={"responsible_name":assignee["full_name"]}))
    payload=payload.model_copy(update={"responsible_name":worker["full_name"],"stage_assignments":assignments})
    version=repository.get_recipe_version(tenant_id,payload.recipe_version_id)
    if version is None:raise ErclaveError("approved_recipe_required","An approved recipe version with the requested unit is required.",status_code=422)
    observations=authorities.observations(tenant_id,version,payload,authorization,key)
    preview=repository.preview_resources(tenant_id,payload,observations)
    if preview is None or not preview.can_release:raise ErclaveError("resources_unavailable","Order cannot be released because authoritative resources are unavailable.",status_code=422,details={"blockers":preview.blockers if preview else []})
    order_id=f"ord_{hashlib.sha256(f'{tenant_id}:{key}'.encode()).hexdigest()[:26]}";reservation_refs={};reserved=[]
    try:
        for row in preview.rows:
            if row.resource_type=="material":
                refs=authorities.reserve(tenant_id,order_id,row,authorization,key);reservation_refs[(row.resource_ref_id or "",row.unit)]=refs;reserved.extend(refs)
        value=repository.create_order(tenant_id,payload,observations,order_id,reservation_refs,key,request_fingerprint(payload),access.actor_id)
    except Exception as exc:
        for reservation_id in reserved:
            try:authorities.reservation_action(tenant_id,reservation_id,"release",authorization,key,"Order creation was rolled back.")
            except ErclaveError:pass
        if isinstance(exc,ValueError):raise ErclaveError(str(exc),"Order cannot be released with authoritative resources.",status_code=422) from exc
        raise
    return ProductionOrderResponse(data=value)


@router.get("/orders/{order_id}",response_model=ProductionOrderResponse)
def get_order(order_id:str,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),repository:ProductionRepository=Depends(get_production_repository),_=Depends(require_production_access("production.order.read"))):
    value=repository.get_order(require_tenant_id(x_tenant_id),order_id)
    if value is None: raise ErclaveError("production_order_not_found","Production order not found.",status_code=404)
    return ProductionOrderResponse(data=value)


@router.patch("/orders/{order_id}/status",response_model=ProductionOrderResponse)
def update_order_status(order_id:str,payload:ProductionOrderStatusRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),authorities:ResourceAuthorityClient=Depends(get_resource_authority_client),access:AuthorizedContext=Depends(require_production_access("production.order.status.update"))):
    key=require_idempotency_key(idempotency_key)
    tenant_id=require_tenant_id(x_tenant_id)
    try:before=repository.preflight_order_status(tenant_id,order_id,payload.status)
    except ValueError as exc:raise ErclaveError(str(exc),"Production order status preconditions are not satisfied.",status_code=409) from exc
    if before is None:raise ErclaveError("production_order_not_found","Production order not found.",status_code=404)
    actuals={}
    if payload.status=="cancelled":
        if before.status in {"released","waiting_resources"}:
            for resource in before.resources:
                for reservation_id in resource.reservation_ref_ids:
                    authorities.reservation_action(tenant_id,reservation_id,"release",authorization,key,payload.reason)
        elif before.status not in {"in_progress","paused"}:raise ErclaveError("invalid_order_transition","Production order status transition is invalid.",status_code=409)
    first_material_issue=payload.status=="in_progress" and before.status in {"released","waiting_resources"}
    if first_material_issue:
        consumption_key=f"production-order-{order_id}-material-start"
        for resource in before.resources:
            for reservation_id in resource.reservation_ref_ids:
                movement=authorities.reservation_action(tenant_id,reservation_id,"consume",authorization,consumption_key,payload.reason)
                actuals[reservation_id]={"quantity":float(movement["quantity"]),"cost":float(movement["quantity"])*float(movement.get("unit_cost") or 0)}
    try: value=repository.update_order_status(tenant_id,order_id,payload,key,request_fingerprint(payload,{"order_id":order_id}),access.actor_id,actuals)
    except ValueError as exc: raise ErclaveError(str(exc),"Production order status transition is invalid.",status_code=409) from exc
    if value is None: raise ErclaveError("production_order_not_found","Production order not found.",status_code=404)
    return ProductionOrderResponse(data=value)


@router.patch("/orders/{order_id}/resources/{resource_id}",response_model=ProductionOrderResourceResponse)
def update_order_resource_actual(order_id:str,resource_id:str,payload:ProductionOrderResourceUpdateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.order.update"))):
    key=require_idempotency_key(idempotency_key)
    try:value=repository.update_order_resource_actual(require_tenant_id(x_tenant_id),order_id,resource_id,payload,key,request_fingerprint(payload,{"order_id":order_id,"resource_id":resource_id}),access.actor_id)
    except ValueError as exc:raise ErclaveError(str(exc),"Actual resource usage cannot be updated.",status_code=409) from exc
    if value is None:raise ErclaveError("production_order_resource_not_found","Production order resource not found.",status_code=404)
    return ProductionOrderResourceResponse(data=value)


@router.patch("/order-stages/{stage_id}",response_model=OrderStageResponse)
def update_order_stage(stage_id:str,payload:OrderStageUpdateRequest,x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),idempotency_key:str|None=Header(None,alias="Idempotency-Key"),repository:ProductionRepository=Depends(get_production_repository),access:AuthorizedContext=Depends(require_production_access("production.order_stage.update"))):
    key=require_idempotency_key(idempotency_key)
    try: value=repository.update_order_stage(require_tenant_id(x_tenant_id),stage_id,payload,key,request_fingerprint(payload,{"stage_id":stage_id}),access.actor_id)
    except ValueError as exc: raise ErclaveError(str(exc),"Production order stage transition is invalid.",status_code=409) from exc
    if value is None: raise ErclaveError("production_order_stage_not_found","Production order stage not found.",status_code=404)
    return OrderStageResponse(data=value)
