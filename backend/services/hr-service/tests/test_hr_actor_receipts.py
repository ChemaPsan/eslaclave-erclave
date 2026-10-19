"""Legacy and new HR receipt authorship, in the authorized rollback fixture."""
from types import SimpleNamespace
from uuid import uuid4
import pytest
from test_hr_organization import local_store,TENANT


@pytest.mark.parametrize('operation',['area.create','area.update','position.create','position.update','worker.create','worker.update'])
def test_postgres_hr_receipt_actor_binding(local_store,operation):
    store,conn,area,_,_=local_store;repo=store.repository;key='actor-'+uuid4().hex
    assert repo._claim(conn,TENANT,operation,key,'hash','original') is None
    value=SimpleNamespace(model_dump=lambda **kw:{'id':area})
    repo._done(conn,TENANT,operation,key,value)
    assert repo._claim(conn,TENANT,operation,key,'hash','original')=={'id':area}
    with pytest.raises(ValueError,match='idempotency_key_reused'):repo._claim(conn,TENANT,operation,key,'hash','other')
    assert repo._claim(conn,TENANT,operation,key,'hash','original')=={'id':area}


@pytest.mark.parametrize('operation',['area.create','area.update','position.create','position.update','worker.create','worker.update'])
def test_postgres_hr_legacy_receipt_uses_prefixed_action_and_real_created_at(local_store,operation):
    store,conn,area,_,_=local_store;repo=store.repository;key='legacy-'+uuid4().hex
    assert repo._claim(conn,TENANT,operation,key,'hash') is None
    repo._audit(conn,TENANT,'original','hr.'+operation,'area',area,{})
    repo._done(conn,TENANT,operation,key,SimpleNamespace(model_dump=lambda **kw:{'id':area}))
    assert repo._claim(conn,TENANT,operation,key,'hash','original')=={'id':area}
    with pytest.raises(ValueError,match='idempotency_key_reused'):repo._claim(conn,TENANT,operation,key,'hash','other')
