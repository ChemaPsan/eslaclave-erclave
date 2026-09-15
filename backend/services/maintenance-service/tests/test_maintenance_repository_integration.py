import importlib
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4, uuid5
from sqlalchemy.engine import make_url

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv("ERCLAVE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="ERCLAVE_TEST_DATABASE_URL is required")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]
repositories = importlib.import_module("app.repositories")
schemas = importlib.import_module("app.schemas")


@pytest.fixture
def repository():
    # These integration tests may only write synthetic records to the approved Local tenant.
    url = make_url(DATABASE_URL)
    assert url.host in {"localhost", "127.0.0.1", "::1"}
    assert url.port == 5434 and url.database == "erclave_local"
    tenant = os.getenv("ERCLAVE_TEST_TENANT_ID", "ten_739ee59d765d5e14818674800d")
    assert tenant == "ten_739ee59d765d5e14818674800d"
    repo = repositories.MaintenanceRepository(DATABASE_URL)
    repo.engine.dispose()
    repo.engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
    namespace = uuid4()
    prefix = namespace.hex + "-"

    def fixture_id(value):
        if value.startswith(("usr_", "hrw_", "maq_")):
            return value.split("_", 1)[0] + "_" + uuid5(namespace, value).hex
        return prefix + value

    repo.fixture_id = fixture_id
    actors = [repo.fixture_id(value) for value in ("usr_test", "usr_warehouse", "usr_maintenance_integration_test")]

    try:
        yield repo, tenant
    finally:
        try:
            with repo.engine.begin() as connection:
                # Ownership, never a before/after tenant baseline: concurrent orders survive.
                order_ids = list(connection.execute(text("select id from maintenance.orders where tenant_id=:tenant and created_by_actor_id=any(:actors)"), {"tenant": tenant, "actors": actors}).scalars())
                params = {"tenant": tenant, "ids": order_ids}
                if order_ids:
                    connection.execute(text("delete from maintenance.material_request_lines where tenant_id=:tenant and material_request_id in (select id from maintenance.material_requests where tenant_id=:tenant and order_id=any(:ids))"), params)
                    connection.execute(text("delete from maintenance.material_requests where tenant_id=:tenant and order_id=any(:ids)"), params)
                    connection.execute(text("delete from maintenance.time_entries where tenant_id=:tenant and order_id=any(:ids)"), params)
                    connection.execute(text("delete from maintenance.assignments where tenant_id=:tenant and order_id=any(:ids)"), params)
                    connection.execute(text("delete from maintenance.orders where tenant_id=:tenant and id=any(:ids)"), params)
                connection.execute(text("delete from maintenance.audit_events where tenant_id=:tenant and actor_id=any(:actors)"), {"tenant": tenant, "actors": actors})
                connection.execute(text("delete from maintenance.idempotency_records where tenant_id=:tenant and left(idempotency_key,length(:prefix))=:prefix"), {"tenant": tenant, "prefix": prefix})
        finally:
            repo.engine.dispose()


def facility(code="MT-TEST"):
    return schemas.OrderCreate(code=f"{code}-{uuid4().hex}", target_type="facility", priority="high", title="Fuga hidraulica", description="Fuga visible en la linea", location="Edificio A")


def transition(name, worker=None):
    return schemas.TransitionRequest(transition=name, assigned_worker_id=worker)


def test_corrective_order_closes_with_worker_time_and_evidence(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility(), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, repo.fixture_id("create-maintenance-1"), "hash-create", repo.fixture_id("usr_maintenance_integration_test"))
    repo.transition(tenant, order["id"], transition("request"), None, repo.fixture_id("request-maintenance-1"), "hash-request", repo.fixture_id("usr_test"))
    worker = {"id": repo.fixture_id("hrw_test"), "full_name": "Tecnico Prueba"}
    repo.transition(tenant, order["id"], transition("assign", worker["id"]), worker, repo.fixture_id("assign-maintenance-1"), "hash-assign", repo.fixture_id("usr_test"))
    repo.transition(tenant, order["id"], transition("start"), None, repo.fixture_id("start-maintenance-1"), "hash-start", repo.fixture_id("usr_test"))
    started = datetime.now(timezone.utc) - timedelta(hours=1)
    entry = repo.create_time(tenant, order["id"], schemas.TimeEntryCreate(worker_id=worker["id"], started_at=started, ended_at=started + timedelta(minutes=45)), worker, repo.fixture_id("time-maintenance-1"), "hash-time", repo.fixture_id("usr_test"))
    assert entry["minutes"] == 45
    repo.update_order(tenant, order["id"], schemas.OrderUpdate(diagnosis="Sello danado", work_performed="Cambio de sello", verification_notes="Sin fuga tras prueba"), repo.fixture_id("update-maintenance-1"), "hash-update", repo.fixture_id("usr_test"))
    resolved = repo.transition(tenant, order["id"], transition("resolve"), None, repo.fixture_id("resolve-maintenance-1"), "hash-resolve", repo.fixture_id("usr_test"))
    closed = repo.transition(tenant, order["id"], transition("close"), None, repo.fixture_id("close-maintenance-1"), "hash-close", repo.fixture_id("usr_test"))
    assert resolved["status"] == "resolved"
    assert closed["status"] == "closed"
    assert closed["total_minutes"] == 45


def test_material_request_persists_multiple_lines_and_reconciles(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility("MT-PARTS"), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, repo.fixture_id("create-parts-1"), "hash-create", repo.fixture_id("usr_test"))
    repo.transition(tenant, order["id"], transition("request"), None, repo.fixture_id("request-parts-1"), "hash-request", repo.fixture_id("usr_test"))
    worker = {"id": repo.fixture_id("hrw_test"), "full_name": "Tecnico Prueba"}
    repo.transition(tenant, order["id"], transition("assign", worker["id"]), worker, repo.fixture_id("assign-parts-1"), "hash-assign", repo.fixture_id("usr_test"))
    payload = schemas.MaterialRequestCreate(warehouse_id="wh_parts", lines=[schemas.MaterialLine(item_id="itm_a", quantity=2, unit_code="PZA"), schemas.MaterialLine(item_id="itm_b", quantity=1, unit_code="PZA")])
    request, plan = repo.prepare_material_request(tenant, order["id"], payload, {"warehouse_name": "Refacciones", "items": [{"code": "A", "name": "Sello"}, {"code": "B", "name": "Banda"}]}, repo.fixture_id("material-maintenance-1"), "hash-material", repo.fixture_id("usr_test"))
    completed = repo.complete_material_request(tenant, request["id"], repo.fixture_id("material-maintenance-1"), [{"id": "res_a", "unit_cost_snapshot": 10}, {"id": "res_b", "unit_cost_snapshot": 20}])
    assert len(plan) == 2
    assert completed["status"] == "reserved"
    with repo.material_command_lock(tenant,request["id"]):
        _,issue_plan=repo.prepare_warehouse_issue(tenant,request["id"],repo.fixture_id("usr_warehouse"))
        repo.complete_warehouse_issue(tenant,request["id"],[(issue_plan[0]["id"],{"id":"mov_a"}),(issue_plan[1]["id"],{"id":"mov_b"})],None,repo.fixture_id("usr_warehouse"))
    assert repo.get_order(tenant, order["id"])["material_requests"][0]["status"] == "issued"


def test_idempotency_and_tenant_isolation(repository):
    repo, tenant = repository
    payload = facility("MT-IDEMP")
    snapshots = {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}
    first = repo.create_order(tenant, payload, snapshots, repo.fixture_id("create-idempotent-1"), "same", repo.fixture_id("usr_test"))
    replay = repo.create_order(tenant, payload, snapshots, repo.fixture_id("create-idempotent-1"), "same", repo.fixture_id("usr_test"))
    assert replay["id"] == first["id"]
    assert repo.get_order("ten_other", first["id"]) is None
    with pytest.raises(ValueError, match="idempotency_key_reused"):
        repo.create_order(tenant, payload, snapshots, repo.fixture_id("create-idempotent-1"), "different", repo.fixture_id("usr_test"))


def test_only_one_active_order_can_block_a_machine(repository):
    repo, tenant = repository
    snapshots = {"machine_code_snapshot": "M-01", "machine_name_snapshot": "Torno", "source_production_order_code_snapshot": None}
    first = schemas.OrderCreate(code=repo.fixture_id("MT-MACHINE-1"), target_type="production_machine", production_machine_id=repo.fixture_id("maq_test"), priority="critical", title="Torno detenido", description="No inicia", location="Linea 1")
    second = first.model_copy(update={"code": repo.fixture_id("MT-MACHINE-2")})
    order = repo.create_order(tenant, first, snapshots, repo.fixture_id("machine-create-1"), repo.fixture_id("machine-one"), repo.fixture_id("usr_test"))
    repo.transition(tenant, order["id"], transition("request"), None, repo.fixture_id("machine-request-1"), repo.fixture_id("machine-request"), repo.fixture_id("usr_test"))
    competing = repo.create_order(tenant, second, snapshots, repo.fixture_id("machine-create-2"), repo.fixture_id("machine-two"), repo.fixture_id("usr_test"))
    with pytest.raises(ValueError, match="maintenance_order_conflict"):
        repo.transition(tenant, competing["id"], transition("request"), None, repo.fixture_id("machine-request-2"), repo.fixture_id("machine-request-two"), repo.fixture_id("usr_test"))


def test_reassignment_keeps_one_primary_worker(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility("MT-ASSIGN"), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, repo.fixture_id("create-assignment-maintenance"), "hash-create", repo.fixture_id("usr_maintenance_integration_test"))
    repo.transition(tenant, order["id"], transition("request"), None, repo.fixture_id("request-assignment-maintenance"), "hash-request", repo.fixture_id("usr_test"))
    first = {"id": repo.fixture_id("hrw_first"), "full_name": "Tecnico Uno"}
    second = {"id": repo.fixture_id("hrw_second"), "full_name": "Tecnico Dos"}
    repo.transition(tenant, order["id"], transition("assign", first["id"]), first, repo.fixture_id("assign-first-maintenance"), "hash-first", repo.fixture_id("usr_test"))
    repo.transition(tenant, order["id"], transition("assign", second["id"]), second, repo.fixture_id("assign-second-maintenance"), "hash-second", repo.fixture_id("usr_test"))
    with repo.engine.connect() as connection:
        primary = connection.execute(text("select count(*) from maintenance.assignments where tenant_id=:tenant and order_id=:order and is_primary"), {"tenant": tenant, "order": order["id"]}).scalar_one()
    assert primary == 1
    assert repo.get_order(tenant, order["id"])["assigned_worker_id"] == second["id"]


def test_partial_material_cancellation_is_retryable(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility("MT-CANCEL-PARTS"), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, repo.fixture_id("create-cancel-maintenance"), "hash-create", repo.fixture_id("usr_maintenance_integration_test"))
    repo.transition(tenant, order["id"], transition("request"), None, repo.fixture_id("request-cancel-maintenance"), "hash-request", repo.fixture_id("usr_test"))
    worker = {"id": repo.fixture_id("hrw_test"), "full_name": "Tecnico Prueba"}
    repo.transition(tenant, order["id"], transition("assign", worker["id"]), worker, repo.fixture_id("assign-cancel-maintenance"), "hash-assign", repo.fixture_id("usr_test"))
    payload = schemas.MaterialRequestCreate(warehouse_id="wh_parts", lines=[schemas.MaterialLine(item_id="itm_a", quantity=2, unit_code="PZA"), schemas.MaterialLine(item_id="itm_b", quantity=1, unit_code="PZA")])
    request, _ = repo.prepare_material_request(tenant, order["id"], payload, {"warehouse_name": "Refacciones", "items": [{"code": "A", "name": "Sello"}, {"code": "B", "name": "Banda"}]}, repo.fixture_id("material-cancel-maintenance"), "hash-material", repo.fixture_id("usr_test"))
    repo.complete_material_request(tenant, request["id"], repo.fixture_id("material-cancel-maintenance"), [{"id": "res_a", "unit_cost_snapshot": 10}, {"id": "res_b", "unit_cost_snapshot": 20}])
    _, plan = repo.prepare_material_cancellation(tenant, request["id"], repo.fixture_id("cancel-parts-maintenance"), "hash-cancel", repo.fixture_id("usr_test"))
    failed = repo.complete_material_cancellation(tenant, request["id"], repo.fixture_id("cancel-parts-maintenance"), [plan[0]["line_id"]], "dependency_unavailable", repo.fixture_id("usr_test"))
    assert failed["status"] == "needs_reconciliation"
    assert failed["pending_operation"] == "cancel"
    _, retry = repo.prepare_material_reconciliation(tenant, request["id"], repo.fixture_id("reconcile-parts-maintenance"), "hash-reconcile", repo.fixture_id("usr_test"))
    completed = repo.complete_material_reconciliation(tenant, request["id"], repo.fixture_id("reconcile-parts-maintenance"), [{"id": retry[0]["reservation_id"]}], None, repo.fixture_id("usr_test"))
    assert completed["status"] == "cancelled"
    assert completed["pending_operation"] is None


def pending_material(repo,tenant,suffix):
    suffix=repo.fixture_id(suffix)
    order=repo.create_order(tenant,facility("MT-PENDING"),{"machine_code_snapshot":None,"machine_name_snapshot":None,"source_production_order_code_snapshot":None},suffix+"-create","create",repo.fixture_id("usr_test"))
    repo.transition(tenant,order["id"],transition("request"),None,suffix+"-request","request",repo.fixture_id("usr_test"))
    worker={"id":repo.fixture_id("hrw_test"),"full_name":"Tecnico Prueba"}
    repo.transition(tenant,order["id"],transition("assign",worker["id"]),worker,suffix+"-assign","assign",repo.fixture_id("usr_test"))
    payload=schemas.MaterialRequestCreate(warehouse_id="wh_parts",lines=[schemas.MaterialLine(item_id="itm_a",quantity=2,unit_code="PZA"),schemas.MaterialLine(item_id="itm_b",quantity=1,unit_code="PZA")])
    req,_=repo.prepare_material_request(tenant,order["id"],payload,{"warehouse_name":"Refacciones","items":[{"code":"A","name":"Sello"},{"code":"B","name":"Banda"}]},suffix+"-materials","materials",repo.fixture_id("usr_test"))
    req=repo.complete_material_request(tenant,req["id"],suffix+"-materials",[{"id":"res_a","unit_cost_snapshot":10},{"id":"res_b","unit_cost_snapshot":20}])
    return order,req


def test_warehouse_partial_failure_queue_isolation_and_retry(repository):
    repo,tenant=repository
    order,req=pending_material(repo,tenant,"WH-RETRY")
    page,more=repo.list_warehouse_material_requests(tenant,1,0)
    assert repo.list_warehouse_material_requests("ten_other")[0]==[]
    all_rows,_=repo.list_warehouse_material_requests(tenant,100)
    row=next(x for x in all_rows if x["id"]==req["id"])
    assert row["order_code"]==order["code"]
    assert row["assigned_worker_name"]=="Tecnico Prueba"
    assert "diagnosis" not in row
    with repo.material_command_lock(tenant,req["id"]):
        _,plan=repo.prepare_warehouse_issue(tenant,req["id"],repo.fixture_id("usr_warehouse"))
        partial=repo.complete_warehouse_issue(tenant,req["id"],[(plan[0]["id"],{"id":"mov_a"})],"dependency_unavailable",repo.fixture_id("usr_warehouse"))
    assert partial["status"]=="needs_reconciliation"
    assert partial["lines"][0]["line_status"]=="issued"
    with pytest.raises(ValueError,match="material_request_not_cancellable"):
        repo.prepare_material_cancellation(tenant,req["id"],repo.fixture_id("warehouse-cancel"),"cancel",repo.fixture_id("usr_test"))
    with repo.material_command_lock(tenant,req["id"]):
        _,retry=repo.prepare_warehouse_issue(tenant,req["id"],repo.fixture_id("usr_warehouse"))
        assert [line["id"] for line in retry]==[plan[1]["id"]]
        done=repo.complete_warehouse_issue(tenant,req["id"],[(retry[0]["id"],{"id":"mov_b"})],None,repo.fixture_id("usr_warehouse"))
        assert repo.prepare_warehouse_issue(tenant,req["id"],repo.fixture_id("usr_warehouse"))[1] is None
    assert done["status"]=="issued"
    assert req["id"] not in [x["id"] for x in repo.list_warehouse_material_requests(tenant,100)[0]]
    with repo.engine.connect() as c:
        audit=c.execute(text("select actor_id,payload from maintenance.audit_events where tenant_id=:t and entity_id=:r and action='maintenance.material_request.authorize_issue' order by occurred_at limit 1"),{"t":tenant,"r":req["id"]}).mappings().one()
        assert audit["actor_id"]==repo.fixture_id("usr_warehouse")
        assert audit["payload"]["recipient_worker_id"]==repo.fixture_id("hrw_test")


def test_warehouse_lock_rejects_competing_commands_and_recovers_after_crash(repository):
    from concurrent.futures import ThreadPoolExecutor
    repo,tenant=repository
    _,req=pending_material(repo,tenant,"WH-LOCK")
    def competing():
        with repo.material_command_lock(tenant,req["id"]):return "unexpected"
    with repo.material_command_lock(tenant,req["id"]):
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(ValueError,match="command_in_progress"):pool.submit(competing).result()
        _,plan=repo.prepare_warehouse_issue(tenant,req["id"],repo.fixture_id("usr_warehouse"))
    # Simulate process loss after durable preparation, before receiving Inventory responses.
    with repo.material_command_lock(tenant,req["id"]):
        _,retry=repo.prepare_warehouse_issue(tenant,req["id"],repo.fixture_id("usr_warehouse"))
        assert [x["id"] for x in retry]==[x["id"] for x in plan]
    assert repo.prepare_warehouse_issue("ten_other",req["id"],repo.fixture_id("usr_test"))== (None,None)


def test_warehouse_rejection_preserves_reason_and_releases_without_issue(repository):
    repo,tenant=repository
    _,req=pending_material(repo,tenant,"WH-REJECT")
    with repo.material_command_lock(tenant,req["id"]):
        repo.record_warehouse_rejection(tenant,req["id"],"Solicitud duplicada",repo.fixture_id("warehouse-reject"),"hash-reason",repo.fixture_id("usr_warehouse"))
        repo.record_warehouse_rejection(tenant,req["id"],"Solicitud duplicada",repo.fixture_id("warehouse-reject"),"hash-reason",repo.fixture_id("usr_warehouse"))
        with pytest.raises(ValueError,match="idempotency_key_reused"):
            repo.record_warehouse_rejection(tenant,req["id"],"Otro motivo",repo.fixture_id("warehouse-reject"),"different",repo.fixture_id("usr_warehouse"))
        _,plan=repo.prepare_material_cancellation(tenant,req["id"],repo.fixture_id("warehouse-reject"),"cancel",repo.fixture_id("usr_warehouse"))
        cancelled=repo.complete_material_cancellation(tenant,req["id"],repo.fixture_id("warehouse-reject"),[x["line_id"] for x in plan],None,repo.fixture_id("usr_warehouse"))
    assert cancelled["status"]=="cancelled"
    assert all(x["inventory_movement_id"] is None for x in cancelled["lines"])
    with pytest.raises(ValueError,match="material_request_not_issuable"):
        repo.prepare_warehouse_issue(tenant,req["id"],repo.fixture_id("usr_warehouse"))
    with repo.engine.connect() as c:
        reasons=c.execute(text("select payload->>'reason' from maintenance.audit_events where tenant_id=:t and entity_id=:r and action='maintenance.material_request.reject'"),{"t":tenant,"r":req["id"]}).scalars().all()
        assert reasons==["Solicitud duplicada"]
