"""Purchasing owns immutable receipt cost and origin evidence for Inventory."""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from sqlalchemy import text
from erclave_common.operational_context import OperationalContext, society_currency
from erclave_common.organization_client import deny
from .document_context import fixed_context, require_supplier


def cost_snapshot(context, currency, price, rate):
    if not currency or not context.cost_currency:
        deny("operational_cost_currency_unavailable", 409)
    original = Decimal(str(price))
    if currency == context.cost_currency:
        if rate is not None and rate != Decimal(1):
            deny("purchasing_receipt_exchange_rate_invalid", 422, "cost_exchange_rate")
        rate = Decimal(1)
    elif rate is None:
        deny("purchasing_receipt_exchange_rate_required", 422, "cost_exchange_rate")
    rate = Decimal(str(rate))
    if not original.is_finite() or original < 0 or not rate.is_finite() or rate <= 0:
        deny("purchasing_receipt_exchange_rate_invalid", 422, "cost_exchange_rate")
    with localcontext() as precision:
        precision.prec = 50
        converted = original * rate
        if converted >= Decimal("1000000000000"):
            deny("purchasing_receipt_exchange_rate_invalid", 422, "cost_exchange_rate")
        converted = converted.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        if converted >= Decimal("1000000000000"):
            deny("purchasing_receipt_exchange_rate_invalid", 422, "cost_exchange_rate")
    return {"organization_context": context.model_dump(), "original_currency": currency,
            "original_unit_cost": str(original), "cost_exchange_rate": str(rate), "unit_cost": str(converted)}


class ReceiptContext:
    def __init__(self, repository, authority):
        self.repository = repository
        self.authority = authority

    def prepare(self, tenant, payload, authorization, actor):
        order = self.repository.get_order(tenant, payload.purchase_order_id)
        if not order:
            return {}
        access = self.authority.organization_access(tenant, "purchasing.receipt.create", authorization, actor)
        inherited = OperationalContext.model_validate(fixed_context(order, None, access))
        by_id = {line["id"]: line for line in order["lines"]}
        result = {}
        cost_currency = None
        for index, item in enumerate(payload.lines):
            line = by_id.get(item.order_line_id)
            if not line or line["line_type"] != "inventory_item":
                continue
            warehouse = self.authority.warehouse(tenant, item.warehouse_id, authorization)
            if warehouse.get("status") != "active":
                deny("inactive_purchase_warehouse", 422, "warehouse_id")
            division_id = warehouse.get("division_ref_id")
            if not division_id:
                deny("operational_context_required", 409, "warehouse_id")
            division = access.division(division_id)
            if division_id != inherited.division_ref_id or division['society_id'] != inherited.society_ref_id:
                deny("operational_context_mismatch", 422, f"lines.{index}.warehouse_id")
            context = inherited
            if cost_currency is not None and cost_currency != context.cost_currency:
                deny("operational_context_mismatch", 422, f"lines.{index}.warehouse_id")
            cost_currency = context.cost_currency
            result[item.order_line_id] = cost_snapshot(context, order["currency"], line["unit_price"], payload.cost_exchange_rate)
        return result


def receipt_divisions(repository, authority, tenant, permission, authorization, actor):
    access = authority.organization_access(tenant, permission, authorization, actor)
    return None if access.all_divisions else [row["id"] for row in access.divisions]


def authorize_receipt(repository, authority, tenant, receipt, permission, authorization, actor, *, active=True):
    """Authorize the whole physical document before idempotency or any mutation."""
    physical = [line for line in receipt.get("lines", []) if line.get("warehouse_ref_id") or line.get("inventory_context_snapshot")]
    access = authority.organization_access(tenant, permission, authorization, actor)
    if receipt.get('organization_context'):
        OperationalContext.model_validate(receipt['organization_context']).authorize(access,active=active)
    elif not physical and not access.all_divisions:
        deny('assignment_division_denied',403)
    for line in physical:
        snapshot = line.get("inventory_context_snapshot")
        if snapshot:
            OperationalContext.model_validate(snapshot["organization_context"]).authorize(access, active=active)
        elif not access.all_divisions:
            deny("assignment_division_denied", 403)


def receipt_proof(repository, authority, tenant, receipt_id, line_id, authorization, actor):
    access = authority.organization_access(tenant, "inventory.movement.create", authorization, actor)
    with repository.engine.connect() as connection:
        row = connection.execute(text("""select r.id receipt_id,r.purchase_order_id,r.status receipt_status,r.received_at,
            rl.id receipt_line_id,rl.order_line_id,rl.quantity,rl.warehouse_ref_id warehouse_id,
            rl.inventory_idempotency_key,rl.inventory_context_snapshot,rl.reconciliation_status,
            ol.inventory_item_ref_id inventory_item_id,ol.unit_code unit,ol.line_type,o.status order_status
            from purchasing.purchase_receipts r
            join purchasing.purchase_receipt_lines rl on rl.tenant_id=r.tenant_id and rl.receipt_id=r.id
            join purchasing.purchase_order_lines ol on ol.tenant_id=rl.tenant_id and ol.id=rl.order_line_id
            join purchasing.purchase_orders o on o.tenant_id=r.tenant_id and o.id=r.purchase_order_id
            where r.tenant_id=:t and r.id=:r and rl.id=:l"""), {"t": tenant, "r": receipt_id, "l": line_id}).mappings().first()
    if not row:
        deny("receipt_not_found", 404)
    # A proof cannot reveal one visible line from a receipt containing another
    # line outside the actor's current scope. This is a plain read, never a lock.
    if hasattr(repository, "get_receipt"):
        receipt = repository.get_receipt(tenant, receipt_id)
        if receipt:
            authorize_receipt(repository, authority, tenant, receipt, "inventory.movement.create", authorization, actor)
    snapshot = row["inventory_context_snapshot"]
    if not snapshot:
        deny("operational_cost_history_review_required", 409)
    context = OperationalContext.model_validate(snapshot["organization_context"])
    context.authorize(access)
    if row["line_type"] != "inventory_item" or row["receipt_status"] not in {"pending_confirmation", "processing", "needs_reconciliation", "completed"} or row["order_status"] == "cancelled":
        deny("receipt_not_reconcilable", 409)
    return {**{key: row[key] for key in ("receipt_id", "purchase_order_id", "receipt_line_id", "order_line_id", "inventory_item_id", "warehouse_id", "unit", "inventory_idempotency_key")},
            "quantity": str(row["quantity"]), "occurred_at": row["received_at"].isoformat(), **snapshot}
