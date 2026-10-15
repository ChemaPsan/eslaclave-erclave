"""Validate the Production projection without accepting monetary client input."""
from decimal import Decimal, InvalidOperation
from pydantic import ValidationError
from erclave_common.operational_context import OperationalContext
from erclave_common.organization_client import deny


def finished_goods_context(order, product, order_id):
    if order.get("id") != order_id or order.get("product_service_id") != product.get("id"):
        deny("operational_context_mismatch", 422)
    value = order.get("organization_context")
    if value is None:
        return None, None
    try:
        context = OperationalContext.model_validate(value)
        original_cost = Decimal(str(order["original_unit_cost"]))
    except (ValidationError, KeyError, ValueError, TypeError, InvalidOperation):
        deny("operational_cost_currency_unavailable", 409)
    if not context.cost_currency or not original_cost.is_finite() or original_cost < 0:
        deny("operational_cost_currency_unavailable", 409)
    return context, original_cost
