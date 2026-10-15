"""Read Sales' authenticated source; never accept organization context from callers."""
from decimal import Decimal, InvalidOperation
from urllib.parse import quote
from erclave_common.config import get_settings
from erclave_common.operational_context import OperationalContext
from erclave_common.errors import ErclaveError
from .order_context import production_access

class SalesSourceClient:
    def __init__(self,settings):self.settings=settings
    def proof(self,tenant,order_id,line_id,authorization):
        from .api import ResourceAuthorityClient
        value=ResourceAuthorityClient(self.settings)._call(self.settings.sales_service_url.rstrip('/'),f'/v1/sales/orders/{quote(order_id,safe="")}/production-context?line_id={quote(line_id,safe="")}',tenant,authorization)
        if not isinstance(value,dict) or not {'order_id','order_line_id','product_service_id','quantity','unit','organization_context'}.issubset(value):
            raise ErclaveError('production_source_unavailable','Sales source proof is incomplete.',status_code=503)
        return value

def get_sales_source_client():return SalesSourceClient(get_settings())

def validate_source(proof,source,tenant,authorization,permission,actor=None):
    try:
        expected={'order_id':source.sales_order_id,'order_line_id':source.sales_order_line_id,'product_service_id':source.product_service_id,'unit':source.unit}
        if any(proof.get(k)!=v for k,v in expected.items()):raise ValueError()
        quantity=Decimal(str(proof['quantity']))
        if not quantity.is_finite() or quantity<=0 or quantity!=Decimal(str(getattr(source,"original_quantity",None) or source.quantity)):raise ValueError()
        context=OperationalContext.model_validate(proof['organization_context']) if proof['organization_context'] is not None else None
        if hasattr(source,'organization_context') and context!=source.organization_context:raise ValueError()
        due=proof.get('requested_due_date')
        if (str(source.requested_due_date) if source.requested_due_date else None)!=due:raise ValueError()
    except (ValueError,KeyError,TypeError,InvalidOperation) as exc:
        raise ErclaveError('production_request_source_conflict','Source product, quantity, unit, date or context differs from Sales.',status_code=409) from exc
    if context:context.authorize(production_access(tenant,authorization,permission,actor))
    return dict(expected,quantity=str(quantity),requested_due_date=due,organization_context=context.model_dump(mode='json') if context else None)

def source_request_fingerprint(payload):
    import hashlib,json
    values=payload.model_dump(mode='json')
    quantity=Decimal(str(payload.quantity))
    # Preserve historical request hashes when a quantity was representable by the old float schema.
    values['quantity']=float(quantity) if Decimal(str(float(quantity)))==quantity else str(quantity)
    return hashlib.sha256(json.dumps({'path':{},'body':values},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
