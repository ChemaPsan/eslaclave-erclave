"""PostgreSQL + private Local files. Synthetic orders only in the authorized tenant."""
import base64
import importlib
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from erclave_common.errors import ErclaveError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."):del sys.modules[name]
repos=importlib.import_module("app.repositories")
schemas=importlib.import_module("app.schemas")
storage=importlib.import_module("app.evidence_files")


def test_service_evidence_gates_expiry_idempotency_and_product_isolation():
    url=os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not url:pytest.skip("Local PostgreSQL required")
    u=make_url(url);assert u.host in ("127.0.0.1","localhost") and u.port==5434 and u.database=="erclave_local"
    t="ten_739ee59d765d5e14818674800d";tag=uuid4().hex[:12];actor="evidence_"+tag
    engine=create_engine(url);repo=repos.ProductionRepository(engine);orders={};keys=[]
    try:
        with engine.begin() as c:
            for kind in ("service","product"):
                source=c.execute(text("select o.id from production.production_orders o join production.product_services p on p.tenant_id=o.tenant_id and p.id=o.product_service_id where o.tenant_id=:t and p.type=:k order by o.created_at limit 1"),{"t":t,"k":kind}).scalar_one()
                oid="evidence_"+kind+"_"+tag;orders[kind]=oid
                c.execute(text("""insert into production.production_orders(id,tenant_id,code,product_service_id,recipe_id,recipe_version_id,quantity,unit,status,responsible_name_snapshot,planned_cost,recipe_snapshot,resource_validation_snapshot,validated_at,created_by)
                    select :o,tenant_id,:o,product_service_id,recipe_id,recipe_version_id,1,unit,'released','Evidence test',0,recipe_snapshot,'{}',now(),:a from production.production_orders where tenant_id=:t and id=:source"""),{"o":oid,"a":actor,"t":t,"source":source})
                c.execute(text("""insert into production.production_order_stages(id,tenant_id,production_order_id,recipe_stage_id,name,sort_order,status,planned_minutes,weight_percent,progress_percent)
                    select :id,tenant_id,:o,recipe_stage_id,name,1,'pending',0,100,0 from production.production_order_stages where tenant_id=:t and production_order_id=:source order by sort_order limit 1"""),{"id":"stage_"+kind+"_"+tag,"o":oid,"t":t,"source":source})
        order=orders["service"]
        with pytest.raises(ValueError,match="start_required"):repo.preflight_order_status(t,order,"waiting_resources")
        assert repo.preflight_order_status(t,orders["product"],"waiting_resources")
        payload=schemas.ServiceEvidenceRequest(description="Received service with documented condition",files=[{"filename":"receipt.txt","content_base64":base64.b64encode(b"Written attachment").decode()}])
        first=repo.save_service_evidence(t,order,"start",payload,actor)
        assert repo.save_service_evidence(t,order,"start",payload,actor)==first
        assert len(first)==1 and len(first[0]["files"])==1
        with pytest.raises(ErclaveError):repo.save_service_evidence(t,order,"start",schemas.ServiceEvidenceRequest(description="Different evidence"),actor)
        with pytest.raises(ErclaveError):repo.save_service_evidence(t,orders["product"],"start",payload,actor)
        assert repo.get_order("other-tenant",order) is None
        fid=first[0]["files"][0]["id"]
        with pytest.raises(ErclaveError):repo.evidence_file("other-tenant",order,fid)
        row,content=repo.evidence_file(t,order,fid);keys.append(row["object_key"]);assert content==b"Written attachment"
        repo.update_order_status(t,order,schemas.ProductionOrderStatusRequest(status="in_progress",reason="Start with evidence"),tag+"start",tag+"hash",actor)
        stage="stage_service_"+tag;progress=schemas.OrderStageUpdateRequest(status="completed",progress_percent=100)
        with pytest.raises(ValueError,match="finish_required"):repo.update_order_stage(t,stage,progress,tag+"no-finish",tag,actor)
        assert repo.get_order(t,order).stages[0].progress_percent==0
        repo.save_service_evidence(t,order,"finish",schemas.ServiceEvidenceRequest(description="Completed service and verified result"),actor)
        repo.update_order_stage(t,stage,progress,tag+"finish",tag,actor)
        assert repo.get_order(t,order).status=="in_validation"
        with engine.begin() as c:c.execute(text("update production.service_evidence_files set expires_at=now()-interval '1 second' where tenant_id=:t and id=:i"),{"t":t,"i":fid})
        with pytest.raises(ErclaveError) as error:repo.evidence_file(t,order,fid)
        assert error.value.status_code==410
        assert repo.purge_service_evidence()>=1
        assert not storage.PrivateEvidenceStore().path(keys[0]).exists()
        evidence=repo.get_order(t,order).service_evidence
        assert evidence[0]["description"]==payload.description and evidence[0]["files"][0]["expired"]
        assert repo.get_order(t,orders["product"]).service_evidence==[]
    finally:
        with engine.begin() as c:
            for oid in orders.values():
                files=c.execute(text("select f.object_key from production.service_evidence_files f join production.service_evidence e on e.tenant_id=f.tenant_id and e.id=f.evidence_id where f.tenant_id=:t and e.order_id=:o"),{"t":t,"o":oid}).scalars().all()
                keys.extend(key for key in files if key)
                c.execute(text("delete from production.service_evidence_files where tenant_id=:t and evidence_id in (select id from production.service_evidence where tenant_id=:t and order_id=:o)"),{"t":t,"o":oid})
                c.execute(text("delete from production.service_evidence where tenant_id=:t and order_id=:o"),{"t":t,"o":oid})
                c.execute(text("delete from production.production_order_stages where tenant_id=:t and production_order_id=:o"),{"t":t,"o":oid})
                c.execute(text("delete from production.production_orders where tenant_id=:t and id=:o"),{"t":t,"o":oid})
            for table in ("audit_events","idempotency_records"):c.execute(text(f"delete from production.{table} where tenant_id=:t and actor_id=:a"),{"t":t,"a":actor})
        for key in keys:storage.PrivateEvidenceStore().delete(key)
        engine.dispose()


def test_service_evidence_migration_rollback_is_lossless_or_blocked():
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError
    url=os.getenv("ERCLAVE_TEST_DATABASE_URL")
    if not url:pytest.skip("Local PostgreSQL required")
    u=make_url(url);assert u.host in ("127.0.0.1","localhost") and u.port==5434 and u.database=="erclave_local"
    source=Path(__file__).resolve().parents[3]/"alembic/versions/20260913_0036_service_evidence.py"
    spec=importlib.util.spec_from_file_location("evidence_migration",source);migration=importlib.util.module_from_spec(spec);spec.loader.exec_module(migration)
    engine=create_engine(url)
    with engine.connect() as c:
        transaction=c.begin()
        try:
            c.execute(text("lock table production.service_evidence in access exclusive mode"))
            migration.op=Operations(MigrationContext.configure(c))
            count=c.scalar(text("select count(*) from production.service_evidence"))
            if count:
                with pytest.raises(DBAPIError,match="archive explicitly"),c.begin_nested():migration.downgrade()
            else:
                migration.downgrade();migration.upgrade()
            assert c.scalar(text("select count(*) from production.service_evidence"))==count
        finally:transaction.rollback()
    engine.dispose()
