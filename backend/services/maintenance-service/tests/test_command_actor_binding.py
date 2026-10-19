"""Actor-bound command receipts on authorized Local PostgreSQL, rollback only."""
from contextlib import contextmanager, nullcontext
import importlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool
from erclave_common.errors import ErclaveError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name == 'app' or name.startswith('app.'):
        del sys.modules[name]
repositories = importlib.import_module('app.repositories')
schemas = importlib.import_module('app.schemas')
api = importlib.import_module('app.api')
TENANT = 'ten_739ee59d765d5e14818674800d'


@pytest.fixture
def pg():
    value = os.getenv('ERCLAVE_TEST_DATABASE_URL')
    if not value:
        pytest.skip('Authorized Local PostgreSQL URL required')
    url = make_url(value)
    assert url.host in {'localhost', '127.0.0.1', '::1'} and url.port == 5434
    assert url.database == 'erclave_local' and not url.query
    engine = create_engine(value, poolclass=NullPool)
    try:
        with engine.connect() as connection:
            outer = connection.begin()
            class TransactionEngine:
                @contextmanager
                def connect(self):
                    yield connection
                @contextmanager
                def begin(self):
                    with connection.begin_nested():
                        yield connection
            repo = object.__new__(repositories.MaintenanceRepository)
            repo.engine = TransactionEngine()
            try:
                assert connection.execute(text('select id from admin.tenants where id=:t'), {'t': TENANT}).scalar_one() == TENANT
                yield SimpleNamespace(repo=repo, c=connection, prefix='actor-' + uuid4().hex[:18], actor='actor-' + uuid4().hex[:18])
            finally:
                outer.rollback()
    finally:
        engine.dispose()


def receipt(pg, operation, key):
    return dict(pg.c.execute(text('select request_hash,response_payload,created_at from maintenance.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'), {'t': TENANT, 'o': operation, 'k': key}).mappings().one())


@pytest.mark.parametrize('operation', ['order.transition', 'material_request.create', 'material_request.reject', 'material_request.cancel', 'material_request.reconcile', 'material_request.issue', 'order.reconcile'])
def test_completed_receipts_bind_actor_without_changing_api_fingerprint(pg, operation):
    key = pg.prefix + '-receipt'
    with pg.repo.engine.begin() as c:
        assert pg.repo._claim(c, TENANT, operation, key, 'unchanged-api-digest', actor=pg.actor) is None
        pg.repo._finish(c, TENANT, operation, key, {'id': pg.prefix})
    assert receipt(pg, operation, key)['request_hash'] != 'unchanged-api-digest'
    with pg.repo.engine.begin() as c:
        assert pg.repo._claim(c, TENANT, operation, key, 'unchanged-api-digest', actor=pg.actor) == {'id': pg.prefix}
    for actor, fingerprint in [(pg.actor + '-other', 'unchanged-api-digest'), (pg.actor, 'changed')]:
        with pytest.raises(ValueError, match='idempotency_key_reused'):
            with pg.repo.engine.begin() as c:
                pg.repo._claim(c, TENANT, operation, key, fingerprint, actor=actor)


@pytest.mark.parametrize('operation,action', [('order.transition', 'maintenance.order.cancel'), ('material_request.reject', 'maintenance.material_request.reject')])
def test_legacy_completed_replays_require_unequivocal_transaction_actor(pg, operation, action):
    key = pg.prefix + '-legacy'
    with pg.repo.engine.begin() as c:
        pg.repo._claim(c, TENANT, operation, key, 'legacy', actor=pg.actor)
        pg.repo._finish(c, TENANT, operation, key, {'id': pg.prefix})
        c.execute(text('update maintenance.idempotency_records set request_hash=:h where tenant_id=:t and operation=:o and idempotency_key=:k'), {'h': 'legacy', 't': TENANT, 'o': operation, 'k': key})
        pg.repo._audit(c, TENANT, pg.actor, action, 'order', pg.prefix, {})
    with pg.repo.engine.begin() as c:
        assert pg.repo._claim(c, TENANT, operation, key, 'legacy', actor=pg.actor) == {'id': pg.prefix}
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        with pg.repo.engine.begin() as c:
            pg.repo._claim(c, TENANT, operation, key, 'legacy', actor=pg.actor + '-other')
    pg.repo._audit(pg.c, TENANT, pg.actor + '-other', action, 'order', pg.prefix, {})
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        with pg.repo.engine.begin() as c:
            pg.repo._claim(c, TENANT, operation, key, 'legacy', actor=pg.actor)
    assert receipt(pg, operation, key)['request_hash'] == 'legacy'


def test_ambiguous_legacy_pending_receipt_is_rejected_unchanged(pg):
    operation, key = 'material_request.cancel', pg.prefix + '-pending'
    with pg.repo.engine.begin() as c:
        pg.repo._claim(c, TENANT, operation, key, 'legacy', actor=pg.actor)
        c.execute(text('update maintenance.idempotency_records set request_hash=:h where tenant_id=:t and operation=:o and idempotency_key=:k'), {'h': 'legacy', 't': TENANT, 'o': operation, 'k': key})
    before = receipt(pg, operation, key)
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        with pg.repo.engine.begin() as c:
            pg.repo._claim(c, TENANT, operation, key, 'legacy', actor=pg.actor, resume=True)
    assert receipt(pg, operation, key) == before


def material(pg):
    repo = pg.repo
    payload = schemas.OrderCreate(code=pg.prefix, target_type='facility', title='Synthetic actor test', description='Rollback only', location='Local')
    order = repo.create_order(TENANT, payload, {'machine_code_snapshot': None, 'machine_name_snapshot': None, 'source_production_order_code_snapshot': None}, pg.prefix + '-order', 'order', pg.actor)
    worker = {'id': pg.prefix + '-worker', 'full_name': 'Synthetic'}
    for action in ('request', 'assign'):
        repo.transition(TENANT, order['id'], schemas.TransitionRequest(transition=action, assigned_worker_id=worker['id'] if action == 'assign' else None), worker if action == 'assign' else None, pg.prefix + '-' + action, action, pg.actor)
    request, _ = repo.prepare_material_request(TENANT, order['id'], schemas.MaterialRequestCreate(warehouse_id=pg.prefix + '-warehouse', lines=[schemas.MaterialLine(item_id=pg.prefix + '-item', quantity=2, unit_code='H87')]), {'warehouse_name': 'Synthetic', 'items': [{'code': 'SYNTHETIC', 'name': 'Synthetic'}]}, pg.prefix + '-material', 'material', pg.actor)
    return order, request


def test_pending_recovery_actor_is_checked_before_state_or_external_plan(pg):
    order, request = material(pg)
    repo, rid = pg.repo, request['id']
    repo.complete_material_request(TENANT, rid, pg.prefix + '-material', [], 'dependency_unavailable', pg.actor)
    assert receipt(pg, 'material_request.create', pg.prefix + '-material')['response_payload'] is None
    key = pg.prefix + '-recover'
    _, plan = repo.prepare_material_reconciliation(TENANT, rid, key, 'recover', pg.actor)
    assert len(plan) == 1
    before = repo.get_material_request(TENANT, rid)
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo.prepare_material_reconciliation(TENANT, rid, key, 'recover', pg.actor + '-other')
    assert repo.get_material_request(TENANT, rid) == before
    repo.complete_material_reconciliation(TENANT, rid, key, [], 'dependency_unavailable', pg.actor)
    assert receipt(pg, 'material_request.reconcile', key)['response_payload'] is None
    _, retry = repo.prepare_material_reconciliation(TENANT, rid, key, 'recover', pg.actor)
    assert len(retry) == 1
    reserved = repo.complete_material_reconciliation(TENANT, rid, key, [{'id': pg.prefix + '-reservation', 'original_unit_cost': '2.123456'}], None, pg.actor)
    assert reserved['status'] == 'reserved'
    assert receipt(pg, 'material_request.reconcile', key)['response_payload']['status'] == 'reserved'


def test_issue_and_cancel_keep_partial_intent_pending_and_actor_bound(pg):
    _, request = material(pg)
    repo, rid = pg.repo, request['id']
    repo.complete_material_request(TENANT, rid, pg.prefix + '-material', [{'id': pg.prefix + '-reservation', 'original_unit_cost': '0'}], actor=pg.actor)
    key = pg.prefix + '-issue'
    _, plan = repo.prepare_warehouse_issue(TENANT, rid, pg.actor, key, 'issue')
    before = repo.get_material_request(TENANT, rid)
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo.prepare_warehouse_issue(TENANT, rid, pg.actor + '-other', key, 'issue')
    assert repo.get_material_request(TENANT, rid) == before
    repo.complete_warehouse_issue(TENANT, rid, [], 'dependency_unavailable', pg.actor, key)
    assert receipt(pg, 'material_request.issue', key)['response_payload'] is None
    _, retry = repo.prepare_warehouse_issue(TENANT, rid, pg.actor, key, 'issue')
    issued = repo.complete_warehouse_issue(TENANT, rid, [(retry[0]['id'], {'id': pg.prefix + '-movement'})], None, pg.actor, key)
    assert issued['status'] == 'issued'
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo.prepare_warehouse_issue(TENANT, rid, pg.actor + '-other', key, 'issue')


def test_cancel_pending_retries_same_actor_and_blocks_other_actor(pg):
    _, request = material(pg)
    repo, rid = pg.repo, request['id']
    repo.complete_material_request(TENANT, rid, pg.prefix + '-material', [{'id': pg.prefix + '-reservation'}], actor=pg.actor)
    key = pg.prefix + '-cancel'
    _, plan = repo.prepare_material_cancellation(TENANT, rid, key, 'cancel', pg.actor)
    repo.complete_material_cancellation(TENANT, rid, key, [], 'dependency_unavailable', pg.actor)
    assert receipt(pg, 'material_request.cancel', key)['response_payload'] is None
    before = repo.get_material_request(TENANT, rid)
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        repo.prepare_material_cancellation(TENANT, rid, key, 'cancel', pg.actor + '-other')
    assert repo.get_material_request(TENANT, rid) == before
    _, retry = repo.prepare_material_cancellation(TENANT, rid, key, 'cancel', pg.actor)
    assert retry[0]['line_id'] == plan[0]['line_id']
    result = repo.complete_material_cancellation(TENANT, rid, key, [retry[0]['line_id']], None, pg.actor)
    assert result['status'] == 'cancelled'


@pytest.mark.parametrize('operation', ['issue', 'cancel', 'reconcile', 'reject'])
def test_api_refuses_another_actor_before_inventory_effects(pg, monkeypatch, operation):
    _, request = material(pg)
    repo, rid, key = pg.repo, request['id'], pg.prefix + '-api-command'
    if operation == 'reconcile':
        repo.complete_material_request(TENANT, rid, pg.prefix + '-material', [], 'dependency_unavailable', pg.actor)
    else:
        repo.complete_material_request(TENANT, rid, pg.prefix + '-material', [{'id': pg.prefix + '-reservation'}], actor=pg.actor)
    payload = schemas.MaterialRejectRequest(reason='Synthetic rejection')
    fingerprint = api.digest(payload, {'id': rid}) if operation == 'reject' else api.digest(path={'id': rid})
    if operation == 'issue':
        repo.prepare_warehouse_issue(TENANT, rid, pg.actor, key, fingerprint)
    elif operation == 'cancel':
        repo.prepare_material_cancellation(TENANT, rid, key, fingerprint, pg.actor)
    elif operation == 'reconcile':
        repo.prepare_material_reconciliation(TENANT, rid, key, fingerprint, pg.actor)
    else:
        repo.record_warehouse_rejection(TENANT, rid, payload.reason, key, fingerprint, pg.actor)
    before = repo.get_material_request(TENANT, rid)
    # This is an API/repository regression, not integrated HTTP acceptance. Scope
    # and advisory locks are tested elsewhere; no dependency is contacted here.
    monkeypatch.setattr(api, 'guard_material', lambda *args, **kwargs: None)
    monkeypatch.setattr(repo, 'material_command_lock', lambda *args: nullcontext())
    def unexpected(*args, **kwargs):
        pytest.fail('Actor conflict must be rejected before Inventory HTTP')
    authority = SimpleNamespace(consume=unexpected, release_reservation=unexpected, reserve=unexpected)
    access = api.AuthorizedContext(TENANT, pg.actor + '-other', 'inventory.movement.create', frozenset({'inventory.movement.create'}))
    with pytest.raises(ErclaveError) as raised:
        if operation == 'issue':
            api.issue_material_request(rid, schemas.MaterialIssueRequest(), TENANT, None, key, repo, authority, access)
        elif operation == 'cancel':
            api.cancel_material_request(rid, TENANT, None, key, repo, authority, access)
        elif operation == 'reconcile':
            api.reconcile_material_request(rid, TENANT, None, key, repo, authority, access)
        else:
            api.reject_material_request(rid, payload, TENANT, None, key, repo, authority, access)
    assert raised.value.code == 'idempotency_key_reused'
    assert repo.get_material_request(TENANT, rid) == before


def test_order_reconciliation_pending_is_not_a_completed_receipt(pg):
    payload = schemas.OrderCreate(code=pg.prefix, target_type='facility', title='Synthetic recovery', description='Rollback only', location='Local')
    order = pg.repo.create_order(TENANT, payload, {'machine_code_snapshot': None, 'machine_name_snapshot': None, 'source_production_order_code_snapshot': None}, pg.prefix + '-order', 'order', pg.actor)
    key = pg.prefix + '-reconcile'
    pg.repo.set_order_integration(TENANT, order['id'], 'needs_reconciliation', 'dependency_unavailable', pg.actor)
    assert pg.repo.prepare_order_reconciliation(TENANT, order['id'], key, 'reconcile', pg.actor)[1] is False
    pg.repo.complete_order_reconciliation(TENANT, order['id'], key, pg.actor)
    assert receipt(pg, 'order.reconcile', key)['response_payload'] is None
    with pytest.raises(ValueError, match='idempotency_key_reused'):
        pg.repo.prepare_order_reconciliation(TENANT, order['id'], key, 'reconcile', pg.actor + '-other')
    pg.repo.set_order_integration(TENANT, order['id'], 'completed', actor=pg.actor)
    pg.repo.complete_order_reconciliation(TENANT, order['id'], key, pg.actor)
    assert pg.repo.prepare_order_reconciliation(TENANT, order['id'], key, 'reconcile', pg.actor)[1] is True


def test_transition_parent_intent_precedes_release_and_resumes_after_partial_failure(pg, monkeypatch):
    order, request = material(pg)
    repo, key = pg.repo, pg.prefix + '-cancel-order'
    repo.complete_material_request(TENANT, request['id'], pg.prefix + '-material', [{'id': pg.prefix + '-reservation'}], actor=pg.actor)
    monkeypatch.setattr(api, 'order_scope', lambda *args, **kwargs: (repo.get_order(TENANT, order['id']), None))
    monkeypatch.setattr(api, 'guard_material', lambda *args, **kwargs: None)
    monkeypatch.setattr(repo, 'material_creation_lock', lambda *args: nullcontext())
    releases = []
    def release(*args):
        assert receipt(pg, 'order.transition', key)['response_payload'] is None
        releases.append(args)
        if len(releases) == 1:raise ErclaveError('dependency_unavailable', 'Synthetic partial release', status_code=503)
    authority = SimpleNamespace(release_reservation=release)
    def invoke(actor):
        access = api.AuthorizedContext(TENANT, actor, 'maintenance.order.cancel', frozenset({'maintenance.order.cancel'}))
        return api.transition_order(order['id'], schemas.TransitionRequest(transition='cancel', reason='Rollback'), TENANT, None, key, repo, authority, access)
    with pytest.raises(ErclaveError, match='Every material request'):
        invoke(pg.actor)
    assert receipt(pg, 'order.transition', key)['response_payload'] is None
    with pytest.raises(ErclaveError) as denied:invoke(pg.actor + '-other')
    assert denied.value.code == 'idempotency_key_reused' and len(releases) == 1
    assert invoke(pg.actor).data['status'] == 'cancelled'
    assert len(releases) == 2
    assert receipt(pg, 'order.transition', key)['response_payload']['status'] == 'cancelled'
    assert invoke(pg.actor).data['status'] == 'cancelled' and len(releases) == 2


def test_machine_transition_partial_replay_resumes_without_reapplying_state(pg, monkeypatch):
    order, _ = material(pg)
    repo, key = pg.repo, pg.prefix + '-machine-request'
    pg.c.execute(text("update maintenance.orders set status='draft', target_type='production_machine', production_machine_ref_id=:machine where tenant_id=:t and id=:i"), {'machine': pg.prefix + '-machine', 't': TENANT, 'i': order['id']})
    monkeypatch.setattr(api, 'order_scope', lambda *args, **kwargs: (repo.get_order(TENANT, order['id']), None))
    monkeypatch.setattr(repo, 'material_creation_lock', lambda *args: nullcontext())
    blocks = []
    def block(*args):
        assert receipt(pg, 'order.transition', key)['response_payload'] is None
        blocks.append(args)
        if len(blocks) == 1:raise ErclaveError('dependency_unavailable', 'Synthetic timeout', status_code=503)
    authority = SimpleNamespace(block_machine=block)
    def invoke(actor):
        access = api.AuthorizedContext(TENANT, actor, 'maintenance.order.request', frozenset({'maintenance.order.request'}))
        return api.transition_order(order['id'], schemas.TransitionRequest(transition='request'), TENANT, None, key, repo, authority, access)
    assert invoke(pg.actor).data['integration_status'] == 'needs_reconciliation'
    assert receipt(pg, 'order.transition', key)['response_payload'] is None
    with pytest.raises(ErclaveError) as denied:invoke(pg.actor + '-other')
    assert denied.value.code == 'idempotency_key_reused' and len(blocks) == 1
    assert invoke(pg.actor).data['integration_status'] == 'completed'
    assert len(blocks) == 2 and blocks[0][-1] == blocks[1][-1]
    assert pg.c.execute(text("select count(*) from maintenance.audit_events where tenant_id=:t and entity_id=:i and action='maintenance.order.request' and payload->>'idempotency_key'=:k"), {'t': TENANT, 'i': order['id'], 'k': key}).scalar_one() == 1
    assert receipt(pg, 'order.transition', key)['response_payload']['integration_status'] == 'completed'


def test_return_reconciliation_pending_actor_guard_and_confirmed_terminal_only(pg, monkeypatch):
    order, request = material(pg)
    repo, key = pg.repo, pg.prefix + '-return'
    reservation = pg.prefix + '-reservation'; movement = pg.prefix + '-movement'
    repo.complete_material_request(TENANT, request['id'], pg.prefix + '-material', [{'id': reservation, 'original_unit_cost': '0'}], actor=pg.actor)
    _, plan = repo.prepare_warehouse_issue(TENANT, request['id'], pg.actor, key + '-issue', 'issue')
    repo.complete_warehouse_issue(TENANT, request['id'], [(plan[0]['id'], {'id': movement})], None, pg.actor, key + '-issue')
    confirmed = {'id': pg.prefix + '-return', 'source_id': order['id'], 'source_type': 'maintenance_order', 'status': 'pending', 'movement_id': None, 'original_movement_id': movement, 'reservation_id': reservation, 'quantity': '2', 'unit_cost': '0', 'organization_context': None}
    monkeypatch.setattr(api, 'guard_material', lambda *args, **kwargs: None)
    monkeypatch.setattr(repo, 'material_creation_lock', lambda *args: nullcontext())
    authority = SimpleNamespace(get_return=lambda *args: dict(confirmed))
    def invoke(actor):
        access = api.AuthorizedContext(TENANT, actor, 'inventory.movement.create', frozenset({'inventory.movement.create'}))
        return api.reconcile_material_return(api.MaterialReturnReconcile(return_id=confirmed['id']), TENANT, None, key, repo, authority, access)
    with pytest.raises(ErclaveError) as pending:invoke(pg.actor)
    assert pending.value.code == 'material_return_receipt_required'
    assert receipt(pg, 'material_return.reconcile', key)['response_payload'] is None
    with pytest.raises(ErclaveError) as denied:invoke(pg.actor + '-other')
    assert denied.value.code == 'idempotency_key_reused'
    confirmed.update(status='received_pending_reconciliation', movement_id=pg.prefix + '-return-movement')
    assert invoke(pg.actor)['data']['status'] == 'completed'
    assert invoke(pg.actor)['data']['status'] == 'completed'
    assert receipt(pg, 'material_return.reconcile', key)['response_payload']['status'] == 'completed'
    assert pg.c.execute(text('select count(*) from maintenance.material_return_adjustments where tenant_id=:t and return_id=:i'), {'t': TENANT, 'i': confirmed['id']}).scalar_one() == 1


def test_real_session_order_lock_excludes_other_commands_without_rows(pg):
    repo = repositories.MaintenanceRepository(os.environ['ERCLAVE_TEST_DATABASE_URL'])
    try:
        with repo.material_creation_lock(TENANT, pg.prefix):
            with pytest.raises(ValueError, match='command_in_progress'):
                with repo.material_creation_lock(TENANT, pg.prefix):
                    pytest.fail('Different sessions must not enter the same order operation')
        with repo.material_creation_lock(TENANT, pg.prefix):
            pass
    finally:
        repo.engine.dispose()


def test_concurrent_receipt_insert_waits_for_transaction_and_rolls_back_cleanly(pg):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import time
    engine = create_engine(os.environ['ERCLAVE_TEST_DATABASE_URL'], poolclass=NullPool)
    ready = Event(); worker_pid = []; key = pg.prefix + '-race'
    def second():
        with engine.connect() as c:
            tx = c.begin()
            try:
                worker_pid.append(c.execute(text('select pg_backend_pid()')).scalar_one())
                ready.set()
                return pg.repo._claim(c, TENANT, 'order.reconcile', key, 'race', actor=pg.actor + '-other')
            finally:tx.rollback()
    try:
        with engine.connect() as c:
            tx = c.begin()
            executor = ThreadPoolExecutor(max_workers=1)
            try:
                pg.repo._claim(c, TENANT, 'order.reconcile', key, 'race', actor=pg.actor)
                future = executor.submit(second)
                assert ready.wait(3)
                blocked = False; deadline = time.monotonic() + 3
                with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as observer:
                    while time.monotonic() < deadline:
                        wait = observer.execute(text('select wait_event_type from pg_stat_activity where pid=:p'), {'p': worker_pid[0]}).scalar_one()
                        if wait == 'Lock':blocked = True; break
                        time.sleep(0.02)
                assert blocked and not future.done()
            finally:
                tx.rollback()
                executor.shutdown(wait=True)
            assert future.result(timeout=3) is None
        with engine.connect() as c:
            assert c.execute(text('select count(*) from maintenance.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'), {'t': TENANT, 'o': 'order.reconcile', 'k': key}).scalar_one() == 0
    finally:engine.dispose()


def test_completed_transition_replay_does_not_execute_a_later_pending_operation(pg, monkeypatch):
    order, _ = material(pg)
    repo, key = pg.repo, pg.prefix + '-old-completed'
    payload = schemas.TransitionRequest(transition='cancel', reason='Rollback')
    fingerprint = api.digest(payload, {'id': order['id']})
    with repo.engine.begin() as c:
        repo._claim(c, TENANT, 'order.transition', key, fingerprint, actor=pg.actor)
        repo._finish(c, TENANT, 'order.transition', key, {'id': order['id'], 'status': 'cancelled'})
    historical = receipt(pg, 'order.transition', key)
    pg.c.execute(text("update maintenance.orders set integration_status='needs_reconciliation', integration_operation='block' where tenant_id=:t and id=:i"), {'t': TENANT, 'i': order['id']})
    monkeypatch.setattr(api, 'order_scope', lambda *args, **kwargs: (repo.get_order(TENANT, order['id']), None))
    monkeypatch.setattr(repo, 'material_creation_lock', lambda *args: nullcontext())
    def unexpected(*args):pytest.fail('Historical terminal replay must not execute a later pending command')
    authority = SimpleNamespace(block_machine=unexpected, release_machine=unexpected)
    access = api.AuthorizedContext(TENANT, pg.actor, 'maintenance.order.cancel', frozenset({'maintenance.order.cancel'}))
    assert api.transition_order(order['id'], payload, TENANT, None, key, repo, authority, access).data['integration_status'] == 'needs_reconciliation'
    assert receipt(pg, 'order.transition', key) == historical
