"""Purchasing document integration: only the Local demo tenant, rolled back."""
import importlib,os,sys
from contextlib import contextmanager
from dataclasses import replace
from datetime import date,datetime,timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import OrganizationAccess

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):del sys.modules[name]
repos=importlib.import_module('app.repositories');schemas=importlib.import_module('app.schemas')
api=importlib.import_module('app.api');orgapi=importlib.import_module('app.organization_api')
dc=importlib.import_module('app.document_context');rc=importlib.import_module('app.receipt_context');reports=importlib.import_module('app.reports')
TENANT='ten_739ee59d765d5e14818674800d'
URL=os.getenv('ERCLAVE_TEST_DATABASE_URL','')
pytestmark=pytest.mark.skipif(not URL,reason='Local PostgreSQL required')

@pytest.fixture
def pg():
    url=make_url(URL)
    assert url.host=='127.0.0.1' and url.port==5434 and url.database=='erclave_local' and not url.query
    repo=repos.PurchasingRepository(URL);engine=repo.engine
    with engine.connect() as c:
        tx=c.begin()
        class Transaction:
            @contextmanager
            def begin(self):yield c
            @contextmanager
            def connect(self):yield c
        repo.engine=Transaction()
        try:
            assert c.execute(text('select id from admin.tenants')).scalars().all()==[TENANT]
            suffix=uuid4().hex[:14];actor='cc15-'+suffix
            division={'id':'cc15-div-'+suffix,'society_id':'cc15-soc-'+suffix,'code':'TEST','name':'Synthetic'}
            scope=OrganizationAccess(TENANT,actor,('purchasing.order.create',),(division,),False,False,societies=({'id':division['society_id'],'base_currency':'MXN'},))
            context=dc.context_from_division(scope,division['id'])
            suppliers=[]
            for i in range(2):
                supplier=repo.create_supplier(TENANT,schemas.SupplierWrite(code=f'S{i}-{suffix}',commercial_name='Synthetic',legal_name='Synthetic SA',tax_id=f'XQZ01010{i}{suffix[:3].upper()}',tax_regime='601',billing_email='test@example.com',fiscal_postal_code='01234',currency='MXN',payment_terms='cash'),f'{suffix}-s{i}',f's{i}',actor)
                suppliers.append(supplier)
                c.execute(text("insert into purchasing.supplier_division_assignments(tenant_id,supplier_id,division_ref_id,society_ref_id,status,revision) values(:t,:id,:d,:s,'active',1)"),{'t':TENANT,'id':supplier['id'],'d':division['id'],'s':division['society_id']})
                c.execute(text("insert into purchasing.supplier_division_terms(tenant_id,supplier_id,division_ref_id,society_ref_id,revision,currency,payment_terms,lead_time_days) values(:t,:id,:d,:s,1,:currency,'cash',3)"),{'t':TENANT,'id':supplier['id'],'d':division['id'],'s':division['society_id'],'currency':'USD' if i==0 else 'EUR'})
            line=schemas.PurchaseLineInput(line_type='service',description='Synthetic service',quantity=1,unit_code='E48',unit_price=Decimal('4.12'))
            payload=schemas.PurchaseOrderWrite(code='PO-'+suffix,supplier_id=suppliers[0]['id'],division_ref_id=division['id'],direct_purchase_reason='Synthetic direct purchase',lines=[line])
            calls=[]
            authority=SimpleNamespace(organization_access=lambda *args:scope,require_catalog=lambda *args:calls.append(args),require_unit=lambda *args:None,allocate_code=lambda tenant,document,code,*args:{'code':code,'mode':'manual'})
            yield SimpleNamespace(repo=repo,c=c,suffix=suffix,actor=actor,scope=scope,context=context,suppliers=suppliers,line=line,payload=payload,authority=authority,calls=calls)
        finally:tx.rollback()
    engine.dispose()

def create_order(f,payload=None,key='create'):
    return f.repo.create_order(TENANT,payload or f.payload,f.suffix+'-'+key,key,f.actor,context=f.context,organization_access=f.scope)

def test_failed_reconciliation_resumes_same_actor_key_only_pending_lines(pg):
    from datetime import datetime,timezone
    f=pg;order=create_order(f)
    f.repo.issue_order(TENANT,order['id'],f.suffix+'-issue','issue',f.actor,organization_access=f.scope)
    payload=schemas.ReceiptWrite(code='REC-'+f.suffix,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[schemas.ReceiptLineInput(order_line_id=order['lines'][0]['id'],quantity=1)])
    receipt,_=f.repo.prepare_receipt(TENANT,payload,f.suffix+'-receipt','receipt',f.actor,organization_access=f.scope)
    key=f.suffix+'-reconcile';first,plan=f.repo.prepare_reconciliation(TENANT,receipt['id'],key,'reconcile',f.actor)
    failed=f.repo.complete_receipt(TENANT,first,plan,[None],key,f.actor,'transport_failure','receipt.reconcile')
    assert failed['status']=='needs_reconciliation'
    attempts=failed['reconciliation_attempts']
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        f.repo.prepare_reconciliation(TENANT,receipt['id'],key,'reconcile','other-actor')
    assert f.repo.get_receipt(TENANT,receipt['id'])['reconciliation_attempts']==attempts
    current,pending=f.repo.prepare_reconciliation(TENANT,receipt['id'],key,'reconcile',f.actor)
    assert len(pending)==1 and pending[0]['receipt_line_id']==plan[0]['receipt_line_id']
    completed=f.repo.complete_receipt(TENANT,current,pending,[{'id':None}],key,f.actor,operation='receipt.reconcile')
    assert completed['status']=='completed'
    replay,no_plan=f.repo.prepare_reconciliation(TENANT,receipt['id'],key,'reconcile',f.actor)
    import json
    assert replay==json.loads(json.dumps(completed,default=lambda item:item.isoformat() if isinstance(item,datetime) else str(item))) and no_plan is None

def test_snapshot_freezes_same_supplier_refreshes_explicit_change_and_issue(pg):
    f=pg;order=create_order(f)
    assert order['currency']=='USD' and order['organization_context']==f.context
    assert order['commercial_terms_snapshot']['terms_revision']==1
    f.c.execute(text("update purchasing.supplier_division_terms set currency='CAD',revision=2 where tenant_id=:t and supplier_id=:s"),{'t':TENANT,'s':f.suppliers[0]['id']})
    updated=f.repo.update_order(TENANT,order['id'],f.payload,f.suffix+'-edit','edit',f.actor,organization_access=f.scope)
    assert updated['currency']=='USD' and updated['commercial_terms_snapshot']==order['commercial_terms_snapshot']
    changed=f.payload.model_copy(update={'supplier_id':f.suppliers[1]['id']})
    updated=f.repo.update_order(TENANT,order['id'],changed,f.suffix+'-change','change',f.actor,organization_access=f.scope)
    assert updated['currency']=='EUR' and updated['commercial_terms_snapshot']['supplier_id']==f.suppliers[1]['id']
    issued=f.repo.issue_order(TENANT,order['id'],f.suffix+'-issue','issue',f.actor,organization_access=f.scope)
    assert issued['commercial_terms_snapshot']==updated['commercial_terms_snapshot']

def test_api_replay_preserves_old_terms_and_revoked_scope_denies(pg):
    f=pg;authorized=api.AuthorizedContext(TENANT,f.actor,'purchasing.order.create')
    payload=f.payload.model_copy(update={'currency':'USD','payment_terms':'cash','expected_terms_revision':1})
    first=api.create_order(payload,TENANT,None,f.suffix+'-api',f.repo,f.authority,authorized).data
    f.c.execute(text("update purchasing.supplier_division_terms set currency='CAD',revision=2 where tenant_id=:t and supplier_id=:s"),{'t':TENANT,'s':f.suppliers[0]['id']})
    calls=len(f.calls)
    replay=api.create_order(payload,TENANT,None,f.suffix+'-api',f.repo,f.authority,authorized).data
    assert replay['id']==first['id'] and replay['currency']=='USD' and len(f.calls)==calls
    other=api.AuthorizedContext(TENANT,'other-'+f.actor,'purchasing.order.create')
    f.authority.organization_access=lambda *args:replace(f.scope,actor_id=other.actor_id)
    with pytest.raises(ErclaveError) as exc:api.create_order(payload,TENANT,None,f.suffix+'-api',f.repo,f.authority,other)
    assert exc.value.code=='idempotency_key_reused' and len(f.calls)==calls
    f.authority.organization_access=lambda *args:replace(f.scope,divisions=())
    with pytest.raises(ErclaveError) as exc:api.create_order(payload,TENANT,None,f.suffix+'-api',f.repo,f.authority,authorized)
    assert exc.value.code=='assignment_division_denied' and len(f.calls)==calls

def test_reviewed_terms_revision_conflict_before_creation_and_zero_lead_preserved(pg):
    f=pg;authorized=api.AuthorizedContext(TENANT,f.actor,'purchasing.order.create')
    payload=f.payload.model_copy(update={'expected_terms_revision':1})
    f.c.execute(text("update purchasing.supplier_division_terms set revision=2,lead_time_days=0 where tenant_id=:t and supplier_id=:s"),{'t':TENANT,'s':f.suppliers[0]['id']})
    with pytest.raises(ErclaveError) as exc:api.create_order(payload,TENANT,None,f.suffix+'-stale',f.repo,f.authority,authorized)
    assert exc.value.code=='purchasing_document_terms_changed' and exc.value.details['field']=='supplier_id'
    assert f.c.execute(text('select count(*) from purchasing.purchase_orders where tenant_id=:t and code=:code'),{'t':TENANT,'code':payload.code}).scalar()==0
    assert not f.calls
    current=payload.model_copy(update={'expected_terms_revision':2})
    order=api.create_order(current,TENANT,None,f.suffix+'-fresh',f.repo,f.authority,authorized).data
    assert order['commercial_terms_snapshot']['values']['lead_time_days']==0
    f.c.execute(text("update purchasing.supplier_division_terms set revision=3,lead_time_days=10 where tenant_id=:t and supplier_id=:s"),{'t':TENANT,'s':f.suppliers[0]['id']})
    updated=f.repo.update_order(TENANT,order['id'],current,f.suffix+'-edit-frozen','edit',f.actor,organization_access=f.scope)
    assert updated['commercial_terms_snapshot']==order['commercial_terms_snapshot']
    with pytest.raises(ErclaveError) as exc:
        f.repo.update_order(TENANT,order['id'],current.model_copy(update={'supplier_id':f.suppliers[1]['id']}),f.suffix+'-other-stale','other',f.actor,organization_access=f.scope)
    assert exc.value.code=='purchasing_document_terms_changed'

def test_requisition_inheritance_immutable_origin_and_division(pg):
    f=pg;p=schemas.RequisitionWrite(code='REQ-'+f.suffix,division_ref_id=f.context['division_ref_id'],required_date=date.today(),lines=[f.line])
    req=f.repo.create_requisition(TENANT,p,f.suffix+'-req','req',f.actor,context=f.context,organization_access=f.scope)
    f.repo.transition_requisition(TENANT,req['id'],'submitted',None,f.suffix+'-submit','submit',f.actor,organization_access=f.scope)
    f.repo.transition_requisition(TENANT,req['id'],'approved',None,f.suffix+'-approve','approve',f.actor,organization_access=f.scope)
    order=create_order(f,f.payload.model_copy(update={'requisition_id':req['id'],'direct_purchase_reason':None,'division_ref_id':None}))
    assert order['organization_context']==req['organization_context']
    with pytest.raises(ValueError,match='order_origin_locked'):
        f.repo.update_order(TENANT,order['id'],f.payload,f.suffix+'-origin','origin',f.actor,organization_access=f.scope)
    with pytest.raises(ErclaveError) as exc:
        f.repo.update_order(TENANT,order['id'],f.payload.model_copy(update={'division_ref_id':'foreign'}),f.suffix+'-division','division',f.actor,organization_access=f.scope)
    assert exc.value.code=='purchasing_document_context_locked'

def test_services_inherit_frozen_currency_scope_queues_replay_and_csv(pg):
    f=pg;order=create_order(f);f.repo.issue_order(TENANT,order['id'],f.suffix+'-issue','issue',f.actor,organization_access=f.scope)
    payload=schemas.ReceiptWrite(code='R-'+f.suffix,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),lines=[{'order_line_id':order['lines'][0]['id'],'quantity':'1'}])
    # Current Society monetary settings changed: the order snapshot is inherited.
    f.authority.organization_access=lambda *args:replace(f.scope,societies=({'id':f.context['society_ref_id'],'base_currency':'CAD'},))
    assert rc.ReceiptContext(f.repo,f.authority).prepare(TENANT,payload,None,f.actor)=={}
    receipt,_=f.repo.prepare_receipt(TENANT,payload,f.suffix+'-receipt','receipt',f.actor,{},organization_access=f.scope)
    assert receipt['organization_context']==f.context
    assert receipt['id'] in [r['id'] for r in f.repo.list_pending_receipts(TENANT,'service',f.actor,allowed_divisions=[f.context['division_ref_id']])]
    assert not f.repo.list_pending_receipts(TENANT,'service',f.actor,allowed_divisions=[])
    assert not f.repo.list_orders(TENANT,allowed_divisions=[])
    assert not f.repo.list_receipts(TENANT,allowed_divisions=[])
    for report in ('requisitions','orders','receipts'):
        assert reports.build_report(f.repo,TENANT,report,{'allowed_divisions':[]}).rows==[]
    f.authority.organization_access=lambda *args:replace(f.scope,divisions=())
    with pytest.raises(ErclaveError):rc.authorize_receipt(f.repo,f.authority,TENANT,receipt,'purchasing.receipt.create',None,f.actor)
    with pytest.raises(ErclaveError):f.repo.prepare_receipt(TENANT,payload,f.suffix+'-receipt','receipt',f.actor,organization_access=replace(f.scope,divisions=()))

def test_legacy_requires_fullscope_read_cancel_and_blocks_new_work(pg):
    f=pg;legacy=f.payload.model_copy(update={'currency':'USD','payment_terms':'cash'})
    order=f.repo.create_order(TENANT,legacy,f.suffix+'-legacy','legacy',f.actor)
    assert order['organization_context'] is None
    assert order['id'] not in [r['id'] for r in f.repo.list_orders(TENANT,allowed_divisions=[f.context['division_ref_id']])]
    with pytest.raises(ErclaveError):f.repo.cancel_order(TENANT,order['id'],'Test cancel',f.suffix+'-denied','denied',f.actor,organization_access=f.scope)
    full=replace(f.scope,all_divisions=True)
    with pytest.raises(ErclaveError) as exc:f.repo.update_order(TENANT,order['id'],legacy,f.suffix+'-edit','edit',f.actor,organization_access=full)
    assert exc.value.code=='purchasing_document_history_review_required'
    assert f.repo.cancel_order(TENANT,order['id'],'Test cancel',f.suffix+'-cancel','cancel',f.actor,organization_access=full)['status']=='cancelled'

def test_supplier_lookup_bounded_missing_terms_and_stale_society(pg):
    f=pg
    f.c.execute(text('delete from purchasing.supplier_division_terms where tenant_id=:t and supplier_id=:s'),{'t':TENANT,'s':f.suppliers[1]['id']})
    page=orgapi.document_suppliers(f.context['division_ref_id'],'',1,1,f.scope,f.repo)
    assert page['meta']=={'total':2,'limit':1,'offset':1}
    assert page['data'][0]['commercial_terms']=={'values':None,'revision':0,'requires_confirmation':True}
    with pytest.raises(ErclaveError) as exc:create_order(f,f.payload.model_copy(update={'supplier_id':f.suppliers[1]['id']}))
    assert exc.value.code=='purchasing_document_terms_required'

def test_physical_receipt_uses_order_currency_snapshot_and_current_assignment(pg):
    f=pg;line=f.line.model_copy(update={'line_type':'inventory_item','inventory_item_id':'item-'+f.suffix,'unit_code':'H87'})
    order=create_order(f,f.payload.model_copy(update={'lines':[line]}))
    f.repo.issue_order(TENANT,order['id'],f.suffix+'-issue','issue',f.actor,organization_access=f.scope)
    p=schemas.ReceiptWrite(code='R-'+f.suffix,purchase_order_id=order['id'],received_at=datetime.now(timezone.utc),cost_exchange_rate='20.123456',lines=[{'order_line_id':order['lines'][0]['id'],'quantity':'1','warehouse_id':'warehouse-test'}])
    f.authority.organization_access=lambda *args:replace(f.scope,societies=({'id':f.context['society_ref_id'],'base_currency':'CAD'},))
    f.authority.warehouse=lambda *args:{'status':'active','division_ref_id':f.context['division_ref_id']}
    snapshots=rc.ReceiptContext(f.repo,f.authority).prepare(TENANT,p,None,f.actor)
    receipt,_=f.repo.prepare_receipt(TENANT,p,f.suffix+'-receipt','receipt',f.actor,snapshots,organization_access=f.scope)
    snapshot=receipt['lines'][0]['inventory_context_snapshot']
    assert snapshot['organization_context']['cost_currency']=='MXN'
    assert snapshot['original_currency']=='USD' and snapshot['original_unit_cost']=='4.12' and snapshot['unit_cost']=='82.908639'
    proof=rc.receipt_proof(f.repo,f.authority,TENANT,receipt['id'],receipt['lines'][0]['id'],None,f.actor)
    assert proof['unit_cost']==snapshot['unit_cost'] and proof['receipt_line_id']==receipt['lines'][0]['id']
    # A new draft may not issue after supplier assignment is revoked.
    draft=create_order(f,f.payload.model_copy(update={'code':'PO2-'+f.suffix}),key='second')
    f.c.execute(text("update purchasing.supplier_division_assignments set status='inactive' where tenant_id=:t and supplier_id=:s"),{'t':TENANT,'s':f.suppliers[0]['id']})
    with pytest.raises(ErclaveError) as exc:f.repo.issue_order(TENANT,draft['id'],f.suffix+'-revoked','revoked',f.actor,organization_access=f.scope)
    assert exc.value.code=='operational_context_resource_unavailable'
    assert f.repo.get_order(TENANT,draft['id'])['status']=='draft'

def test_item_selection_requires_explicit_active_assignment_and_scope_society(pg):
    f=pg;line=f.line.model_copy(update={'line_type':'inventory_item','inventory_item_id':'item-test'})
    f.authority.item_assignments=lambda *args:[]
    with pytest.raises(ErclaveError) as exc:dc.validate_document_items(TENANT,[line],f.context,f.authority,None)
    assert exc.value.code=='operational_context_resource_unavailable' and exc.value.details['field']=='lines.0.inventory_item_id'
    f.authority.item_assignments=lambda *args:[{'item_id':'item-test','division_ref_id':f.context['division_ref_id'],'status':'active'}]
    dc.validate_document_items(TENANT,[line],f.context,f.authority,None)
    moved=replace(f.scope,divisions=({**f.scope.divisions[0],'society_id':'another-society'},))
    with pytest.raises(ErclaveError) as exc:dc.authorize_document({'organization_context':f.context},moved)
    assert exc.value.code=='operational_context_mismatch'

def test_cc15_downgrade_blocks_history_before_schema_drop(pg,monkeypatch):
    from sqlalchemy.exc import DBAPIError
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    f=pg;create_order(f)
    path=Path(__file__).resolve().parents[3]/'alembic/versions/20261012_0058_purchasing_documents.py'
    spec=importlib.util.spec_from_file_location('cc15_history_proof',path);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    operations=Operations(MigrationContext.configure(f.c));monkeypatch.setattr(migration,'op',operations)
    for method in ('drop_index','drop_column','drop_constraint'):monkeypatch.setattr(operations,method,lambda *args,**kwargs:pytest.fail('history must block before drop'))
    with pytest.raises(DBAPIError,match='CC15 history exists'):
        with f.c.begin_nested():
            f.c.execute(text("set local lock_timeout='2s'"));migration.downgrade()
    assert f.c.execute(text("select 1 from information_schema.columns where table_schema='purchasing' and table_name='purchase_orders' and column_name='commercial_terms_snapshot'")).scalar()==1
