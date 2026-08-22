import hashlib
import json

from fastapi import APIRouter, Depends, Header, Query

from erclave_common.errors import ErclaveError

from .authorization import AuthorizedContext, require_sales_access
from .authorities import SalesAuthorityClient, get_sales_authority_client
from .repositories import SalesRepository, get_sales_repository
from .schemas import *


router = APIRouter(prefix="/v1/sales", tags=["sales"])


def require_tenant(value):
    if not value:
        raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
    return value


def require_key(value):
    if not value or len(value.strip()) < 8:
        raise ErclaveError("idempotency_key_required", "Idempotency-Key header is required.", status_code=400)
    return value.strip()


def fingerprint(payload=None, path=None):
    document = {"body": payload.model_dump(mode="json") if payload else {}, "path": path or {}}
    return hashlib.sha256(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def conflict(exc):
    code = str(exc)
    messages = {
        "idempotency_key_reused": "Idempotency-Key was already used with a different request.",
        "quote_not_editable": "Only draft quotes can be edited.",
        "invalid_quote_transition": "Quote status transition is not allowed or the quote has expired.",
        "sales_order_not_fulfillable": "Sales order can no longer be fulfilled.",
        "sales_order_line_not_found": "Sales order line does not exist.",
        "sales_order_line_already_delivered": "A delivered order line cannot change fulfillment.",
        "sales_order_line_already_configured": "A configured order line cannot be configured again.",
        "sales_order_fulfillment_in_progress": "This order has a different fulfillment command in progress.",
        "sales_order_cancellation_in_progress": "This order has a different cancellation command in progress.",
        "sales_order_not_cancellable": "A partially or fully delivered order cannot be cancelled.",
        "sales_order_not_deliverable": "Sales order cannot receive new deliveries.",
        "delivery_quantity_exceeds_remaining": "Delivery quantity exceeds the remaining order quantity.",
        "delivery_quantity_exceeds_uncommitted": "Delivery quantity exceeds the uncommitted order quantity.",
        "delivery_exceeds_reserved_quantity": "Delivery quantity exceeds active inventory reservations.",
        "order_line_not_ready_for_delivery": "The order line is not ready for delivery.",
        "delivery_not_confirmable": "Only draft deliveries can be confirmed.",
        "delivery_not_cancellable": "Only draft deliveries can be cancelled.",
        "delivery_confirmation_in_progress": "This delivery has a different confirmation command in progress.",
        "service_actual_cost_required": "Service deliveries require a captured actual unit cost.",
        "stock_cost_is_authoritative": "Stock delivery cost is supplied by Inventory and cannot be entered manually.",
    }
    return ErclaveError(code, messages.get(code, "Sales command conflicts with current state."), status_code=409)


def resolve_lines(tenant_id, inputs, authority, authorization):
    result = []
    for item in inputs:
        product = authority.get_product(tenant_id, item.product_service_id, authorization)
        unit = authority.require_unit(tenant_id, item.unit, authorization)
        if unit != product.base_unit.upper():
            raise ErclaveError("quote_unit_mismatch", "Quote line unit must match the authoritative product or service base unit.", status_code=422, details={"product_service_id": product.id, "expected_unit": product.base_unit, "received_unit": unit})
        result.append(ResolvedQuoteLine(product=product, quantity=item.quantity, unit=unit, unit_price=item.unit_price, discount_percentage=item.discount_percentage))
    return result


@router.get("/reference-data", response_model=SalesReferenceDataResponse)
def reference_data(x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), authority: SalesAuthorityClient = Depends(get_sales_authority_client), _=Depends(require_sales_access(("sales.customer.read", "sales.customer.create", "sales.customer.update", "sales.quote.read", "sales.quote.create", "sales.quote.update", "sales.order.read", "sales.order.create")))):
    currencies = authority.list_catalog(x_tenant_id, "currencies", authorization)
    payment_terms = authority.list_catalog(x_tenant_id, "payment_terms", authorization)
    return SalesReferenceDataResponse(data=SalesReferenceDataRead(
        currencies=[ReferenceOption.model_validate(item) for item in currencies],
        payment_terms=[ReferenceOption.model_validate(item) for item in payment_terms],
    ))


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(status: CustomerStatus | None = None, q: str | None = Query(default=None, max_length=120), x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.customer.read"))):
    return CustomerListResponse(data=repository.list_customers(require_tenant(x_tenant_id), status, q))


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.customer.read"))):
    value = repository.get_customer(require_tenant(x_tenant_id), customer_id)
    if not value: raise ErclaveError("customer_not_found", "Customer not found.", status_code=404)
    return CustomerResponse(data=value)


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(payload: CustomerCreateRequest, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.customer.create"))):
    tenant_id = require_tenant(x_tenant_id); worker = authority.get_worker(tenant_id, payload.responsible_worker_id, authorization)
    authority.require_catalog_item(tenant_id, "currencies", payload.currency, authorization)
    authority.require_catalog_item(tenant_id, "payment_terms", payload.payment_terms, authorization)
    try: value = repository.create_customer(tenant_id, payload, worker, require_key(idempotency_key), fingerprint(payload), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    if not value: raise ErclaveError("customer_identity_conflict", "Customer code or tax ID already exists.", status_code=409)
    return CustomerResponse(data=value)


@router.patch("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: str, payload: CustomerUpdateRequest, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.customer.update"))):
    tenant_id = require_tenant(x_tenant_id); before = repository.get_customer(tenant_id, customer_id)
    if not before: raise ErclaveError("customer_not_found", "Customer not found.", status_code=404)
    fiscal_fields = {"legal_name", "tax_id", "tax_regime", "cfdi_use", "billing_email", "billing_address"}
    if payload.model_fields_set & fiscal_fields:
        merged = {name: getattr(payload, name) if name in payload.model_fields_set else getattr(before, name) for name in fiscal_fields}
        if any(merged.values()) and not all([merged["legal_name"], merged["tax_id"], merged["billing_email"]]):
            raise ErclaveError("incomplete_billing_profile", "Legal name, tax ID and billing email are required together.", status_code=422)
    worker = authority.get_worker(tenant_id, payload.responsible_worker_id, authorization) if payload.responsible_worker_id else None
    if payload.currency: authority.require_catalog_item(tenant_id, "currencies", payload.currency, authorization)
    if payload.payment_terms: authority.require_catalog_item(tenant_id, "payment_terms", payload.payment_terms, authorization)
    try: value = repository.update_customer(tenant_id, customer_id, payload, worker, require_key(idempotency_key), fingerprint(payload, {"customer_id": customer_id}), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    return CustomerResponse(data=value)


@router.get("/quotes", response_model=QuoteListResponse)
def list_quotes(status: QuoteStatus | None = None, customer_id: str | None = None, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.quote.read"))):
    return QuoteListResponse(data=repository.list_quotes(require_tenant(x_tenant_id), status, customer_id))


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: str, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.quote.read"))):
    value = repository.get_quote(require_tenant(x_tenant_id), quote_id)
    if not value: raise ErclaveError("quote_not_found", "Quote not found.", status_code=404)
    return QuoteResponse(data=value)


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
def create_quote(payload: QuoteCreateRequest, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.quote.create"))):
    tenant_id = require_tenant(x_tenant_id); customer = repository.get_customer(tenant_id, payload.customer_id)
    if not customer or customer.status != "active": raise ErclaveError("active_customer_required", "Quote requires an active customer.", status_code=422)
    worker = authority.get_worker(tenant_id, payload.responsible_worker_id or customer.responsible_worker_id, authorization)
    authority.require_catalog_item(tenant_id, "currencies", payload.currency or customer.currency, authorization)
    authority.require_catalog_item(tenant_id, "payment_terms", payload.payment_terms or customer.payment_terms, authorization)
    lines = resolve_lines(tenant_id, payload.lines, authority, authorization)
    try: value = repository.create_quote(tenant_id, payload, customer, worker, lines, require_key(idempotency_key), fingerprint(payload), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    if not value: raise ErclaveError("quote_code_conflict", "Quote code already exists.", status_code=409)
    return QuoteResponse(data=value)


@router.patch("/quotes/{quote_id}", response_model=QuoteResponse)
def update_quote(quote_id: str, payload: QuoteUpdateRequest, x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.quote.update"))):
    tenant_id = require_tenant(x_tenant_id); before = repository.get_quote(tenant_id, quote_id)
    if not before: raise ErclaveError("quote_not_found", "Quote not found.", status_code=404)
    customer = repository.get_customer(tenant_id, payload.customer_id) if payload.customer_id else None
    if customer and customer.status != "active": raise ErclaveError("active_customer_required", "Quote requires an active customer.", status_code=422)
    worker = authority.get_worker(tenant_id, payload.responsible_worker_id, authorization) if payload.responsible_worker_id else None
    if payload.currency: authority.require_catalog_item(tenant_id, "currencies", payload.currency, authorization)
    if payload.payment_terms: authority.require_catalog_item(tenant_id, "payment_terms", payload.payment_terms, authorization)
    lines = resolve_lines(tenant_id, payload.lines, authority, authorization) if payload.lines is not None else None
    try: value = repository.update_quote(tenant_id, quote_id, payload, customer, worker, lines, require_key(idempotency_key), fingerprint(payload, {"quote_id": quote_id}), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    return QuoteResponse(data=value)


def transition(quote_id, target, tenant_id, authorization, key, repository, authority, access):
    current = repository.get_quote(tenant_id, quote_id)
    if not current: raise ErclaveError("quote_not_found", "Quote not found.", status_code=404)
    if target in {"quoted", "approved"}:
        customer = repository.get_customer(tenant_id, current.customer_id)
        if not customer or customer.status != "active": raise ErclaveError("active_customer_required", "Quote requires an active customer.", status_code=422)
        authority.get_worker(tenant_id, current.responsible_worker_id, authorization)
        authority.require_catalog_item(tenant_id, "currencies", current.currency, authorization)
        authority.require_catalog_item(tenant_id, "payment_terms", current.payment_terms, authorization)
        for line in current.lines:
            product = authority.get_product(tenant_id, line.product_service_id, authorization)
            unit = authority.require_unit(tenant_id, line.unit, authorization)
            if product.base_unit.upper() != unit: raise ErclaveError("quote_unit_mismatch", "Quote line no longer matches the authoritative product unit.", status_code=422)
    try: value = repository.transition_quote(tenant_id, quote_id, target, require_key(key), fingerprint(path={"quote_id": quote_id, "target": target}), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    return QuoteResponse(data=value)


@router.post("/quotes/{quote_id}/submit", response_model=QuoteResponse)
def submit_quote(quote_id: str, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.quote.submit"))): return transition(quote_id, "quoted", x_tenant_id, authorization, idempotency_key, repository, authority, access)


@router.post("/quotes/{quote_id}/approve", response_model=QuoteResponse)
def approve_quote(quote_id: str, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.quote.approve"))): return transition(quote_id, "approved", x_tenant_id, authorization, idempotency_key, repository, authority, access)


@router.post("/quotes/{quote_id}/expire", response_model=QuoteResponse)
def expire_quote(quote_id: str, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.quote.expire"))): return transition(quote_id, "expired", x_tenant_id, authorization, idempotency_key, repository, authority, access)


@router.post("/quotes/{quote_id}/cancel", response_model=QuoteResponse)
def cancel_quote(quote_id: str, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.quote.cancel"))): return transition(quote_id, "cancelled", x_tenant_id, authorization, idempotency_key, repository, authority, access)


@router.get("/orders", response_model=SalesOrderListResponse)
def list_sales_orders(status: OrderStatus | None = None, customer_id: str | None = None, x_tenant_id: str = Header(alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.order.read"))):
    return SalesOrderListResponse(data=repository.list_orders(x_tenant_id, status, customer_id))


@router.get("/orders/{order_id}", response_model=SalesOrderResponse)
def get_sales_order(order_id: str, x_tenant_id: str = Header(alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.order.read"))):
    value = repository.get_order(x_tenant_id, order_id)
    if not value: raise ErclaveError("sales_order_not_found", "Sales order not found.", status_code=404)
    return SalesOrderResponse(data=value)


@router.post("/orders", response_model=SalesOrderResponse, status_code=201)
def create_sales_order(payload: SalesOrderCreateRequest, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.order.create"))):
    quote = repository.get_quote(x_tenant_id, payload.quote_id)
    if not quote or quote.status != "approved": raise ErclaveError("approved_quote_required", "Sales order requires an approved quote.", status_code=422)
    customer = repository.get_customer(x_tenant_id, quote.customer_id)
    if not customer or customer.status != "active": raise ErclaveError("active_customer_required", "Sales order requires an active customer.", status_code=422)
    authority.get_worker(x_tenant_id, quote.responsible_worker_id, authorization)
    authority.require_catalog_item(x_tenant_id, "currencies", quote.currency, authorization)
    authority.require_catalog_item(x_tenant_id, "payment_terms", quote.payment_terms, authorization)
    for line in quote.lines:
        product = authority.get_product(x_tenant_id, line.product_service_id, authorization)
        if authority.require_unit(x_tenant_id, line.unit, authorization) != product.base_unit.upper():
            raise ErclaveError("quote_unit_mismatch", "Approved quote references are no longer valid.", status_code=422)
    try: value = repository.create_order(x_tenant_id, payload, quote, require_key(idempotency_key), fingerprint(payload), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    if not value: raise ErclaveError("sales_order_identity_conflict", "Order code already exists or quote was already converted.", status_code=409)
    return SalesOrderResponse(data=value)


@router.post("/orders/{order_id}/fulfillment", response_model=SalesOrderResponse)
def configure_sales_order_fulfillment(order_id: str, payload: SalesOrderFulfillmentRequest, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.order.fulfill"))):
    command_key = require_key(idempotency_key); request_hash = fingerprint(payload, {"order_id": order_id}); order = repository.get_order(x_tenant_id, order_id)
    if not order: raise ErclaveError("sales_order_not_found", "Sales order not found.", status_code=404)
    if order.fulfillment_state == "completed":
        try: prepared = repository.prepare_order_fulfillment(x_tenant_id, order_id, payload, command_key, request_hash)
        except ValueError as exc: raise conflict(exc) from exc
        return SalesOrderResponse(data=prepared[0])
    by_id = {line.id: line for line in order.lines}; stock_sources = {}; claimed = False
    try:
        for request_line in payload.lines:
            line = by_id.get(request_line.order_line_id)
            if not line: raise ErclaveError("sales_order_line_not_found", "Sales order line not found.", status_code=404)
            if line.fulfillment_mode != "pending":
                raise ErclaveError("sales_order_line_already_configured", "A configured order line cannot be configured again.", status_code=409)
            if request_line.mode == "service" and line.product_service_type != "service": raise ErclaveError("service_fulfillment_requires_service", "Only service lines use service fulfillment.", status_code=422)
            if request_line.mode in {"stock", "production"} and line.product_service_type != "product": raise ErclaveError("product_fulfillment_required", "Stock and production fulfillment require product lines.", status_code=422)
            if request_line.mode == "stock":
                if sum(item.quantity for item in request_line.allocations) != line.ordered_quantity - line.delivered_quantity: raise ErclaveError("stock_allocation_quantity_mismatch", "Stock allocations must cover the remaining line quantity.", status_code=422)
                inventory_ids = {item.inventory_item_id for item in request_line.allocations}
                if len(inventory_ids) != 1: raise ErclaveError("single_inventory_item_required", "A sales order line must map to one inventory item.", status_code=422)
                product = authority.get_product(x_tenant_id, line.product_service_id, authorization)
                if product.inventory_item_id != next(iter(inventory_ids)):
                    raise ErclaveError("product_inventory_mapping_mismatch", "Stock fulfillment must use the Inventory item mapped to the sold product.", status_code=422)
                inventory_item = authority.get_inventory_item(x_tenant_id, product.inventory_item_id, authorization)
                if inventory_item.get("base_unit", "").upper() != line.unit.upper():
                    raise ErclaveError("product_inventory_unit_mismatch", "Mapped Inventory item unit does not match the sold product.", status_code=422)
                stock_sources[line.id] = (product, inventory_item)
        prepared = repository.prepare_order_fulfillment(x_tenant_id, order_id, payload, command_key, request_hash)
        if not prepared: raise ErclaveError("sales_order_not_found", "Sales order not found.", status_code=404)
        claimed = True
        order, command_key = prepared; by_id = {line.id: line for line in order.lines}; resolved = []
        for request_line in payload.lines:
            line = by_id[request_line.order_line_id]
            if request_line.mode == "stock":
                product, inventory_item = stock_sources[line.id]; reservations = []
                for index, allocation in enumerate(request_line.allocations):
                    reservation = authority.reserve_stock(x_tenant_id, order_id, line.id, allocation.inventory_item_id, allocation.warehouse_id, allocation.quantity, line.unit, authorization, f"{command_key}-reserve-{line.id}-{index}")
                    reservations.append(reservation)
                resolved.append({"order_line_id": line.id, "mode": "stock", "inventory_item_id": product.inventory_item_id,
                    "inventory_item_code": inventory_item.get("code"), "inventory_item_name": inventory_item.get("name"), "reservations": reservations})
            elif request_line.mode == "production":
                production_request = authority.request_production(x_tenant_id, order_id, line, order.promised_delivery_date, authorization, f"{command_key}-production-{line.id}")
                resolved.append({"order_line_id": line.id, "mode": "production", "production_request_id": production_request["id"]})
            else:
                resolved.append({"order_line_id": line.id, "mode": "service"})
        value = repository.configure_order_fulfillment(x_tenant_id, order_id, resolved, command_key, request_hash, access.actor_id)
    except ValueError as exc:
        if claimed: repository.mark_fulfillment_reconciliation(x_tenant_id, order_id)
        raise conflict(exc) from exc
    except Exception:
        if claimed: repository.mark_fulfillment_reconciliation(x_tenant_id, order_id)
        raise
    return SalesOrderResponse(data=value)


@router.post("/orders/{order_id}/cancel", response_model=SalesOrderResponse)
def cancel_sales_order(order_id: str, payload: ActionReasonRequest, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.order.cancel"))):
    command_key = require_key(idempotency_key); request_hash = fingerprint(payload, {"order_id": order_id})
    try: prepared = repository.prepare_cancel_order(x_tenant_id, order_id, command_key, request_hash)
    except ValueError as exc: raise conflict(exc) from exc
    if not prepared: raise ErclaveError("sales_order_not_found", "Sales order not found.", status_code=404)
    order, command_key = prepared
    try:
        for line in order.lines:
            for reservation in line.reservations:
                if reservation.status == "active": authority.release_reservation(x_tenant_id, reservation.reservation_ref_id, payload.reason, authorization, f"{command_key}-release-{reservation.reservation_ref_id}")
        value = repository.cancel_order(x_tenant_id, order_id, payload.reason, command_key, request_hash, access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    except Exception:
        repository.mark_cancellation_reconciliation(x_tenant_id, order_id)
        raise
    return SalesOrderResponse(data=value)


@router.get("/deliveries", response_model=DeliveryListResponse)
def list_deliveries(status: DeliveryStatus | None = None, order_id: str | None = None, x_tenant_id: str = Header(alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.delivery.read"))):
    return DeliveryListResponse(data=repository.list_deliveries(x_tenant_id, status, order_id))


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: str, x_tenant_id: str = Header(alias="X-Tenant-Id"), repository: SalesRepository = Depends(get_sales_repository), _=Depends(require_sales_access("sales.delivery.read"))):
    value = repository.get_delivery(x_tenant_id, delivery_id)
    if not value: raise ErclaveError("delivery_not_found", "Delivery not found.", status_code=404)
    return DeliveryResponse(data=value)


@router.post("/deliveries", response_model=DeliveryResponse, status_code=201)
def create_delivery(payload: DeliveryCreateRequest, x_tenant_id: str = Header(alias="X-Tenant-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), access: AuthorizedContext = Depends(require_sales_access("sales.delivery.create"))):
    try: value = repository.create_delivery(x_tenant_id, payload, require_key(idempotency_key), fingerprint(payload), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    if not value: raise ErclaveError("delivery_code_conflict", "Delivery code already exists.", status_code=409)
    return DeliveryResponse(data=value)


@router.post("/deliveries/{delivery_id}/confirm", response_model=DeliveryResponse)
def confirm_delivery(delivery_id: str, payload: ActionReasonRequest, x_tenant_id: str = Header(alias="X-Tenant-Id"), authorization: str | None = Header(default=None, alias="Authorization"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), authority: SalesAuthorityClient = Depends(get_sales_authority_client), access: AuthorizedContext = Depends(require_sales_access("sales.delivery.confirm"))):
    command_key = require_key(idempotency_key); request_hash = fingerprint(payload, {"delivery_id": delivery_id})
    try: planned = repository.prepare_delivery_confirmation(x_tenant_id, delivery_id, command_key, request_hash)
    except ValueError as exc: raise conflict(exc) from exc
    if not planned: raise ErclaveError("delivery_not_found", "Delivery not found.", status_code=404)
    delivery, plan, command_key = planned; consumptions = []
    if delivery.status == "confirmed": return DeliveryResponse(data=delivery)
    try:
        for index, item in enumerate(plan):
            movement = authority.consume_reservation(x_tenant_id, item["reservation_ref_id"], item["quantity"], payload.reason, authorization, f"{command_key}-consume-{index}-{item['reservation_ref_id']}")
            consumptions.append({**item, "unit_cost": movement.get("unit_cost") if movement.get("unit_cost") is not None else item["unit_cost"]})
        value = repository.confirm_delivery(x_tenant_id, delivery_id, consumptions, command_key, request_hash, access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    except Exception:
        repository.mark_delivery_reconciliation(x_tenant_id, delivery_id)
        raise
    return DeliveryResponse(data=value)


@router.post("/deliveries/{delivery_id}/cancel", response_model=DeliveryResponse)
def cancel_delivery(delivery_id: str, payload: ActionReasonRequest, x_tenant_id: str = Header(alias="X-Tenant-Id"), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), repository: SalesRepository = Depends(get_sales_repository), access: AuthorizedContext = Depends(require_sales_access("sales.delivery.cancel"))):
    try: value = repository.cancel_delivery(x_tenant_id, delivery_id, payload.reason, require_key(idempotency_key), fingerprint(payload, {"delivery_id": delivery_id}), access.actor_id)
    except ValueError as exc: raise conflict(exc) from exc
    if not value: raise ErclaveError("delivery_not_found", "Delivery not found.", status_code=404)
    return DeliveryResponse(data=value)
