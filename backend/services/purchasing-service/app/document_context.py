"""Purchasing owns document context and frozen supplier conditions."""
from sqlalchemy import text
from erclave_common.operational_context import OperationalContext, society_currency
from erclave_common.organization_client import deny


def require_supplier(connection, tenant, supplier_id, context):
    # Same lock order as commercial assignment/condition writes.
    params = {'t': tenant, 'id': supplier_id, 'd': context.division_ref_id}
    supplier = connection.execute(text('select status from purchasing.suppliers where tenant_id=:t and id=:id for share'), params).scalar()
    assignment = connection.execute(text('select status,society_ref_id from purchasing.supplier_division_assignments where tenant_id=:t and supplier_id=:id and division_ref_id=:d for share'), params).mappings().first()
    if supplier != 'active' or not assignment or assignment['status'] != 'active' or assignment['society_ref_id'] != context.society_ref_id:
        deny('operational_context_resource_unavailable', 422, 'supplier_id')


def context_from_division(access, division_id):
    if not division_id:
        deny('purchasing_document_context_required',422,'division_ref_id')
    division=access.division(division_id)
    return OperationalContext(division_ref_id=division_id,society_ref_id=division['society_id'],
        division_code=division['code'],division_name=division['name'],cost_currency=society_currency(access,division['society_id'])).model_dump()


def authorize_document(value, access, *, legacy=False, active=True):
    if value is None:return
    context=value.get('organization_context')
    if context:
        if access is None:deny('assignment_division_denied',403)
        OperationalContext.model_validate(context).authorize(access,active=active)
    elif access is not None:
        if not access.all_divisions:deny('assignment_division_denied',403)
        if not legacy:deny('purchasing_document_history_review_required',409)


def fixed_context(value, requested_division, access):
    authorize_document(value,access)
    context=value.get('organization_context')
    if not context:deny('purchasing_document_history_review_required',409)
    if requested_division and requested_division!=context['division_ref_id']:
        deny('purchasing_document_context_locked',409,'division_ref_id')
    return context


def document_access(repository,authority,tenant,permission,authorization,actor,*,always=True):
    return authority.organization_access(tenant,permission,authorization,actor)


def divisions_for(access):
    return None if access is None or access.all_divisions else [row['id'] for row in access.divisions]


def document_scope_sql(divisions,alias='x'):
    return '' if divisions is None else f" and ({alias}.organization_context->>'division_ref_id')=any(:divisions)"


def supplier_terms(connection,tenant,supplier_id,context,*,expected=None):
    typed=OperationalContext.model_validate(context)
    require_supplier(connection,tenant,supplier_id,typed)
    row=connection.execute(text('select * from purchasing.supplier_division_terms where tenant_id=:t and supplier_id=:id and division_ref_id=:d for share'),{'t':tenant,'id':supplier_id,'d':typed.division_ref_id}).mappings().first()
    if not row or row['society_ref_id']!=typed.society_ref_id:
        deny('purchasing_document_terms_required',409,'supplier_id')
    snapshot={'supplier_id':supplier_id,'terms_revision':row['revision'],
        'values':{field:row[field] for field in ('currency','payment_terms','lead_time_days')},
        'division':{'id':typed.division_ref_id,'society_id':typed.society_ref_id,'code':typed.division_code,'name':typed.division_name}}
    if expected is not None and snapshot!=expected:
        deny('purchasing_document_terms_changed',409,'supplier_id')
    return snapshot


def check_submitted_terms(payload,snapshot):
    if payload.expected_terms_revision is not None and payload.expected_terms_revision!=snapshot['terms_revision']:
        deny('purchasing_document_terms_changed',409,'supplier_id')
    for field in ('currency','payment_terms'):
        submitted=getattr(payload,field)
        if submitted is not None and submitted!=snapshot['values'][field]:
            deny('purchasing_document_terms_mismatch',422,field)


def validate_document_items(tenant,lines,context,authority,authorization):
    for index,line in enumerate(lines):
        kind=line.get('line_type') if isinstance(line,dict) else line.line_type
        if kind!='inventory_item':continue
        item=(line.get('inventory_item_ref_id') or line.get('inventory_item_id')) if isinstance(line,dict) else line.inventory_item_id
        rows=authority.item_assignments(tenant,item,context['division_ref_id'],authorization)
        # Inventory assigns items to a Division; its response has no Society.
        # OperationalContext.authorize validates the Division's current Society.
        if not any(row.get('item_id',row.get('inventory_item_id'))==item and row.get('division_ref_id')==context['division_ref_id'] and row.get('status')=='active' for row in rows):
            deny('operational_context_resource_unavailable',422,f'lines.{index}.inventory_item_id')
