"""Sales owns service cost snapshots. Existing unknown-currency entries stay unknown."""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation, localcontext
from erclave_common.errors import ErclaveError
from .stock_context import cost_rate

ORIGINAL_MAX = Decimal('999999999999.999999')
DOCUMENT_MAX = Decimal('9999999999999999.99')


def deny(code, status, field=None):
    details = {'field':field, 'issues':[{'loc':['body',field], 'type':'value_error', 'msg':code}]} if field else {}
    raise ErclaveError(code, 'Service cost could not be confirmed.', status, details)


def monetary_amount(value, quantum, maximum, field):
    try:
        rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        deny('operational_cost_amount_out_of_range', 422, field)
    if not rounded.is_finite() or rounded < 0 or rounded > maximum:
        deny('operational_cost_amount_out_of_range', 422, field)
    return rounded


def entry_money(service, payload, original_amount, base_currency):
    field = 'hourly_cost' if hasattr(payload, 'hourly_cost') else 'unit_cost'
    # A product of the original 18,6 amount and 24,12 rate must not lose
    # significant digits before the final two-decimal rounding.
    with localcontext() as arithmetic:
        arithmetic.prec = 64
        if not service.division_ref_id:
            if payload.cost_currency is not None or payload.cost_exchange_rate is not None:
                deny('operational_context_required', 409)
            total = monetary_amount(original_amount, Decimal('0.01'), DOCUMENT_MAX, field)
            return {'cost_currency':None,'document_currency':None,'cost_exchange_rate':None,'original_total_cost':None,'total_cost':total}
        if not base_currency or not service.currency:
            deny('operational_cost_currency_unavailable', 409)
        if payload.cost_currency is None:
            deny('operational_cost_currency_required', 422, 'cost_currency')
        if payload.cost_currency != base_currency:
            deny('operational_cost_currency_mismatch', 422, 'cost_currency')
        try:
            rate = cost_rate(base_currency, service.currency, payload.cost_exchange_rate)
        except ErclaveError as exc:
            if exc.details.get('field'):
                deny(exc.code, exc.status_code, exc.details['field'])
            raise
        original = monetary_amount(original_amount, Decimal('0.000001'), ORIGINAL_MAX, field)
        total = monetary_amount(original * rate, Decimal('0.01'), DOCUMENT_MAX, field)
        return {'cost_currency':base_currency,'document_currency':service.currency,'cost_exchange_rate':rate,'original_total_cost':original,'total_cost':total}
