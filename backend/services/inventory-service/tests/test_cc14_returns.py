"""Return cost/context conservation and recovery without external dependencies."""
import importlib
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from erclave_common.errors import ErclaveError
from erclave_common.operational_context import OperationalContext

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
for name in list(sys.modules):
    if name=='app' or name.startswith('app.'):
        del sys.modules[name]
returns=importlib.import_module('app.material_returns')
schemas=importlib.import_module('app.schemas')
inventory_api=importlib.import_module('app.api')
TENANT='ten_739ee59d765d5e14818674800d'
CONTEXT=OperationalContext(division_ref_id='division',society_ref_id='society',division_code='D',division_name='Division',cost_currency='MXN')


def material_return(**changes):
    value=dict(id='return',original_movement_id='out',source_type='maintenance_order',source_id='order',source_code='OT',reservation_id='reservation',quantity=Decimal('1.123456'),reason='Synthetic return',status='pending',requested_by='actor',created_at=datetime.now(timezone.utc),inventory_item_id='item',item_code='IT',item_name='Item',warehouse_id='warehouse',warehouse_name='Warehouse',unit='PZA',unit_cost=Decimal('123456789012.123456'),organization_context=CONTEXT)
    value.update(changes)
    return schemas.MaterialReturnRead(**value)


class Connection:
    def __init__(self):self.calls=[]
    def execute(self,sql,params):
        self.calls.append((str(sql),params))
        return SimpleNamespace(first=lambda:None,scalars=lambda:SimpleNamespace(all=lambda:[]))


class Engine:
    def __init__(self):self.connection=Connection()
    @contextmanager
    def begin(self):yield self.connection
    @contextmanager
    def connect(self):yield self.connection


class Repository(returns.InventoryMaterialReturns):
    def __init__(self,value):self.value=value;self.engine=Engine();self.inserted=[]
    def _material_return(self,*args):return self.value
    def _warehouse(self,*args):return SimpleNamespace(status='active')
    def _resource_lock(self,*args):pass
    def _insert_movement(self,*args,**kwargs):self.inserted.append((args,kwargs))
    def _audit(self,*args):pass


@pytest.fixture
def validations(monkeypatch):
    calls=[]
    monkeypatch.setattr(returns,'validate_local_context',lambda c,t,p,ctx:calls.append(('context',t,ctx)))
    monkeypatch.setattr(returns,'validate_cost_currency',lambda c,t,i,w,ctx:calls.append(('currency',t,ctx)))
    return calls


def test_receipt_uses_original_cost_context_and_quantity(validations):
    repo=Repository(material_return())
    repo.receive_material_return(TENANT,'return','actor')
    args,kwargs=repo.inserted[0]
    assert kwargs['organization_context']==CONTEXT
    assert kwargs['unit_cost']==Decimal('123456789012.123456')
    assert args[4].quantity==Decimal('1.123456') and isinstance(args[4].quantity,Decimal)
    assert validations==[('context',TENANT,CONTEXT),('currency',TENANT,CONTEXT)]


@pytest.mark.parametrize('status',['received_pending_reconciliation','completed'])
def test_reconciliation_retry_never_inserts_another_receipt(status,validations):
    repo=Repository(material_return(status=status))
    assert repo.receive_material_return(TENANT,'return','actor').status==status
    assert repo.inserted==[] and validations==[]


@pytest.mark.parametrize('changes',[{'unit_cost':None},{'organization_context':CONTEXT.model_copy(update={'cost_currency':None})}])
def test_scoped_return_never_invents_currency_or_zero_cost(changes,validations):
    repo=Repository(material_return(**changes))
    with pytest.raises(ValueError,match='operational_cost_currency_unavailable'):
        repo.receive_material_return(TENANT,'return','actor')
    assert repo.inserted==[]


def test_legacy_return_does_not_adopt_current_warehouse_dimension(monkeypatch,validations):
    repo=Repository(material_return(organization_context=None))
    def reject(c,t,p,ctx):
        assert ctx is None
        raise ErclaveError('operational_context_required','Legacy source',409)
    monkeypatch.setattr(returns,'validate_local_context',reject)
    with pytest.raises(ErclaveError) as exc:repo.receive_material_return(TENANT,'return','actor')
    assert exc.value.code=='operational_context_required' and repo.inserted==[]


def test_currency_history_failure_keeps_return_pending(monkeypatch,validations):
    repo=Repository(material_return())
    def reject(*args):raise ErclaveError('operational_cost_history_review_required','History',409)
    monkeypatch.setattr(returns,'validate_cost_currency',reject)
    with pytest.raises(ErclaveError):repo.receive_material_return(TENANT,'return','actor')
    assert repo.inserted==[]
    assert not any('update inventory.material_returns' in sql for sql,_ in repo.engine.connection.calls)


@pytest.mark.parametrize('divisions',[[],['division']])
def test_return_scope_filters_original_snapshot_before_pagination(divisions):
    repo=Repository(material_return())
    assert repo.list_material_returns(TENANT,10,20,allowed_divisions=divisions)==[]
    sql,params=repo.engine.connection.calls[0]
    assert "m.organization_context->>'division_ref_id'" in sql
    assert sql.index('=any(:divisions)')<sql.index('limit :limit')
    assert params=={'t':TENANT,'limit':10,'offset':20,'divisions':divisions}


def test_api_return_request_revoked_scope_blocks_idempotent_replay():
    from erclave_common.organization_client import OrganizationAccess
    class Client:
        def access(self,*args):return OrganizationAccess(TENANT,'actor',('inventory.movement.create',),(),False,False)
    class GuardedRepository:
        def return_source(self,*args):return {'source_type':'maintenance_order','organization_context':CONTEXT.model_dump()}
        def replay_material_return_request(self,*args):raise AssertionError('Revoked scope reached replay')
    with pytest.raises(ErclaveError) as exc:
        inventory_api.request_material_return(schemas.MaterialReturnRequest(original_movement_id='out',quantity=1,reason='Synthetic'),x_tenant_id=TENANT,authorization=None,idempotency_key='same-key',repository=GuardedRepository(),authority=None,access=inventory_api.AuthorizedContext(TENANT,'actor','inventory.movement.create'),context_client=Client())
    assert exc.value.status_code==403


@pytest.mark.parametrize('status',['pending','received_pending_reconciliation','completed'])
@pytest.mark.parametrize('action',['receive','cancel'])
def test_api_return_scope_is_checked_before_receive_or_reconciliation(status,action):
    from erclave_common.organization_client import OrganizationAccess
    class Client:
        def access(self,*args):return OrganizationAccess(TENANT,'actor',('inventory.movement.create',),(),False,False)
    class GuardedRepository:
        @contextmanager
        def return_command_lock(self,*args):yield
        def get_material_return(self,*args):return material_return(status=status)
        def begin_material_return_command(self,*args):raise AssertionError('Revoked scope reached durable intent/replay')
        def receive_material_return(self,*args):raise AssertionError('Revoked scope reached receipt')
    with pytest.raises(ErclaveError) as exc:
        options=dict(x_tenant_id=TENANT,idempotency_key='same-key',repository=GuardedRepository(),access=inventory_api.AuthorizedContext(TENANT,'actor','inventory.movement.create'),context_client=Client())
        if action=='receive':inventory_api.receive_material_return('return',authorization=None,authority=None,**options)
        else:inventory_api.cancel_material_return('return',schemas.ReverseRequest(reason='Synthetic cancellation'),**options)
    assert exc.value.status_code==403


# Both test modules share the same guarded, rollback-only Inventory fixture.
from test_cc14_handoffs import local_cc14_inventory


@pytest.mark.parametrize('source_type',['production_order','maintenance_order'])
def test_db_return_preserves_issued_context_cost_and_recovery(local_cc14_inventory,source_type):
    from sqlalchemy import text
    repo,c,item,warehouse,_,context,other,suffix=local_cc14_inventory
    repo.create_movement(TENANT,schemas.MovementCreate(movement_type='entry',inventory_item_id=item,warehouse_id=warehouse,quantity=10,unit='PZA',unit_cost=Decimal('12.123456'),reason='Synthetic opening',source=schemas.SourceRef(type='manual',id=suffix),occurred_at=datetime.now(timezone.utc)),'entry-'+suffix,'entry','actor',organization_context=context)
    reservation=repo.create_reservation(TENANT,schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=warehouse,quantity=4,unit='PZA',source=schemas.SourceRef(type=source_type,id='order-'+suffix,line_id='line-'+suffix)),'reserve-'+suffix,'reserve','actor',organization_context=context)
    outgoing=repo.consume_reservation(TENANT,reservation.id,'Synthetic issue','issue-'+suffix,'issue','actor',allowed_sources={source_type})
    source=repo.return_source(TENANT,outgoing.id)
    assert source['organization_context']==context.model_dump()
    payload=schemas.MaterialReturnRequest(original_movement_id=outgoing.id,quantity=Decimal('1.123456'),reason='Synthetic unused material')
    requested=repo.request_material_return(TENANT,payload,source,'ORDER-'+suffix,'request-'+suffix,'request','actor')
    assert requested.organization_context==context
    assert repo.list_material_returns(TENANT,allowed_divisions=[other.division_ref_id])==[]
    assert any(r.id==requested.id for r in repo.list_material_returns(TENANT,allowed_divisions=[context.division_ref_id]))
    received=repo.receive_material_return(TENANT,requested.id,'actor')
    assert received.status=='received_pending_reconciliation'
    repo.finish_material_return(TENANT,requested.id,'actor','material_return_dependency_unavailable')
    assert repo.receive_material_return(TENANT,requested.id,'actor').movement_id==received.movement_id
    completed=repo.finish_material_return(TENANT,requested.id,'actor')
    assert completed.status=='completed'
    assert repo.replay_material_return_request(TENANT,'request-'+suffix,'request','actor').status=='completed'
    row=c.execute(text("select quantity,unit_cost,organization_context from inventory.movements where tenant_id=:t and source_type='material_return' and source_id=:id"),{'t':TENANT,'id':requested.id}).mappings().one()
    assert row['quantity']==Decimal('1.123456') and row['unit_cost']==Decimal('12.123456')
    assert row['organization_context']==context.model_dump()
    assert repo.get_material_return('unrelated-read-only-tenant',requested.id) is None
    with pytest.raises(ValueError,match='material_return_quantity_exceeded'):
        repo.request_material_return(TENANT,payload.model_copy(update={'quantity':Decimal(3)}),source,'ORDER-'+suffix,'excess-'+suffix,'excess','actor')


def test_db_legacy_return_cannot_adopt_later_warehouse_dimension(local_cc14_inventory):
    from sqlalchemy import text
    repo,c,item,warehouse,_,context,_,suffix=local_cc14_inventory
    c.execute(text('update inventory.warehouses set division_ref_id=null,division_revision=0 where tenant_id=:t and id=:id'),{'t':TENANT,'id':warehouse})
    repo.create_movement(TENANT,schemas.MovementCreate(movement_type='entry',inventory_item_id=item,warehouse_id=warehouse,quantity=10,unit='PZA',unit_cost=Decimal('12.123456'),reason='Synthetic opening',source=schemas.SourceRef(type='manual',id=suffix),occurred_at=datetime.now(timezone.utc)),'entry-'+suffix,'entry','actor')
    reserved=repo.create_reservation(TENANT,schemas.ReservationCreateRequest(inventory_item_id=item,warehouse_id=warehouse,quantity=4,unit='PZA',source=schemas.SourceRef(type='maintenance_order',id='order-'+suffix,line_id='line-'+suffix)),'reserve-'+suffix,'reserve','actor')
    outgoing=repo.consume_reservation(TENANT,reserved.id,'Synthetic issue','issue-'+suffix,'issue','actor',allowed_sources={'maintenance_order'})
    requested=repo.request_material_return(TENANT,schemas.MaterialReturnRequest(original_movement_id=outgoing.id,quantity=1,reason='Synthetic unused material'),repo.return_source(TENANT,outgoing.id),'ORDER-'+suffix,'request-'+suffix,'request','actor')
    c.execute(text('update inventory.warehouses set division_ref_id=:d,division_revision=1 where tenant_id=:t and id=:id'),{'t':TENANT,'id':warehouse,'d':context.division_ref_id})
    with pytest.raises(ErclaveError) as exc:repo.receive_material_return(TENANT,requested.id,'actor')
    assert exc.value.code=='operational_context_required'
    assert repo.get_material_return(TENANT,requested.id).organization_context is None
    assert repo.get_material_return(TENANT,requested.id).status=='pending'
