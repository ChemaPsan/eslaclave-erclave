from uuid import uuid4
from fastapi import APIRouter, Depends, Header, Query, Path
from erclave_common.organization_client import OrganizationAccess, require_organization_access, deny
from .repositories import get_purchasing_repository
from .organization_store import OrganizationStore
from .organization_schemas import AssignmentCommand, AssignmentResponse, AssignmentListResponse, DivisionChoicesResponse, EligiblePartiesResponse
router=APIRouter(prefix='/v1/purchasing',tags=['Organization assignments'])
from sqlalchemy import text
from erclave_common.operational_context import society_currency

@router.get('/document-divisions',operation_id='listPurchasingDocumentDivisions')
def document_divisions(q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_organization_access('purchasing',('purchasing.requisition.create','purchasing.requisition.update','purchasing.order.create','purchasing.order.update')))):
    rows=[]
    for row in access.divisions:
        if q.casefold() not in (row['code']+' '+row['name']).casefold():continue
        access.division(row['id'])
        rows.append({key:row[key] for key in ('id','code','name','society_id')}|{'cost_currency':society_currency(access,row['society_id'])})
    rows.sort(key=lambda row:(row['code'],row['id']))
    return {'data':rows[offset:offset+limit],'meta':{'total':len(rows),'limit':limit,'offset':offset}}

@router.get('/document-suppliers',operation_id='listPurchasingDocumentSuppliers')
def document_suppliers(division_id: str=Query(min_length=1,max_length=40),q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_organization_access('purchasing',('purchasing.order.create','purchasing.order.update'))),repository=Depends(get_purchasing_repository)):
    division=access.division(division_id)
    query=q.strip().replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
    join=""" from purchasing.suppliers s join purchasing.supplier_division_assignments a on a.tenant_id=s.tenant_id and a.supplier_id=s.id
        left join purchasing.supplier_division_terms ct on ct.tenant_id=a.tenant_id and ct.supplier_id=a.supplier_id and ct.division_ref_id=a.division_ref_id
        where s.tenant_id=:t and a.division_ref_id=:d and a.society_ref_id=:society and a.status='active' and s.status='active' and (s.code ilike :q or s.commercial_name ilike :q)"""
    params={'t':access.tenant_id,'d':division_id,'society':division['society_id'],'q':'%'+query+'%','limit':limit,'offset':offset}
    with repository.engine.connect() as c:
        total=c.execute(text('select count(*)'+join),params).scalar_one()
        rows=c.execute(text('select s.id,s.code,s.commercial_name name,a.division_ref_id,a.society_ref_id,ct.society_ref_id terms_society,ct.revision,ct.currency,ct.payment_terms,ct.lead_time_days'+join+' order by s.code,s.id limit :limit offset :offset'),params).mappings().all()
    result=[]
    for row in rows:
        confirmed=row['revision'] is not None and row['terms_society']==division['society_id']
        result.append({key:row[key] for key in ('id','code','name','division_ref_id','society_ref_id')}|{'commercial_terms':{'values':{key:row[key] for key in ('currency','payment_terms','lead_time_days')} if confirmed else None,'revision':row['revision'] or 0,'requires_confirmation':not confirmed}})
    return {'data':result,'meta':{'total':total,'limit':limit,'offset':offset}}
def require_purchasing_organization(permission):return require_organization_access('purchasing',permission)
def store(repository=Depends(get_purchasing_repository)):return OrganizationStore(repository)
def command_meta(key: str | None=Header(None,alias='Idempotency-Key',max_length=160),correlation: str | None=Header(None,alias='X-Correlation-Id',max_length=128)):
    if not key or len(key.strip())<8:deny('idempotency_key_required',400)
    return key.strip(),correlation or str(uuid4())
@router.get('/organization/divisions',response_model=DivisionChoicesResponse)
def divisions(q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_purchasing_organization('purchasing.supplier.read'))):
    rows=sorted((row for row in access.divisions if q.casefold() in (row['code']+' '+row['name']).casefold()),key=lambda row:row['code'])
    return {'data':rows[offset:offset+limit],'meta':{'total':len(rows),'limit':limit,'offset':offset}}
@router.get('/suppliers/{resource_id}/division-assignments',response_model=AssignmentListResponse)
def assignments(resource_id: str=Path(max_length=40),division_id: str | None=Query(None,min_length=1,max_length=40),limit: int=Query(25,ge=1,le=100),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_purchasing_organization('purchasing.supplier.read')),repository: OrganizationStore=Depends(store)):
    return repository.assignments(access,resource_id,limit,offset,division_id)
@router.put('/suppliers/{resource_id}/division-assignments/{division_id}',response_model=AssignmentResponse)
def assign(payload: AssignmentCommand,resource_id: str=Path(max_length=40),division_id: str=Path(max_length=40),meta: tuple=Depends(command_meta),access: OrganizationAccess=Depends(require_purchasing_organization('purchasing.supplier.update')),repository: OrganizationStore=Depends(store)):
    return {'data':repository.save(access,resource_id,division_id,payload,*meta)}
@router.get('/division-suppliers',response_model=EligiblePartiesResponse)
def eligible(division_id: str=Query(min_length=1,max_length=40),q: str=Query('',max_length=240),limit: int=Query(20,ge=1,le=25),offset: int=Query(0,ge=0),access: OrganizationAccess=Depends(require_purchasing_organization('purchasing.supplier.read')),repository: OrganizationStore=Depends(store)):
    return repository.eligible(access,division_id,q,limit,offset)

from .commercial_terms_schemas import CommercialTermsCommand, CommercialTermsResponse
from .commercial_terms_store import CommercialTermsStore
from .authorities import get_purchasing_authority_client

def terms_store(repository=Depends(get_purchasing_repository)):
    return CommercialTermsStore(repository)

@router.get('/suppliers/{resource_id}/division-assignments/{division_id}/commercial-terms', response_model=CommercialTermsResponse)
def commercial_terms(resource_id: str=Path(max_length=40), division_id: str=Path(max_length=40), access: OrganizationAccess=Depends(require_purchasing_organization('purchasing.supplier.read')), repository: CommercialTermsStore=Depends(terms_store)):
    return {'data': repository.read(access, resource_id, division_id)}

@router.put('/suppliers/{resource_id}/division-assignments/{division_id}/commercial-terms', response_model=CommercialTermsResponse)
def save_commercial_terms(payload: CommercialTermsCommand, resource_id: str=Path(max_length=40), division_id: str=Path(max_length=40), meta: tuple=Depends(command_meta), access: OrganizationAccess=Depends(require_purchasing_organization('purchasing.supplier.update')), repository: CommercialTermsStore=Depends(terms_store), authority=Depends(get_purchasing_authority_client)):
    return {'data': repository.save(access, resource_id, division_id, payload, *meta, authority)}
