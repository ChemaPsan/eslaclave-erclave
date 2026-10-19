"""Sales owns document snapshots; Admin/HR/Production remain HTTP authorities."""
import hashlib
import json
from decimal import Decimal
from urllib.parse import urlencode
from sqlalchemy import text
from pydantic import BaseModel, ConfigDict, Field
from erclave_common.config import get_settings
from erclave_common.organization_client import OrganizationClient, resolve_organization_access, deny
from .commercial_terms_store import CommercialTermsStore

class QuoteContextCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    division_ref_id: str = Field(min_length=1, max_length=40)
    expected_revision: int = Field(ge=0)
    cost_exchange_rate: Decimal | None = Field(default=None, gt=0, max_digits=24, decimal_places=12, allow_inf_nan=False)

def quote_cost_currency(access, society_id):
    society=next((row for row in access.societies if row.get('id')==society_id),None)
    currency=(society or {}).get('base_currency')
    if not isinstance(currency,str) or len(currency)!=3 or not currency.isalpha():deny('operational_cost_currency_unavailable',422)
    return currency.upper()

def quote_cost_rate(cost_currency, document_currency, requested):
    if cost_currency==document_currency:
        if requested is not None and requested!=Decimal('1'):deny('operational_exchange_rate_invalid',422,'cost_exchange_rate')
        return Decimal('1')
    return requested

def pending_cost_snapshot(cost_currency, document_currency, rate):
    return {'cost_currency':cost_currency,'document_currency':document_currency,'cost_exchange_rate':str(rate) if rate is not None else None,'status':'pending'}

def collect_quote_costs(authority, tenant, lines, division_id, society_id, authorization):
    return {line.product_service_id:authority.get_division_estimated_cost(tenant,line.product_service_id,division_id,society_id,authorization) for line in lines}

def quote_access(tenant, authorization, permission, actor=None):
    data=OrganizationClient(get_settings()).session(tenant,authorization,actor)
    return resolve_organization_access(data,tenant,'sales',permission,authorization)

def guard_quote(quote, tenant, authorization, permission, actor=None):
    if not getattr(quote,'division_ref_id',None):
        return None
    access=quote_access(tenant,authorization,permission,actor)
    access.division(quote.division_ref_id,active=False)
    return access

def local_customer_context(conn, tenant, quote):
    if not quote.division_ref_id:
        return
    params={'t':tenant,'c':quote.customer_id,'d':quote.division_ref_id}
    # Match commercial-term writes: lock master before assignment.
    customer=conn.execute(text("select status from sales.customers where tenant_id=:t and id=:c for share"),params).mappings().first()
    row=conn.execute(text("select society_ref_id,status from sales.customer_division_assignments where tenant_id=:t and customer_id=:c and division_ref_id=:d for share"),params).mappings().first()
    if not customer or customer['status']!='active' or not row or row['status']!='active' or row['society_ref_id']!=quote.society_ref_id:
        deny('quote_context_unavailable',409)

def resources(quote, access, authority, lines=None, worker=None):
    organization=access.division(quote.division_ref_id)
    if organization['society_id'] != quote.society_ref_id:
        deny('quote_context_unavailable',409)
    checks=[(authority.hr_url,'/v1/hr/division-workers',worker or quote.responsible_worker_id)]
    checks.extend((authority.production_url,'/v1/production/division-product-services',row.product_service_id) for row in (lines if lines is not None else quote.lines))
    for base,path,id_ in checks:
        rows=authority._get(base+path+'?'+urlencode({'division_id':quote.division_ref_id,'resource_id':id_,'limit':1}),access.tenant_id,access.authorization)
        if not isinstance(rows,list) or not any(row.get('id')==id_ and row.get('division_ref_id')==quote.division_ref_id for row in rows):
            deny('quote_context_resource_unavailable',422)

class QuoteContextStore:
    def __init__(self, repository):
        self.repository=repository

    def save(self, access, quote_id, payload, key, correlation, authority):
        organization=access.division(payload.division_ref_id)
        preview_quote=self.repository.get_quote(access.tenant_id,quote_id)
        if not preview_quote:deny('quote_not_found',404)
        if preview_quote.division_ref_id:
            access.division(preview_quote.division_ref_id,active=False)
            if preview_quote.division_ref_id!=payload.division_ref_id:deny('quote_context_locked',409)
        preview_costs=collect_quote_costs(authority,access.tenant_id,preview_quote.lines,payload.division_ref_id,organization['society_id'],access.authorization) if preview_quote.status=='draft' and preview_quote.organization_revision==payload.expected_revision else None
        operation='quote.context:'+quote_id
        digest=hashlib.sha256(json.dumps({'actor':access.actor_id,'payload':payload.model_dump(mode='json')},sort_keys=True).encode()).hexdigest()
        with self.repository.engine.begin() as conn:
            conn.execute(text('select id from sales.quotes where tenant_id=:t and id=:i for update'),{'t':access.tenant_id,'i':quote_id})
            quote=self.repository._quote(conn,access.tenant_id,quote_id)
            if not quote:deny('quote_not_found',404)
            if quote.division_ref_id:
                access.division(quote.division_ref_id,active=False)
                if quote.division_ref_id!=payload.division_ref_id:deny('quote_context_locked',409)
            try:replay=self.repository._claim(conn,access.tenant_id,operation,key,digest)
            except ValueError as exc:deny(str(exc),409)
            if replay:return replay
            if quote.status!='draft':deny('quote_not_editable',409)
            if quote.organization_revision!=payload.expected_revision:deny('assignment_revision_conflict',409)
            terms=CommercialTermsStore(self.repository)
            master,assignment=terms._assignment(conn,access,quote.customer_id,payload.division_ref_id,lock=True)
            current=terms._read(conn,access,quote.customer_id,payload.division_ref_id,master,assignment)
            if not current.assignment_active or current.requires_confirmation or not current.values:deny('quote_context_unavailable',409)
            values=current.values.model_dump(mode='json')
            if quote.currency!=values['currency']:deny('quote_context_currency_mismatch',409)
            authority.require_catalog_item(access.tenant_id,'currencies',values['currency'],access.authorization)
            authority.require_catalog_item(access.tenant_id,'payment_terms',values['payment_terms'],access.authorization)
            candidate=quote.model_copy(update={'division_ref_id':payload.division_ref_id,'society_ref_id':organization['society_id']})
            resources(candidate,access,authority)
            cost_currency=quote_cost_currency(access,organization['society_id'])
            previous=(quote.estimated_cost_snapshot or {}).get('cost_exchange_rate')
            requested=payload.cost_exchange_rate if 'cost_exchange_rate' in payload.model_fields_set else Decimal(str(previous)) if previous is not None else None
            rate=quote_cost_rate(cost_currency,quote.currency,requested)
            cost_snapshot=pending_cost_snapshot(cost_currency,quote.currency,rate)
            snapshot={'values':values,'terms_revision':current.revision,'customer_id':quote.customer_id,'division':{k:organization[k] for k in ('id','code','name','society_id')}}
            conn.execute(text('update sales.quotes set division_ref_id=:d,society_ref_id=:s,organization_revision=organization_revision+1,commercial_terms_snapshot=cast(:v as jsonb),estimated_cost_snapshot=cast(:cost_snapshot as jsonb),estimated_cost=null,estimated_margin=null,currency=:currency,payment_terms=:payment,updated_at=now() where tenant_id=:t and id=:i'),{'t':access.tenant_id,'i':quote_id,'d':payload.division_ref_id,'s':organization['society_id'],'v':json.dumps(snapshot),'cost_snapshot':json.dumps(cost_snapshot),'currency':values['currency'],'payment':values['payment_terms']})
            conn.execute(text('update sales.quote_lines set standard_unit_cost_snapshot=null,estimated_cost=null,estimated_cost_snapshot=null where tenant_id=:t and quote_id=:i'),{'t':access.tenant_id,'i':quote_id})
            preview=self.repository._quote(conn,access.tenant_id,quote_id)
            self.repository._write_estimated_cost(conn,access.tenant_id,preview,cost_currency,preview_costs,phase='preview')
            value=self.repository._quote(conn,access.tenant_id,quote_id)
            self.repository._audit(conn,access.tenant_id,access.actor_id,'quote.context','quote',quote_id,{'before':quote.commercial_terms_snapshot,'after':snapshot,'revision':value.organization_revision,'correlation_id':correlation,'idempotency_key':key})
            self.repository._finish(conn,access.tenant_id,operation,key,value)
            return value.model_dump(mode='json')
