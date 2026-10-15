"""CC-14 domain checks use no DB, network, credentials or external fixtures."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == 'app' or name.startswith('app.'):
        del sys.modules[name]
handoffs = importlib.import_module('app.handoffs')
schemas = importlib.import_module('app.schemas')
inventory_api = importlib.import_module('app.api')
TENANT = 'ten_739ee59d765d5e14818674800d'
ORIGIN = OperationalContext(division_ref_id='origin', society_ref_id='society', division_code='O', division_name='Origin', cost_currency='MXN')
DESTINATION = ORIGIN.model_copy(update={'division_ref_id': 'destination', 'division_code': 'D', 'division_name': 'Destination'})


def transfer(**changes):
    value = dict(id='transfer', status='in_transit', outgoing_movement_id='out', code='TR-1', inventory_item_id='item', item_code='IT', item_name='Item', origin_warehouse_id='origin-wh', destination_warehouse_id='destination-wh', origin_name='Origin', destination_name='Destination', quantity=Decimal('3'), received_quantity=Decimal(0), returned_quantity=Decimal(0), unit='PZA', unit_cost=Decimal('123456789012.123456'), created_at=datetime.now(timezone.utc), organization_context=ORIGIN, destination_context=DESTINATION)
    value.update(changes)
    return schemas.TransferRead(**value)


class Connection:
    def __init__(self): self.calls = []
    def execute(self, sql, params):
        self.calls.append((str(sql), params))
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))


class Engine:
    def __init__(self): self.connection = Connection()
    @contextmanager
    def begin(self): yield self.connection
    @contextmanager
    def connect(self): yield self.connection


class Repository(handoffs.InventoryHandoffs):
    def __init__(self, value): self.value=value; self.engine=Engine(); self.inserted=[]; self.replay=None
    def _claim(self, *args): return self.replay
    def _transfer(self, *args): return self.value
    def _warehouse(self, *args): return SimpleNamespace(status='active')
    def _resource_lock(self, *args): pass
    def _insert_movement(self, *args, **kwargs): self.inserted.append((args, kwargs))
    def _audit(self, *args): pass
    def _done(self, *args): self.replay=args[-1].model_dump(mode='json')


@pytest.fixture
def validations(monkeypatch):
    calls=[]
    monkeypatch.setattr(handoffs, 'validate_local_context', lambda c,t,p,ctx: calls.append(('context',t,p.warehouse_id,ctx)))
    monkeypatch.setattr(handoffs, 'validate_cost_currency', lambda c,t,i,w,ctx: calls.append(('currency',t,w,ctx)))
    return calls


@pytest.mark.parametrize('action,status,warehouse,context', [('receive','in_transit','destination-wh',DESTINATION), ('receive-return','return_requested','origin-wh',ORIGIN)])
def test_receipt_keeps_frozen_side_and_exact_cost_quantity(action,status,warehouse,context,validations):
    repo=Repository(transfer(status=status))
    payload=schemas.TransferActionRequest(warehouse_id=warehouse,quantity=Decimal('1.123456'),reason='Synthetic receipt')
    repo.transition_transfer(TENANT,'transfer',action,payload,'key','digest','actor')
    args,kwargs=repo.inserted[0]
    assert args[4].quantity==Decimal('1.123456') and isinstance(args[4].quantity,Decimal)
    assert kwargs['unit_cost']==Decimal('123456789012.123456')
    assert kwargs['organization_context']==context
    assert validations==[('context',TENANT,warehouse,context),('currency',TENANT,warehouse,context)]
    repo.transition_transfer(TENANT,'transfer',action,payload,'key','digest','actor')
    assert len(repo.inserted)==1


@pytest.mark.parametrize('changes,code', [({'destination_context':None},'operational_context_mismatch'), ({'destination_context':DESTINATION.model_copy(update={'society_ref_id':'foreign'})},'operational_context_mismatch'), ({'destination_context':DESTINATION.model_copy(update={'cost_currency':'USD'})},'operational_cost_currency_unavailable'), ({'unit_cost':None},'operational_cost_currency_unavailable')])
def test_transfer_rejects_cross_society_missing_context_or_cost(changes,code,validations):
    repo=Repository(transfer(**changes))
    with pytest.raises(ValueError,match=code):
        repo.transition_transfer(TENANT,'transfer','receive',schemas.TransferActionRequest(warehouse_id='destination-wh',quantity=1,reason='Synthetic'),'key','digest','actor')
    assert repo.inserted==[]


def test_incompatible_destination_cost_history_cannot_receive(monkeypatch,validations):
    repo=Repository(transfer())
    def reject(*args): raise ErclaveError('operational_cost_history_review_required','Synthetic history',409)
    monkeypatch.setattr(handoffs,'validate_cost_currency',reject)
    with pytest.raises(ErclaveError):
        repo.transition_transfer(TENANT,'transfer','receive',schemas.TransferActionRequest(warehouse_id='destination-wh',quantity=1,reason='Synthetic'),'key','digest','actor')
    assert repo.inserted==[]


@pytest.mark.parametrize('divisions', [[], ['origin'], ['origin','destination']])
def test_transfer_scope_filters_both_sides_before_pagination(divisions):
    repo=Repository(transfer())
    assert repo.list_transfers(TENANT,10,20,allowed_divisions=divisions)==[]
    sql,params=repo.engine.connection.calls[0]
    assert sql.count('=any(:divisions)')==2
    assert sql.index('=any(:divisions)')<sql.index('limit :limit')
    assert params=={'t':TENANT,'limit':10,'offset':20,'divisions':divisions}


def test_legacy_transfer_keeps_null_context_without_currency_invention(validations):
    repo=Repository(transfer(organization_context=None,destination_context=None,unit_cost=None))
    repo.transition_transfer(TENANT,'transfer','receive',schemas.TransferActionRequest(warehouse_id='destination-wh',quantity=1,reason='Synthetic'),'key','digest','actor')
    assert repo.inserted[0][1]['organization_context'] is None


@pytest.mark.parametrize('allowed',[[],['origin'],['destination']])
def test_api_transfer_requires_both_scopes_before_command_or_replay(allowed):
    from erclave_common.organization_client import OrganizationAccess
    rows=tuple({'id':d,'code':d,'name':d,'society_id':'society'} for d in allowed)
    scope=OrganizationAccess(TENANT,'actor',('inventory.movement.create',),rows,False,False)
    class Client:
        def access(self,*args):return scope
    class GuardedRepository:
        def get_transfer(self,*args):return transfer()
        def transition_transfer(self,*args):raise AssertionError('Unauthorized transfer reached command/replay')
    with pytest.raises(ErclaveError) as exc:
        inventory_api.transfer_action('transfer','receive',schemas.TransferActionRequest(warehouse_id='destination-wh',quantity=1,reason='Synthetic'),x_tenant_id=TENANT,idempotency_key='same-key',repository=GuardedRepository(),access=inventory_api.AuthorizedContext(TENANT,'actor','inventory.movement.create'),authorization=None,context_client=Client())
    assert exc.value.status_code==403


@pytest.fixture
def local_cc14_inventory():
    import os
    from uuid import uuid4
    from sqlalchemy import create_engine,text
    from sqlalchemy.engine import make_url
    from sqlalchemy.pool import NullPool
    configured=os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not configured:pytest.skip('Local PostgreSQL URL not configured')
    parsed=make_url(configured)
    assert parsed.host in ('127.0.0.1','localhost','::1') and parsed.port==5434 and parsed.database=='erclave_local' and not parsed.query
    # Import through this module's package generation, shared with its schemas.
    repo_type=importlib.import_module(handoffs.__package__+'.repositories').InventoryRepository
    engine=create_engine(parsed,poolclass=NullPool)
    with engine.connect() as connection:
        outer=connection.begin()
        class TransactionEngine:
            @contextmanager
            def begin(self):
                with connection.begin_nested():yield connection
            @contextmanager
            def connect(self):yield connection
        try:
            assert connection.execute(text('select id from admin.tenants where id=:t'),{'t':TENANT}).scalar()==TENANT
            suffix=uuid4().hex[:18];item='cc14_it_'+suffix;origin='cc14_oa_'+suffix;destination='cc14_db_'+suffix
            first=ORIGIN.model_copy(update={'division_ref_id':'cc14_da_'+suffix})
            second=DESTINATION.model_copy(update={'division_ref_id':'cc14_dd_'+suffix})
            connection.execute(text("insert into inventory.items(id,tenant_id,code,name,type,base_unit,use_in_recipe) values(:id,:t,:id,'CC14 synthetic item','rawMaterial','PZA',true)"),{'id':item,'t':TENANT})
            for warehouse,context in ((origin,first),(destination,second)):
                connection.execute(text("insert into inventory.warehouses(id,tenant_id,code,name,type,business_center,location,owner,division_ref_id,division_revision) values(:id,:t,:id,'CC14 synthetic warehouse','general','Synthetic','Synthetic','Synthetic',:d,1)"),{'id':warehouse,'t':TENANT,'d':context.division_ref_id})
                connection.execute(text("insert into inventory.item_division_assignments(tenant_id,item_id,division_ref_id,status,revision) values(:t,:id,:d,'active',1)"),{'t':TENANT,'id':item,'d':context.division_ref_id})
            yield repo_type(TransactionEngine()),connection,item,origin,destination,first,second,suffix
        finally:outer.rollback()
    engine.dispose()


def test_db_transfer_partial_receipt_and_return_keep_two_snapshots(local_cc14_inventory):
    from sqlalchemy import text
    repo,c,item,origin,destination,first,second,suffix=local_cc14_inventory
    common=dict(inventory_item_id=item,warehouse_id=origin,unit='PZA',reason='Synthetic CC14',source=schemas.SourceRef(type='manual',id=suffix),occurred_at=datetime.now(timezone.utc))
    repo.create_movement(TENANT,schemas.MovementCreate(**common,movement_type='entry',quantity=10,unit_cost=Decimal('12.123456')),'entry-'+suffix,'entry','actor',organization_context=first)
    movement=repo.create_movement(TENANT,schemas.MovementCreate(**common,movement_type='transfer',destination_warehouse_id=destination,quantity=3),'transfer-'+suffix,'transfer','actor',organization_context=first,destination_context=second)
    transfer_id=movement.transfer_group_id
    assert repo.list_transfers(TENANT,allowed_divisions=[first.division_ref_id])==[]
    assert any(row.id==transfer_id for row in repo.list_transfers(TENANT,allowed_divisions=[first.division_ref_id,second.division_ref_id]))
    payload=schemas.TransferActionRequest(warehouse_id=destination,quantity=1,reason='Synthetic receive')
    received=repo.transition_transfer(TENANT,transfer_id,'receive',payload,'receive-'+suffix,'receive','actor')
    assert received.status=='partially_received'
    assert repo.transition_transfer(TENANT,transfer_id,'receive',payload,'receive-'+suffix,'receive','actor').received_quantity==1
    repo.transition_transfer(TENANT,transfer_id,'request-return',payload.model_copy(update={'quantity':None}),'return-'+suffix,'return','actor')
    returned=repo.transition_transfer(TENANT,transfer_id,'receive-return',payload.model_copy(update={'warehouse_id':origin,'quantity':Decimal(2)}),'back-'+suffix,'back','actor')
    assert returned.status=='returned' and returned.returned_quantity==2
    rows=c.execute(text("select warehouse_id,organization_context,quantity,unit_cost from inventory.movements where tenant_id=:t and source_type='transfer' and source_id=:id order by warehouse_id"),{'t':TENANT,'id':transfer_id}).mappings().all()
    assert len(rows)==2
    assert {r['warehouse_id']:r['organization_context'] for r in rows}=={origin:first.model_dump(),destination:second.model_dump()}
    assert all(r['unit_cost']==Decimal('12.123456') for r in rows)
    assert repo.get_transfer('unrelated-read-only-tenant',transfer_id) is None


def test_db_transfer_rejects_revoked_destination_assignment(local_cc14_inventory):
    from sqlalchemy import text
    repo,c,item,origin,destination,first,second,suffix=local_cc14_inventory
    common=dict(inventory_item_id=item,warehouse_id=origin,unit='PZA',reason='Synthetic CC14',source=schemas.SourceRef(type='manual',id=suffix),occurred_at=datetime.now(timezone.utc))
    repo.create_movement(TENANT,schemas.MovementCreate(**common,movement_type='entry',quantity=10,unit_cost=Decimal('12.123456')),'entry-'+suffix,'entry','actor',organization_context=first)
    outgoing=repo.create_movement(TENANT,schemas.MovementCreate(**common,movement_type='transfer',destination_warehouse_id=destination,quantity=3),'transfer-'+suffix,'transfer','actor',organization_context=first,destination_context=second)
    c.execute(text("update inventory.item_division_assignments set status='inactive' where tenant_id=:t and item_id=:id and division_ref_id=:d"),{'t':TENANT,'id':item,'d':second.division_ref_id})
    with pytest.raises(ErclaveError) as exc:
        repo.transition_transfer(TENANT,outgoing.transfer_group_id,'receive',schemas.TransferActionRequest(warehouse_id=destination,quantity=1,reason='Synthetic receive'),'receive-'+suffix,'receive','actor')
    assert exc.value.code=='operational_context_resource_unavailable'
    assert repo.get_transfer(TENANT,outgoing.transfer_group_id).received_quantity==0
