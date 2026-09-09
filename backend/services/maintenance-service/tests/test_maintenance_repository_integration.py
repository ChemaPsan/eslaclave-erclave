import importlib
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
    repo = repositories.MaintenanceRepository(DATABASE_URL)
    repo.engine.dispose()
    repo.engine = create_engine(DATABASE_URL, pool_pre_ping=True, poolclass=NullPool)
    tenant = os.getenv("ERCLAVE_TEST_TENANT_ID", "ten_739ee59d765d5e14818674800d")
    with repo.engine.connect() as connection:
        baseline_orders = set(connection.execute(text("select id from maintenance.orders where tenant_id=:tenant"), {"tenant": tenant}).scalars())
        baseline_audits = set(connection.execute(text("select id from maintenance.audit_events where tenant_id=:tenant"), {"tenant": tenant}).scalars())
        baseline_idempotency = set(connection.execute(text("select id from maintenance.idempotency_records where tenant_id=:tenant"), {"tenant": tenant}).scalars())
    def cleanup_created_records():
        with repo.engine.begin() as connection:
            order_ids = list(set(connection.execute(text("select id from maintenance.orders where tenant_id=:tenant"), {"tenant": tenant}).scalars()) - baseline_orders)
            if order_ids:
                connection.execute(text("delete from maintenance.material_request_lines where tenant_id=:tenant and material_request_id in (select id from maintenance.material_requests where tenant_id=:tenant and order_id=any(:ids))"), {"tenant": tenant, "ids": order_ids})
                connection.execute(text("delete from maintenance.material_requests where tenant_id=:tenant and order_id=any(:ids)"), {"tenant": tenant, "ids": order_ids})
                connection.execute(text("delete from maintenance.time_entries where tenant_id=:tenant and order_id=any(:ids)"), {"tenant": tenant, "ids": order_ids})
                connection.execute(text("delete from maintenance.assignments where tenant_id=:tenant and order_id=any(:ids)"), {"tenant": tenant, "ids": order_ids})
                connection.execute(text("delete from maintenance.orders where tenant_id=:tenant and id=any(:ids)"), {"tenant": tenant, "ids": order_ids})
            audit_ids = list(set(connection.execute(text("select id from maintenance.audit_events where tenant_id=:tenant"), {"tenant": tenant}).scalars()) - baseline_audits)
            if audit_ids:connection.execute(text("delete from maintenance.audit_events where tenant_id=:tenant and id=any(:ids)"), {"tenant": tenant, "ids": audit_ids})
            idempotency_ids = list(set(connection.execute(text("select id from maintenance.idempotency_records where tenant_id=:tenant"), {"tenant": tenant}).scalars()) - baseline_idempotency)
            if idempotency_ids:connection.execute(text("delete from maintenance.idempotency_records where tenant_id=:tenant and id=any(:ids)"), {"tenant": tenant, "ids": idempotency_ids})
    yield repo, tenant
    cleanup_created_records()
    repo.engine.dispose()


def facility(code="MT-TEST"):
    return schemas.OrderCreate(code=code, target_type="facility", priority="high", title="Fuga hidraulica", description="Fuga visible en la linea", location="Edificio A")


def transition(name, worker=None):
    return schemas.TransitionRequest(transition=name, assigned_worker_id=worker)


def test_corrective_order_closes_with_worker_time_and_evidence(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility(), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, "create-maintenance-1", "hash-create", "usr_maintenance_integration_test")
    repo.transition(tenant, order["id"], transition("request"), None, "request-maintenance-1", "hash-request", "usr_test")
    worker = {"id": "hrw_test", "full_name": "Tecnico Prueba"}
    repo.transition(tenant, order["id"], transition("assign", worker["id"]), worker, "assign-maintenance-1", "hash-assign", "usr_test")
    repo.transition(tenant, order["id"], transition("start"), None, "start-maintenance-1", "hash-start", "usr_test")
    started = datetime.now(timezone.utc) - timedelta(hours=1)
    entry = repo.create_time(tenant, order["id"], schemas.TimeEntryCreate(worker_id=worker["id"], started_at=started, ended_at=started + timedelta(minutes=45)), worker, "time-maintenance-1", "hash-time", "usr_test")
    assert entry["minutes"] == 45
    repo.update_order(tenant, order["id"], schemas.OrderUpdate(diagnosis="Sello danado", work_performed="Cambio de sello", verification_notes="Sin fuga tras prueba"), "update-maintenance-1", "hash-update", "usr_test")
    resolved = repo.transition(tenant, order["id"], transition("resolve"), None, "resolve-maintenance-1", "hash-resolve", "usr_test")
    closed = repo.transition(tenant, order["id"], transition("close"), None, "close-maintenance-1", "hash-close", "usr_test")
    assert resolved["status"] == "resolved"
    assert closed["status"] == "closed"
    assert closed["total_minutes"] == 45


def test_material_request_persists_multiple_lines_and_reconciles(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility("MT-PARTS"), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, "create-parts-1", "hash-create", "usr_test")
    repo.transition(tenant, order["id"], transition("request"), None, "request-parts-1", "hash-request", "usr_test")
    worker = {"id": "hrw_test", "full_name": "Tecnico Prueba"}
    repo.transition(tenant, order["id"], transition("assign", worker["id"]), worker, "assign-parts-1", "hash-assign", "usr_test")
    payload = schemas.MaterialRequestCreate(warehouse_id="wh_parts", lines=[schemas.MaterialLine(item_id="itm_a", quantity=2, unit_code="PZA"), schemas.MaterialLine(item_id="itm_b", quantity=1, unit_code="PZA")])
    request, plan = repo.prepare_material_request(tenant, order["id"], payload, {"warehouse_name": "Refacciones", "items": [{"code": "A", "name": "Sello"}, {"code": "B", "name": "Banda"}]}, "material-maintenance-1", "hash-material", "usr_test")
    completed = repo.complete_material_request(tenant, request["id"], "material-maintenance-1", [{"id": "res_a", "unit_cost_snapshot": 10}, {"id": "res_b", "unit_cost_snapshot": 20}])
    assert len(plan) == 2
    assert completed["status"] == "reserved"
    with repo.material_command_lock(tenant,request["id"]):
        _,issue_plan=repo.prepare_warehouse_issue(tenant,request["id"],"usr_warehouse")
        repo.complete_warehouse_issue(tenant,request["id"],[(issue_plan[0]["id"],{"id":"mov_a"}),(issue_plan[1]["id"],{"id":"mov_b"})],None,"usr_warehouse")
    assert repo.get_order(tenant, order["id"])["material_requests"][0]["status"] == "issued"


def test_idempotency_and_tenant_isolation(repository):
    repo, tenant = repository
    payload = facility("MT-IDEMP")
    snapshots = {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}
    first = repo.create_order(tenant, payload, snapshots, "create-idempotent-1", "same", "usr_test")
    replay = repo.create_order(tenant, payload, snapshots, "create-idempotent-1", "same", "usr_test")
    assert replay["id"] == first["id"]
    assert repo.get_order("ten_other", first["id"]) is None
    with pytest.raises(ValueError, match="idempotency_key_reused"):
        repo.create_order(tenant, payload, snapshots, "create-idempotent-1", "different", "usr_test")


def test_only_one_active_order_can_block_a_machine(repository):
    repo, tenant = repository
    snapshots = {"machine_code_snapshot": "M-01", "machine_name_snapshot": "Torno", "source_production_order_code_snapshot": None}
    first = schemas.OrderCreate(code="MT-MACHINE-1", target_type="production_machine", production_machine_id="maq_test", priority="critical", title="Torno detenido", description="No inicia", location="Linea 1")
    second = first.model_copy(update={"code": "MT-MACHINE-2"})
    order = repo.create_order(tenant, first, snapshots, "machine-create-1", "machine-one", "usr_test")
    repo.transition(tenant, order["id"], transition("request"), None, "machine-request-1", "machine-request", "usr_test")
    competing = repo.create_order(tenant, second, snapshots, "machine-create-2", "machine-two", "usr_test")
    with pytest.raises(ValueError, match="maintenance_order_conflict"):
        repo.transition(tenant, competing["id"], transition("request"), None, "machine-request-2", "machine-request-two", "usr_test")


def test_reassignment_keeps_one_primary_worker(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility("MT-ASSIGN"), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, "create-assignment-maintenance", "hash-create", "usr_maintenance_integration_test")
    repo.transition(tenant, order["id"], transition("request"), None, "request-assignment-maintenance", "hash-request", "usr_test")
    first = {"id": "hrw_first", "full_name": "Tecnico Uno"}
    second = {"id": "hrw_second", "full_name": "Tecnico Dos"}
    repo.transition(tenant, order["id"], transition("assign", first["id"]), first, "assign-first-maintenance", "hash-first", "usr_test")
    repo.transition(tenant, order["id"], transition("assign", second["id"]), second, "assign-second-maintenance", "hash-second", "usr_test")
    with repo.engine.connect() as connection:
        primary = connection.execute(text("select count(*) from maintenance.assignments where tenant_id=:tenant and order_id=:order and is_primary"), {"tenant": tenant, "order": order["id"]}).scalar_one()
    assert primary == 1
    assert repo.get_order(tenant, order["id"])["assigned_worker_id"] == second["id"]


def test_partial_material_cancellation_is_retryable(repository):
    repo, tenant = repository
    order = repo.create_order(tenant, facility("MT-CANCEL-PARTS"), {"machine_code_snapshot": None, "machine_name_snapshot": None, "source_production_order_code_snapshot": None}, "create-cancel-maintenance", "hash-create", "usr_maintenance_integration_test")
    repo.transition(tenant, order["id"], transition("request"), None, "request-cancel-maintenance", "hash-request", "usr_test")
    worker = {"id": "hrw_test", "full_name": "Tecnico Prueba"}
    repo.transition(tenant, order["id"], transition("assign", worker["id"]), worker, "assign-cancel-maintenance", "hash-assign", "usr_test")
    payload = schemas.MaterialRequestCreate(warehouse_id="wh_parts", lines=[schemas.MaterialLine(item_id="itm_a", quantity=2, unit_code="PZA"), schemas.MaterialLine(item_id="itm_b", quantity=1, unit_code="PZA")])
    request, _ = repo.prepare_material_request(tenant, order["id"], payload, {"warehouse_name": "Refacciones", "items": [{"code": "A", "name": "Sello"}, {"code": "B", "name": "Banda"}]}, "material-cancel-maintenance", "hash-material", "usr_test")
    repo.complete_material_request(tenant, request["id"], "material-cancel-maintenance", [{"id": "res_a", "unit_cost_snapshot": 10}, {"id": "res_b", "unit_cost_snapshot": 20}])
    _, plan = repo.prepare_material_cancellation(tenant, request["id"], "cancel-parts-maintenance", "hash-cancel", "usr_test")
    failed = repo.complete_material_cancellation(tenant, request["id"], "cancel-parts-maintenance", [plan[0]["line_id"]], "dependency_unavailable", "usr_test")
    assert failed["status"] == "needs_reconciliation"
    assert failed["pending_operation"] == "cancel"
    _, retry = repo.prepare_material_reconciliation(tenant, request["id"], "reconcile-parts-maintenance", "hash-reconcile", "usr_test")
    completed = repo.complete_material_reconciliation(tenant, request["id"], "reconcile-parts-maintenance", [{"id": retry[0]["reservation_id"]}], None, "usr_test")
    assert completed["status"] == "cancelled"
    assert completed["pending_operation"] is None


def pending_material(repo,tenant,suffix):
    order=repo.create_order(tenant,facility("MT-"+suffix),{"machine_code_snapshot":None,"machine_name_snapshot":None,"source_production_order_code_snapshot":None},suffix+"-create","create","usr_test")
    repo.transition(tenant,order["id"],transition("request"),None,suffix+"-request","request","usr_test")
    worker={"id":"hrw_test","full_name":"Tecnico Prueba"}
    repo.transition(tenant,order["id"],transition("assign",worker["id"]),worker,suffix+"-assign","assign","usr_test")
    payload=schemas.MaterialRequestCreate(warehouse_id="wh_parts",lines=[schemas.MaterialLine(item_id="itm_a",quantity=2,unit_code="PZA"),schemas.MaterialLine(item_id="itm_b",quantity=1,unit_code="PZA")])
    req,_=repo.prepare_material_request(tenant,order["id"],payload,{"warehouse_name":"Refacciones","items":[{"code":"A","name":"Sello"},{"code":"B","name":"Banda"}]},suffix+"-materials","materials","usr_test")
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
        _,plan=repo.prepare_warehouse_issue(tenant,req["id"],"usr_warehouse")
        partial=repo.complete_warehouse_issue(tenant,req["id"],[(plan[0]["id"],{"id":"mov_a"})],"dependency_unavailable","usr_warehouse")
    assert partial["status"]=="needs_reconciliation"
    assert partial["lines"][0]["line_status"]=="issued"
    with pytest.raises(ValueError,match="material_request_not_cancellable"):
        repo.prepare_material_cancellation(tenant,req["id"],"warehouse-cancel","cancel","usr_test")
    with repo.material_command_lock(tenant,req["id"]):
        _,retry=repo.prepare_warehouse_issue(tenant,req["id"],"usr_warehouse")
        assert [line["id"] for line in retry]==[plan[1]["id"]]
        done=repo.complete_warehouse_issue(tenant,req["id"],[(retry[0]["id"],{"id":"mov_b"})],None,"usr_warehouse")
        assert repo.prepare_warehouse_issue(tenant,req["id"],"usr_warehouse")[1] is None
    assert done["status"]=="issued"
    assert req["id"] not in [x["id"] for x in repo.list_warehouse_material_requests(tenant,100)[0]]
    with repo.engine.connect() as c:
        audit=c.execute(text("select actor_id,payload from maintenance.audit_events where tenant_id=:t and entity_id=:r and action='maintenance.material_request.authorize_issue' order by occurred_at limit 1"),{"t":tenant,"r":req["id"]}).mappings().one()
        assert audit["actor_id"]=="usr_warehouse"
        assert audit["payload"]["recipient_worker_id"]=="hrw_test"


def test_warehouse_lock_rejects_competing_commands_and_recovers_after_crash(repository):
    from concurrent.futures import ThreadPoolExecutor
    repo,tenant=repository
    _,req=pending_material(repo,tenant,"WH-LOCK")
    def competing():
        with repo.material_command_lock(tenant,req["id"]):return "unexpected"
    with repo.material_command_lock(tenant,req["id"]):
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(ValueError,match="command_in_progress"):pool.submit(competing).result()
        _,plan=repo.prepare_warehouse_issue(tenant,req["id"],"usr_warehouse")
    # Simulate process loss after durable preparation, before receiving Inventory responses.
    with repo.material_command_lock(tenant,req["id"]):
        _,retry=repo.prepare_warehouse_issue(tenant,req["id"],"usr_warehouse")
        assert [x["id"] for x in retry]==[x["id"] for x in plan]
    assert repo.prepare_warehouse_issue("ten_other",req["id"],"usr_test")== (None,None)


def test_warehouse_rejection_preserves_reason_and_releases_without_issue(repository):
    repo,tenant=repository
    _,req=pending_material(repo,tenant,"WH-REJECT")
    with repo.material_command_lock(tenant,req["id"]):
        repo.record_warehouse_rejection(tenant,req["id"],"Solicitud duplicada","warehouse-reject","hash-reason","usr_warehouse")
        repo.record_warehouse_rejection(tenant,req["id"],"Solicitud duplicada","warehouse-reject","hash-reason","usr_warehouse")
        with pytest.raises(ValueError,match="idempotency_key_reused"):
            repo.record_warehouse_rejection(tenant,req["id"],"Otro motivo","warehouse-reject","different","usr_warehouse")
        _,plan=repo.prepare_material_cancellation(tenant,req["id"],"warehouse-reject","cancel","usr_warehouse")
        cancelled=repo.complete_material_cancellation(tenant,req["id"],"warehouse-reject",[x["line_id"] for x in plan],None,"usr_warehouse")
    assert cancelled["status"]=="cancelled"
    assert all(x["inventory_movement_id"] is None for x in cancelled["lines"])
    with pytest.raises(ValueError,match="material_request_not_issuable"):
        repo.prepare_warehouse_issue(tenant,req["id"],"usr_warehouse")
    with repo.engine.connect() as c:
        reasons=c.execute(text("select payload->>'reason' from maintenance.audit_events where tenant_id=:t and entity_id=:r and action='maintenance.material_request.reject'"),{"t":tenant,"r":req["id"]}).scalars().all()
        assert reasons==["Solicitud duplicada"]
