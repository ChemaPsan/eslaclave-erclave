"""Sales converts original inventory cost only with a frozen explicit rate."""
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode
from erclave_common.organization_client import deny
from erclave_common.operational_context import society_currency
from .quote_context import guard_quote


def cost_rate(original_currency, order_currency, captured):
    if original_currency==order_currency:
        if captured is not None and captured!=Decimal('1'):
            deny('operational_exchange_rate_invalid',422,'cost_exchange_rate')
        return Decimal('1')
    if captured is None or not captured.is_finite() or captured<=0:
        deny('operational_exchange_rate_required',422,'cost_exchange_rate')
    return captured


def convert_cost(amount, rate):
    return (Decimal(str(amount))*rate).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)


def stock_context(order, payload, tenant, authorization, actor, authority):
    access=guard_quote(order,tenant,authorization,'sales.order.fulfill',actor)
    if access is None:return None,None
    division=access.division(order.division_ref_id)
    if division['society_id']!=order.society_ref_id:deny('operational_context_mismatch',409)
    currency=order.cost_currency or society_currency(access,order.society_ref_id)
    rate=cost_rate(currency,order.currency,payload.cost_exchange_rate)
    if order.cost_exchange_rate is not None and rate!=order.cost_exchange_rate:deny('operational_exchange_rate_locked',409)
    lines={line.id:line for line in order.lines}
    for requested in payload.lines:
        line=lines.get(requested.order_line_id)
        if line is None:deny('sales_order_line_not_found',404)
        rows=authority._get(authority.production_url+'/v1/production/division-product-services?'+urlencode({'division_id':order.division_ref_id,'resource_id':line.product_service_id,'limit':1}),tenant,authorization)
        if not isinstance(rows,list) or not any(row.get('id')==line.product_service_id and row.get('division_ref_id')==order.division_ref_id for row in rows):deny('service_context_resource_unavailable',422)
    return currency,rate
