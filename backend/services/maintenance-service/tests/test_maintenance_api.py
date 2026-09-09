from contextlib import nullcontext
from decimal import Decimal
from io import BytesIO
import json
import pytest
import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from erclave_common.errors import ErclaveError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]

main = importlib.import_module("app.main")
repositories = importlib.import_module("app.repositories")
authorities = importlib.import_module("app.authorities")
authorization = importlib.import_module("app.authorization")
from erclave_common.config import Settings

TENANT = "ten_demo"


class FakeRepository:
    def __init__(self):
        self.order = None

    def list_orders(self, tenant, q=None, status=None, limit=100):
        return [self.order] if tenant == TENANT and self.order else []

    def get_order(self, tenant, order_id):
        return self.order if tenant == TENANT and self.order and self.order["id"] == order_id else None

    def create_order(self, tenant, payload, snapshots, key, request_hash, actor):
        self.order = {
            "id": "mwo_1", "code": payload.code, "status": "draft",
            "production_machine_id": payload.production_machine_id,
            "source_production_order_id": payload.source_production_order_id,
            "integration_status": "not_required", "integration_operation": None, "total_minutes": 0,
            "diagnosis": None, "work_performed": None, "verification_notes": None,
            "material_requests": [], **snapshots,
        }
        return self.order

    def transition(self, tenant, order_id, payload, worker, key, request_hash, actor):
        targets = {"request": "requested", "assign": "assigned", "start": "in_progress", "resolve": "resolved", "reopen": "in_progress", "cancel": "cancelled"}
        self.order["status"] = targets[payload.transition]
        if payload.transition in {"request", "reopen"}:
            self.order["integration_status"] = "processing"
            self.order["integration_operation"] = "block"
        elif payload.transition in {"resolve", "cancel"}:
            self.order["integration_status"] = "processing"
            self.order["integration_operation"] = "release"
        if worker:
            self.order["assigned_worker_id"] = worker["id"]
        return self.order

    def set_order_integration(self, tenant, order_id, status, error=None, actor="system"):
        self.order["integration_status"] = status
        self.order["integration_error"] = error
        if status == "completed":
            self.order["integration_operation"] = None
        return self.order

    def material_command_lock(self, tenant, request_id):
        return nullcontext()

    def material_creation_lock(self, tenant, order_id):
        return nullcontext()

    def list_warehouse_material_requests(self, tenant, limit=50, offset=0):
        return ([self.material] if tenant == TENANT and self.material else []), False

    def get_material_request(self,tenant,request_id):
        return self.material if tenant==TENANT and self.material and self.material["id"]==request_id else None

    def record_warehouse_rejection(self,tenant,request_id,reason,key,request_hash,actor):
        if self.material["pending_operation"]=="issue" or self.material["status"]=="issued":raise ValueError("material_request_not_cancellable")
        self.material["rejection_reason"]=reason

    def prepare_material_cancellation(self,tenant,request_id,key,request_hash,actor):
        return self.material,[{"line_id":line["id"],"reservation_id":line["reservation_id"]} for line in self.material["lines"]]

    def complete_material_cancellation(self,tenant,request_id,key,released,error,actor):
        self.material["status"]="needs_reconciliation" if error else "cancelled"
        return self.material

    def prepare_warehouse_issue(self, tenant, request_id, actor):
        value = self.material if tenant == TENANT and self.material and self.material["id"] == request_id else None
        if not value: return None, None
        if value["status"] == "issued": return value, None
        if value["status"] != "reserved" and value.get("pending_operation") != "issue":
            raise ValueError("material_request_not_issuable")
        value["pending_operation"] = "issue"
        return value, [line for line in value["lines"] if line["line_status"] == "reserved"]

    def complete_warehouse_issue(self, tenant, request_id, results, error, actor):
        for line_id, movement in results:
            line = next(line for line in self.material["lines"] if line["id"] == line_id)
            line.update(line_status="issued", inventory_movement_id=movement["id"])
        self.material.update(status="needs_reconciliation" if error else "issued", pending_operation="issue" if error else None)
        return self.material

    def prepare_material_request(self, tenant, order_id, payload, snapshots, key, request_hash, actor):
        return {"id": "mmr_1", "order_id": order_id}, [
            {"line_id": f"line_{index}", "item_id": line.item_id, "quantity": line.quantity, "unit_code": line.unit_code}
            for index, line in enumerate(payload.lines, 1)
        ]

    def complete_material_request(self, tenant, request_id, key, reservations, error=None, actor="system"):
        return {"id": request_id, "status": "reserved" if not error else "needs_reconciliation", "reservation_count": len(reservations)}


class FakeAuthority:
    def __init__(self):
        self.blocked = []
        self.consumed = []
        self.reserved = []
        self.fail_block_once = False

    def machine(self, tenant, machine_id, authorization):
        return {"id": machine_id, "code": "M-01", "name": "Torno"}

    def production_order(self, tenant, order_id, authorization):
        return {"id": order_id, "code": "OP-01", "status": "in_progress", "resources": [{"resource_type": "machine", "resource_ref_id": "maq_1"}]}

    def workers(self, tenant, authorization):
        return [{"id": "hrw_1", "full_name": "Ana Garcia"}]

    def block_machine(self, tenant, machine_id, order_id, source_id, authorization, key):
        if self.fail_block_once:
            self.fail_block_once = False
            raise ErclaveError("maintenance_dependency_unavailable", "Unavailable", status_code=503)
        self.blocked.append((machine_id, order_id, source_id))
        return {"status": "maintenance"}

    def release_machine(self, *args):
        return {"status": "active"}

    def warehouse(self, tenant, warehouse_id, authorization):
        return {"id": warehouse_id, "name": "Refacciones", "type": "spare_parts", "status": "active"}

    def item(self, tenant, item_id, authorization):
        return {"id": item_id, "code": item_id.upper(), "name": item_id, "base_unit": "PZA", "status": "active"}

    def reserve(self, tenant, order_id, request_id, line, warehouse_id, authorization, key):
        self.reserved.append(line["item_id"])
        return {"id": f"res_{line['item_id']}", "unit_cost_snapshot": 10}

    def consume(self, *args):
        self.consumed.append(args)
        return {"id": "mov_1"}

    def release_reservation(self, *args):
        return {"status": "released"}


repo = FakeRepository()
authority = FakeAuthority()


def client():
    main.app.dependency_overrides[repositories.get_maintenance_repository] = lambda: repo
    main.app.dependency_overrides[authorities.get_maintenance_authority_client] = lambda: authority
    return TestClient(main.app)


def headers(command=False):
    value = {"X-Tenant-Id": TENANT, "X-Actor-Id": "usr_demo"}
    if command:
        value["Idempotency-Key"] = "maintenance-test-key"
    return value


def setup_function():
    repo.order = None
    repo.material = None
    authority.blocked.clear()
    authority.consumed.clear()
    authority.reserved.clear()
    authority.fail_block_once = False


def teardown_function():
    main.app.dependency_overrides.clear()


def production_payload():
    return {"code": "MT-001", "target_type": "production_machine", "production_machine_id": "maq_1", "source_type": "production_order", "source_production_order_id": "pro_1", "priority": "high", "title": "Torno detenido", "description": "No inicia", "location": "Linea 1"}


def test_create_requires_idempotency_key():
    assert client().post("/v1/maintenance/orders", headers=headers(), json=production_payload()).status_code == 400


def test_production_order_creation_captures_snapshots_and_blocks_on_request():
    created = client().post("/v1/maintenance/orders", headers=headers(True), json=production_payload())
    assert created.status_code == 201
    assert created.json()["data"]["machine_name_snapshot"] == "Torno"
    requested = client().post("/v1/maintenance/orders/mwo_1/transitions", headers=headers(True), json={"transition": "request"})
    assert requested.status_code == 200
    assert requested.json()["data"]["integration_status"] == "completed"
    assert authority.blocked == [("maq_1", "mwo_1", "pro_1")]


def test_resolve_validation_happens_before_inventory_side_effects():
    client().post("/v1/maintenance/orders", headers=headers(True), json=production_payload())
    repo.order["status"] = "in_progress"
    response = client().post("/v1/maintenance/orders/mwo_1/transitions", headers=headers(True), json={"transition": "resolve"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "maintenance_resolution_evidence_required"
    assert authority.consumed == []


def test_material_request_reserves_every_line():
    client().post("/v1/maintenance/orders", headers=headers(True), json=production_payload())
    repo.order["status"] = "assigned"
    response = client().post("/v1/maintenance/orders/mwo_1/material-requests", headers=headers(True), json={"warehouse_id": "wh_1", "lines": [{"item_id": "itm_1", "quantity": 2, "unit_code": "PZA"}, {"item_id": "itm_2", "quantity": 1, "unit_code": "PZA"}]})
    assert response.status_code == 201
    assert response.json()["data"]["reservation_count"] == 2
    assert authority.reserved == ["itm_1", "itm_2"]


def test_failed_machine_block_can_be_reconciled_without_repeating_transition():
    client().post("/v1/maintenance/orders", headers=headers(True), json=production_payload())
    authority.fail_block_once = True
    requested = client().post("/v1/maintenance/orders/mwo_1/transitions", headers=headers(True), json={"transition": "request"})
    assert requested.status_code == 200
    assert requested.json()["data"]["integration_status"] == "needs_reconciliation"
    reconciled = client().post("/v1/maintenance/orders/mwo_1/reconcile", headers=headers(True))
    assert reconciled.status_code == 200
    assert reconciled.json()["data"]["integration_status"] == "completed"
    assert authority.blocked == [("maq_1", "mwo_1", "pro_1")]


def test_manual_source_rejects_production_order_reference():
    payload = production_payload() | {"source_type": "manual"}
    response = client().post("/v1/maintenance/orders", headers=headers(True), json=payload)
    assert response.status_code == 422


def test_maintenance_transition_requires_the_exact_action_permission():
    class SessionClient:
        def get_context(self, tenant_id, bearer):
            return {"tenant":{"id":TENANT,"status":"active"},"user":{"id":"usr_auth"},"active_modules":["maintenance"],"permissions":["maintenance.order.assign"]}
    repo.order={"id":"mwo_1","status":"draft","production_machine_id":None,"source_production_order_id":None,"integration_status":"not_required","integration_operation":None,"total_minutes":0,"diagnosis":None,"work_performed":None,"verification_notes":None,"material_requests":[]}
    main.app.dependency_overrides[authorization.get_settings]=lambda:Settings(auth_mode="firebase")
    main.app.dependency_overrides[authorization.get_admin_session_client]=lambda:SessionClient()
    response=client().post("/v1/maintenance/orders/mwo_1/transitions",headers={**headers(True),"Authorization":"Bearer test-token"},json={"transition":"request"})
    assert response.status_code==403
    assert response.json()["error"]["details"]["permission"]=="maintenance.order.request"


def test_recovery_requires_its_own_permission():
    h=warehouse_session(['inventory.movement.create','maintenance.material_request.cancel'])
    response=client().post('/v1/maintenance/material-requests/mmr_1/reconcile',headers=h)
    assert response.status_code==403
    assert response.json()['error']['details']['permission']=='maintenance.material_request.reconcile'


def test_real_authority_encodes_database_decimal_reservation(monkeypatch):
    calls=[]
    def send(request,timeout):
        calls.append(json.loads(request.data))
        return BytesIO(b'{"data":{"id":"res_decimal"}}')
    monkeypatch.setattr(authorities.request,'urlopen',send)
    real=authorities.MaintenanceAuthorityClient(Settings())
    real.reserve(TENANT,'order','request',{'item_id':'item','line_id':'line','quantity':Decimal('1.125000'),'unit_code':'H87'},'warehouse',None,'stable-key')
    assert calls[0]['quantity']==1.125
    assert calls[0]['source']=={'type':'maintenance_order','id':'order','line_id':'line'}


def test_invalid_payload_encoding_becomes_recoverable_error_before_http(monkeypatch):
    def forbidden(*args,**kwargs):pytest.fail('No HTTP call expected')
    monkeypatch.setattr(authorities.request,'urlopen',forbidden)
    real=authorities.MaintenanceAuthorityClient(Settings())
    with pytest.raises(ErclaveError) as result:real._call('http://127.0.0.1:8004',TENANT,None,'POST',{'quantity':float('nan')})
    assert result.value.code=='maintenance_dependency_unavailable'


def material_fixture():
    repo.material = {"id":"mmr_1","order_id":"mwo_1","status":"reserved","pending_operation":None,"lines":[
        {"id":"line_a","reservation_id":"res_a","quantity":2,"line_status":"reserved"},
        {"id":"line_b","reservation_id":"res_b","quantity":1,"line_status":"reserved"}]}
    return repo.material


def warehouse_session(permissions, modules=("maintenance","inventory")):
    class SessionClient:
        def get_context(self, tenant_id, bearer):
            return {"tenant":{"id":TENANT,"status":"active"},"user":{"id":"usr_warehouse"},"active_modules":list(modules),"permissions":permissions}
    main.app.dependency_overrides[authorization.get_settings]=lambda:Settings(auth_mode="firebase")
    main.app.dependency_overrides[authorization.get_admin_session_client]=lambda:SessionClient()
    return {**headers(True),"Authorization":"Bearer test-token"}


def test_warehouse_can_read_queue_without_maintenance_order_read():
    material_fixture()
    h=warehouse_session(["inventory.movement.read"])
    assert client().get("/v1/maintenance/warehouse-material-requests",headers=h).json()["data"][0]["id"]=="mmr_1"
    assert client().get("/v1/maintenance/orders",headers=h).status_code==403
    assert client().post("/v1/maintenance/material-requests/mmr_1/issue",headers=h).status_code==403
    assert authority.consumed==[]


def test_warehouse_issue_is_idempotent_and_maintenance_resolve_cannot_issue():
    material_fixture()
    h=warehouse_session(["maintenance.order.resolve"])
    assert client().post("/v1/maintenance/material-requests/mmr_1/issue",headers=h).status_code==403
    h=warehouse_session(["inventory.movement.create"])
    for _ in range(2):
        response=client().post("/v1/maintenance/material-requests/mmr_1/issue",headers=h)
        assert response.status_code==200
        assert response.json()["data"]["status"]=="issued"
    assert len(authority.consumed)==2
    assert authority.consumed[0][-1]=="maintenance-mwo_1-consume-line_a"
    assert client().post("/v1/maintenance/material-requests/mmr_other/issue",headers=h).status_code==404


def test_warehouse_issue_retries_only_unconfirmed_lines():
    material_fixture()
    calls=[]
    class PartialAuthority(FakeAuthority):
        def consume(self, tenant, reservation_id, quantity, token, key):
            calls.append(reservation_id)
            if calls==["res_a","res_b"]:raise ErclaveError("maintenance_dependency_unavailable","Offline",status_code=503)
            return {"id":"mov_"+reservation_id}
    main.app.dependency_overrides[authorities.get_maintenance_authority_client]=lambda:PartialAuthority()
    # client() installs the ordinary authority; override after constructing it.
    c=client()
    main.app.dependency_overrides[authorities.get_maintenance_authority_client]=lambda:PartialAuthority()
    h=warehouse_session(["inventory.movement.create"])
    first=c.post("/v1/maintenance/material-requests/mmr_1/issue",headers=h)
    assert first.json()["data"]["status"]=="needs_reconciliation"
    second=c.post("/v1/maintenance/material-requests/mmr_1/issue",headers=h)
    assert second.json()["data"]["status"]=="issued"
    assert calls==["res_a","res_b","res_b"]


def test_resolve_blocks_reserved_parts_without_consumption():
    client().post("/v1/maintenance/orders",headers=headers(True),json=production_payload())
    repo.order.update(status="in_progress",diagnosis="Sello",work_performed="Cambio",verification_notes="Prueba",total_minutes=5,material_requests=[material_fixture()])
    response=client().post("/v1/maintenance/orders/mwo_1/transitions",headers=headers(True),json={"transition":"resolve"})
    assert response.status_code==409
    assert response.json()["error"]["code"]=="maintenance_materials_not_reconciled"
    assert authority.consumed==[]
    repo.material["status"]="issued"
    assert client().post("/v1/maintenance/orders/mwo_1/transitions",headers=headers(True),json={"transition":"resolve"}).status_code==200
    assert authority.consumed==[]


def test_warehouse_issue_requires_both_modules_and_rejects_partial_payload():
    material_fixture()
    h=warehouse_session(["inventory.movement.create"],modules=("maintenance",))
    assert client().post("/v1/maintenance/material-requests/mmr_1/issue",headers=h).status_code==403
    h=warehouse_session(["inventory.movement.create"])
    assert client().post("/v1/maintenance/material-requests/mmr_1/issue",headers=h,json={"quantity":1}).status_code==422
    assert authority.consumed==[]


def test_warehouse_rejection_requires_reason_and_cannot_reject_issued_parts():
    material_fixture()
    h=warehouse_session(["inventory.movement.create"])
    for reason in ["  ","ab","x"*501]:
        assert client().post("/v1/maintenance/material-requests/mmr_1/reject",headers=h,json={"reason":reason}).status_code==422
    response=client().post("/v1/maintenance/material-requests/mmr_1/reject",headers=h,json={"reason":"  Solicitud duplicada  "})
    assert response.status_code==200
    assert response.json()["data"]["status"]=="cancelled"
    assert response.json()["data"]["rejection_reason"]=="Solicitud duplicada"
    assert authority.consumed==[]
    repo.material.update(status="issued",pending_operation=None)
    assert client().post("/v1/maintenance/material-requests/mmr_1/reject",headers=h,json={"reason":"Duplicada"}).status_code==409
