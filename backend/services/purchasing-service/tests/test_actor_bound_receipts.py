"""Local demo-only transaction tests; every synthetic write is rolled back."""
import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name == 'app' or name.startswith('app.'):
        del sys.modules[name]
repos=importlib.import_module('app.repositories')
TENANT='ten_739ee59d765d5e14818674800d'
URL=os.getenv('ERCLAVE_TEST_DATABASE_URL','')
pytestmark=pytest.mark.skipif(not URL,reason='Local PostgreSQL required')

@pytest.fixture
def pg():
    url=make_url(URL)
    assert url.host=='127.0.0.1' and url.port==5434 and url.database=='erclave_local' and not url.query
    engine=create_engine(URL)
    with engine.connect() as connection:
        tx=connection.begin()
        assert connection.execute(text('select id from admin.tenants where id=:t'),{'t':TENANT}).scalar_one()==TENANT
        class Transaction:
            @contextmanager
            def begin(self):yield connection
            @contextmanager
            def connect(self):yield connection
        repo=repos.PurchasingRepository(URL);repo.engine.dispose();repo.engine=Transaction()
        try:yield repo,connection,'cc20-actor-'+uuid4().hex[:14]
        finally:tx.rollback()
    engine.dispose()

@pytest.mark.parametrize('operation,lookup',[('supplier.create','supplier_replay'),('receipt.create','receipt_replay')])
def test_completed_receipt_never_inherits_another_actor(pg,operation,lookup):
    repo,c,key=pg
    assert repo._claim(c,TENANT,operation,key,'request','actor-a') is None
    repo._finish(c,TENANT,operation,key,{'id':'synthetic'})
    row=c.execute(text('select request_hash from purchasing.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'),{'t':TENANT,'o':operation,'k':key}).mappings().one()
    assert row['request_hash']==repo._actor_hash('request','actor-a')
    assert getattr(repo,lookup)(TENANT,key,'request','actor-a')=={'id':'synthetic'}
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        getattr(repo,lookup)(TENANT,key,'request','actor-b')
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(c,TENANT,operation,key,'request','actor-b')

def test_pending_bound_intent_resumes_only_same_actor(pg):
    repo,c,key=pg
    repo._claim(c,TENANT,'receipt.reconcile',key,'request','actor-a')
    assert repo._claim(c,TENANT,'receipt.reconcile',key,'request','actor-a',resume=True) is None
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(c,TENANT,'receipt.reconcile',key,'request','actor-b',resume=True)
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(c,TENANT,'receipt.reconcile',key,'changed','actor-a',resume=True)

def test_legacy_completed_receipt_requires_unambiguous_transaction_audit(pg):
    repo,c,key=pg
    repo._claim(c,TENANT,'supplier.create',key,'legacy')
    repo._finish(c,TENANT,'supplier.create',key,{'id':key})
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo.supplier_replay(TENANT,key,'legacy','actor-a')
    repo._audit(c,TENANT,'actor-a','supplier.create','supplier',key,{})
    assert repo.supplier_replay(TENANT,key,'legacy','actor-a')=={'id':key}
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo.supplier_replay(TENANT,key,'legacy','actor-b')
    repo._audit(c,TENANT,'actor-b','supplier.create','supplier',key,{})
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo.supplier_replay(TENANT,key,'legacy','actor-a')

def test_legacy_pending_receipt_does_not_invent_an_author(pg):
    repo,c,key=pg
    repo._claim(c,TENANT,'receipt.reconcile',key,'legacy')
    before=c.execute(text('select request_hash,response_payload from purchasing.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'),{'t':TENANT,'o':'receipt.reconcile','k':key}).mappings().one()
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(c,TENANT,'receipt.reconcile',key,'legacy','actor-a',resume=True)
    after=c.execute(text('select request_hash,response_payload from purchasing.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'),{'t':TENANT,'o':'receipt.reconcile','k':key}).mappings().one()
    assert dict(after)==dict(before)

def test_new_and_legacy_receipt_timestamps_match_initial_iso_response(pg):
    from datetime import datetime,timezone
    from fastapi.encoders import jsonable_encoder
    repo,c,key=pg
    stamp=datetime(2026,10,18,23,42,0,123456,tzinfo=timezone.utc)
    value={'id':key,'created_at':stamp,'received_at':stamp,'last_reconciliation_at':stamp}
    repo._claim(c,TENANT,'receipt.create',key,'request','actor-a')
    repo._finish(c,TENANT,'receipt.create',key,value)
    expected=jsonable_encoder(value)
    assert repo.receipt_replay(TENANT,key,'request','actor-a')==expected
    persisted=c.execute(text('select response_payload from purchasing.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'),{'t':TENANT,'o':'receipt.create','k':key}).scalar_one()
    assert persisted==expected
    # Canonical wire output also handles the historical space separator without
    # rewriting the receipt's hash, actor proof, or persisted history.
    c.execute(text("update purchasing.idempotency_records set response_payload=cast(:p as jsonb) where tenant_id=:t and operation='receipt.create' and idempotency_key=:k"),{'t':TENANT,'k':key,'p':__import__('json').dumps(value,default=str)})
    assert repo.receipt_replay(TENANT,key,'request','actor-a')==expected

def test_legacy_reconcile_uses_frozen_reconciler_and_matching_prepare_time(pg):
    repo,c,key=pg
    repo._claim(c,TENANT,'receipt.reconcile',key,'legacy')
    prepared=c.execute(text('select created_at from purchasing.idempotency_records where tenant_id=:t and operation=:o and idempotency_key=:k'),{'t':TENANT,'o':'receipt.reconcile','k':key}).scalar_one()
    value={'id':key,'reconciled_by_actor_id':'actor-a','last_reconciliation_at':prepared.isoformat()}
    repo._finish(c,TENANT,'receipt.reconcile',key,value)
    # Distinct timestamp models the external call between prepare and complete.
    repo._audit(c,TENANT,'actor-a','receipt.reconcile','purchase_receipt',key,{})
    c.execute(text("update purchasing.audit_events set occurred_at=occurred_at+interval '1 second' where tenant_id=:t and entity_id=:id"),{'t':TENANT,'id':key})
    assert repo._claim(c,TENANT,'receipt.reconcile',key,'legacy','actor-a',resume=True)==value
    with pytest.raises(ValueError,match='idempotency_key_reused'):
        repo._claim(c,TENANT,'receipt.reconcile',key,'legacy','actor-b',resume=True)
