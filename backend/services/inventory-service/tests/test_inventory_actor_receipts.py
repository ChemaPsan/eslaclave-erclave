"""Actor binding for durable receipts, including pre-upgrade audit recovery."""
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for module_name in list(sys.modules):
    if module_name == 'app' or module_name.startswith('app.'):
        del sys.modules[module_name]
Repository = importlib.import_module('app.repositories').InventoryRepository


class AuditConnection:
    def __init__(self, actors): self.actors = actors; self.queries = []
    def execute(self, query, parameters):
        self.queries.append((str(query), parameters))
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self.actors))


@pytest.mark.parametrize('operation', ['warehouse.create','warehouse.update','item.create','item.update','movement.create','movement.reverse','reservation.create','reservation.release','reservation.consume','finished_goods_receipt.create','transfer.receive','transfer.request-return','transfer.receive-return','material_return.request'])
def test_receipt_hash_binds_actor_for_every_command(operation):
    repo = Repository(None)
    row = {'request_hash': repo._actor_hash('payload', 'original'), 'created_at': datetime.now(timezone.utc)}
    connection = AuditConnection([])
    repo._validate_receipt(connection, 'tenant', operation, 'key', row, 'payload', 'original')
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo._validate_receipt(connection, 'tenant', operation, 'key', row, 'payload', 'other')
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo._validate_receipt(connection, 'tenant', operation, 'key', row, 'changed', 'original')
    assert connection.queries == []


@pytest.mark.parametrize('actors,actor,allowed', [(['original'],'original',True),(['original'],'other',False),([], 'original',False),(['original','other'],'original',False)])
def test_legacy_receipt_requires_unambiguous_same_transaction_audited_actor(actors, actor, allowed):
    repo = Repository(None)
    created = datetime.now(timezone.utc)
    row = {'request_hash': 'legacy', 'created_at': created}
    connection = AuditConnection(actors)
    if allowed:
        repo._validate_receipt(connection,'tenant','movement.create','key',row,'legacy',actor)
    else:
        with pytest.raises(ValueError, match='idempotency_key_reused'):
            repo._validate_receipt(connection,'tenant','movement.create','key',row,'legacy',actor)
    sql, params = connection.queries[0]
    assert 'tenant_id=:t' in sql and 'action=:o' in sql and 'created_at=:created' in sql
    assert params == {'t': 'tenant', 'o': 'movement.create', 'created': created}


from test_cc14_handoffs import local_cc14_inventory


@pytest.mark.parametrize('operation', ['warehouse.create','warehouse.update','item.create','item.update','movement.create','movement.reverse','reservation.create','reservation.release','reservation.consume','finished_goods_receipt.create','transfer.receive','transfer.request-return','transfer.receive-return','material_return.request'])
def test_postgres_durable_claim_rejects_other_actor_without_changing_receipt(local_cc14_inventory, operation):
    repo, connection, *_, suffix = local_cc14_inventory
    tenant = 'ten_739ee59d765d5e14818674800d'
    key = 'actor-bound-' + operation + suffix
    assert repo._claim(connection, tenant, operation, key, 'request', 'original') is None
    value = SimpleNamespace(model_dump=lambda **kwargs: {'id': 'own-synthetic-receipt'})
    repo._done(connection, tenant, operation, key, value)
    assert repo._claim(connection, tenant, operation, key, 'request', 'original') == {'id': 'own-synthetic-receipt'}
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo._claim(connection, tenant, operation, key, 'request', 'other')
    assert repo._claim(connection, tenant, operation, key, 'request', 'original') == {'id': 'own-synthetic-receipt'}


@pytest.mark.parametrize('action',['receive','cancel'])
def test_postgres_material_return_command_keeps_pending_retry_bound_to_actor(local_cc14_inventory,action):
    from test_cc14_returns import material_return
    repo,conn,*_,suffix=local_cc14_inventory;tenant='ten_739ee59d765d5e14818674800d';key='return-actor-'+action+suffix
    assert repo.begin_material_return_command(tenant,'own-return',action,key,'hash','original') is None
    assert repo.begin_material_return_command(tenant,'own-return',action,key,'hash','original') is None
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo.begin_material_return_command(tenant,'own-return',action,key,'hash','other')
    pending=material_return(status='received_pending_reconciliation')
    repo.finish_material_return_command(tenant,action,key,pending)
    assert repo.begin_material_return_command(tenant,'own-return',action,key,'hash','original') is None
    terminal=material_return(status='completed' if action=='receive' else 'cancelled')
    repo.finish_material_return_command(tenant,action,key,terminal)
    assert repo.begin_material_return_command(tenant,'own-return',action,key,'hash','original')==terminal
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo.begin_material_return_command(tenant,'own-return',action,key,'hash','other')
