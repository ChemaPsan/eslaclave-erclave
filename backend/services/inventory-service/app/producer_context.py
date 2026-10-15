"""Authenticated producer proofs for CC-14; Inventory owns physical effects."""
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from urllib.parse import quote, urlencode, urlparse
from pydantic import ValidationError
from erclave_common.operational_context import OperationalContext
from erclave_common.organization_client import deny


def read_proof(client, base, path, tenant, authorization, actor):
    parsed = urlparse(base)
    if (parsed.username or parsed.password or parsed.query or parsed.fragment
        or not parsed.hostname or (client.environment != 'local' and (
            parsed.scheme != 'https' or parsed.hostname.lower() in ('localhost', '127.0.0.1', '::1')))):
        deny('assignment_authority_unavailable', 503)
    return client.client.get(base, path, tenant, authorization, actor)


def maintenance_context(client, tenant, payload, authorization, actor):
    path = '/v1/maintenance/orders/' + quote(payload.source.id, safe='') + '/inventory-context?' + urlencode({'line_id': payload.source.line_id or ''})
    proof = read_proof(client, client.maintenance, path, tenant, authorization, actor)
    return validate_maintenance_proof(proof, payload)


def validate_maintenance_proof(proof, payload):
    try:
        quantity = Decimal(str(proof['quantity']))
        raw = proof['organization_context']
        context = OperationalContext.model_validate(raw) if raw is not None else None
    except (KeyError, TypeError, ValueError, InvalidOperation, ValidationError):
        deny('assignment_authority_unavailable', 503)
    if (proof.get('order_id') != payload.source.id or proof.get('line_id') != payload.source.line_id
        or proof.get('inventory_item_id') != payload.inventory_item_id
        or proof.get('warehouse_id') != payload.warehouse_id or proof.get('unit') != payload.unit
        or not quantity.is_finite() or quantity <= 0 or quantity != Decimal(str(payload.quantity))):
        deny('operational_context_mismatch', 422)
    if (proof.get('line_status') not in ('pending', 'failed', 'reserved')
        or proof.get('order_status') not in ('assigned', 'in_progress', 'waiting_parts')
        or proof.get('request_status') not in ('processing', 'needs_reconciliation', 'reserved')):
        deny('operational_context_resource_unavailable', 409)
    if context and not context.cost_currency:
        deny('operational_cost_currency_unavailable', 409)
    return context


def purchase_context(client, tenant, payload, key, authorization, actor):
    path = '/v1/purchasing/receipts/' + quote(payload.source.id, safe='') + '/lines/' + quote(payload.source.line_id or '', safe='') + '/inventory-proof'
    proof = read_proof(client, client.purchasing, path, tenant, authorization, actor)
    return validate_purchase_proof(proof, payload, key)


def validate_purchase_proof(proof, payload, key):
    try:
        context = OperationalContext.model_validate(proof['organization_context'])
        quantity = Decimal(str(proof['quantity']))
        cost = Decimal(str(proof['unit_cost']))
        original = Decimal(str(proof['original_unit_cost']))
        rate = Decimal(str(proof['cost_exchange_rate']))
        currency = proof['original_currency']
        occurred_at = datetime.fromisoformat(proof['occurred_at'].replace('Z', '+00:00'))
    except (KeyError, AttributeError, TypeError, ValueError, InvalidOperation, ValidationError):
        deny('assignment_authority_unavailable', 503)
    if not context.cost_currency:
        deny('operational_cost_currency_unavailable', 409)
    if (not all(value.is_finite() for value in (quantity, cost, original, rate))
        or quantity <= 0 or cost < 0 or original < 0 or rate <= 0
        or not isinstance(currency,str) or re.fullmatch(r'[A-Z0-9._-]{3,12}',currency) is None
        or occurred_at.tzinfo is None):
        deny('assignment_authority_unavailable', 503)
    try:
        consistent = (original * rate).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP) == cost
    except InvalidOperation:
        consistent = False
    if not consistent or (currency == context.cost_currency and rate != 1):
        deny('assignment_authority_unavailable', 503)
    if (proof.get('receipt_id') != payload.source.id or proof.get('receipt_line_id') != payload.source.line_id
        or proof.get('inventory_item_id') != payload.inventory_item_id or proof.get('warehouse_id') != payload.warehouse_id
        or proof.get('unit') != payload.unit or quantity != payload.quantity or cost != payload.unit_cost
        or occurred_at != payload.occurred_at or proof.get('inventory_idempotency_key') != key):
        deny('operational_context_mismatch', 422)
    # Producer owns conversion/rounding; Inventory retains the proof unchanged.
    return context, {name: str(proof[name]) for name in ('original_currency', 'original_unit_cost', 'cost_exchange_rate', 'unit_cost')}
