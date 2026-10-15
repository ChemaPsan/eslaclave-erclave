"""Context validation for service execution; Sales owns all mutations."""
from urllib.parse import urlencode
from erclave_common.organization_client import deny
from .quote_context import guard_quote

def service_context(value,tenant,authorization,permission,authority,actor=None,worker=None,stopping=False):
    scope=guard_quote(value,tenant,authorization,permission,actor)
    if not scope or stopping:return scope
    division=scope.division(value.division_ref_id)
    if division['society_id']!=value.society_ref_id:deny('quote_context_unavailable',409)
    checks=[(authority.production_url,'/v1/production/division-product-services',value.product_service_id)]
    workers={id_ for id_ in [worker,value.responsible_worker_id] if id_}
    checks.extend((authority.hr_url,'/v1/hr/division-workers',id_) for id_ in workers)
    for base,path,id_ in checks:
        rows=authority._get(base+path+'?'+urlencode({'division_id':value.division_ref_id,'resource_id':id_,'limit':1}),tenant,authorization)
        if not isinstance(rows,list) or not any(row.get('id')==id_ and row.get('division_ref_id')==value.division_ref_id for row in rows):deny('service_context_resource_unavailable',422)
    return scope
