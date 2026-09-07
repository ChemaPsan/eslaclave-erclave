import importlib
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from erclave_common.errors import ErclaveError
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]

main = importlib.import_module("app.main")
repositories = importlib.import_module("app.repositories")
authorities = importlib.import_module("app.authorities")

TENANT = "ten_purchasing_api"


class FakeRepository:
    def __init__(self):
        self.order = None
        self.receipt = None
        self.completed_movements = None

    def create_requisition(self, tenant, payload, key, request_hash, actor, snapshots):
        assert tenant == TENANT
        return {
            "id": "pre_service",
            "code": payload.code,
            "status": "draft",
            "lines": [
                {
                    "id": "prl_service",
                    "line_type": line.line_type,
                    "inventory_item_ref_id": line.inventory_item_id,
                    "description": line.description,
                    "quantity": line.quantity,
                    "unit_code": line.unit_code,
                }
                for line in payload.lines
            ],
        }

    def get_order(self, tenant, order_id):
        return self.order if tenant == TENANT and self.order and self.order["id"] == order_id else None

    def issue_order(self, tenant, order_id, key, request_hash, actor):
        self.order = {**self.order, "status": "issued"}
        return self.order

    def prepare_receipt(self, tenant, payload, key, request_hash, actor):
        self.receipt = {
            "id": "rcp_service",
            "code": payload.code,
            "purchase_order_id": payload.purchase_order_id,
            "status": "processing",
            "lines": [{"id": "rcl_service", "reconciliation_status": "processing"}],
        }
        return self.receipt, [{
            "receipt_line_id": "rcl_service",
            "order_line_id": "pol_service",
            "line_type": "service",
            "inventory_item_id": None,
            "quantity": payload.lines[0].quantity,
            "warehouse_id": None,
            "unit_code": "E48",
            "unit_price": 500,
            "received_at": payload.received_at.isoformat(),
            "inventory_idempotency_key": "purchase-receipt-rcl_service",
        }]

    def complete_receipt(self, tenant, receipt, plan, movements, key, actor, error=None, operation="receipt.create"):
        self.completed_movements = movements
        return {**receipt, "status": "completed", "lines": [{"id": "rcl_service", "reconciliation_status": "completed", "inventory_movement_ref_id": None}]}


class FakeAuthority:
    def __init__(self):
        self.units = []
        self.inventory_calls = []
        self.warehouse_calls = []
        self.invalid_units = set()

    def require_unit(self, tenant, code, authorization):
        self.units.append((tenant, code))
        if code in self.invalid_units:
            raise ErclaveError("purchase_unit_not_found", "Unit is inactive.", status_code=422)
        return {"code": code, "status": "active"}

    def item(self, *args):
        self.inventory_calls.append(args)
        return {"id": "itm_1", "status": "active", "base_unit": "H87"}

    def warehouse(self, *args):
        self.warehouse_calls.append(args)
        raise AssertionError("A service receipt must not query Inventory warehouses.")

    def receive(self, *args):
        self.inventory_calls.append(args)
        raise AssertionError("A service receipt must not create Inventory movements.")


repo = FakeRepository()
authority = FakeAuthority()


def client():
    main.app.dependency_overrides[repositories.get_purchasing_repository] = lambda: repo
    main.app.dependency_overrides[authorities.get_purchasing_authority_client] = lambda: authority
    return TestClient(main.app)


def headers(command=False):
    result = {"X-Tenant-Id": TENANT, "X-Actor-Id": "usr_purchasing"}
    if command:
        result["Idempotency-Key"] = "purchasing-service-test"
    return result


def setup_function():
    repo.order = None
    repo.receipt = None
    repo.completed_movements = None
    authority.units.clear()
    authority.inventory_calls.clear()
    authority.warehouse_calls.clear()
    authority.invalid_units.clear()


def teardown_function():
    main.app.dependency_overrides.clear()


def service_line():
    return {"line_type": "service", "description": "  Diagnostico especializado  ", "quantity": 1, "unit_code": " e48 "}


def test_service_requisition_uses_active_admin_unit_without_inventory_lookup():
    response = client().post(
        "/v1/purchasing/requisitions",
        headers=headers(True),
        json={"code": "REQ-SRV-1", "required_date": date.today().isoformat(), "lines": [service_line()]},
    )

    assert response.status_code == 201
    assert response.json()["data"]["lines"][0] == {
        "id": "prl_service",
        "line_type": "service",
        "inventory_item_ref_id": None,
        "description": "Diagnostico especializado",
        "quantity": "1",
        "unit_code": "E48",
    }
    assert authority.units == [(TENANT, "E48")]
    assert authority.inventory_calls == []


def test_service_requisition_rejects_inactive_unit_with_stable_error():
    authority.invalid_units.add("E48")
    response = client().post(
        "/v1/purchasing/requisitions",
        headers=headers(True),
        json={"code": "REQ-SRV-2", "required_date": date.today().isoformat(), "lines": [service_line()]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "purchase_unit_not_found"
    assert authority.inventory_calls == []


def test_issue_revalidates_service_unit_without_inventory_lookup():
    repo.order = {
        "id": "por_service",
        "status": "draft",
        "lines": [{"line_type": "service", "inventory_item_ref_id": None, "unit_code": "E48"}],
    }

    response = client().post("/v1/purchasing/orders/por_service/issue", headers=headers(True))

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "issued"
    assert authority.units == [(TENANT, "E48")]
    assert authority.inventory_calls == []


def test_issue_requires_idempotency_before_authority_lookup():
    repo.order = {
        "id": "por_service",
        "status": "draft",
        "lines": [{"line_type": "service", "inventory_item_ref_id": None, "unit_code": "E48"}],
    }

    response = client().post("/v1/purchasing/orders/por_service/issue", headers=headers())

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"
    assert authority.units == []


def test_service_receipt_completes_without_warehouse_or_inventory_movement():
    response = client().post(
        "/v1/purchasing/receipts",
        headers=headers(True),
        json={
            "code": "REC-SRV-1",
            "purchase_order_id": "por_service",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "lines": [{"order_line_id": "pol_service", "quantity": 1}],
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "completed"
    assert response.json()["data"]["lines"][0]["inventory_movement_ref_id"] is None
    assert repo.completed_movements == [{"id": None}]
    assert authority.warehouse_calls == []
    assert authority.inventory_calls == []


def test_service_receipt_rejects_warehouse_before_inventory_lookup():
    repo.order = {
        "id": "por_service",
        "status": "issued",
        "lines": [{"id": "pol_service", "line_type": "service", "inventory_item_ref_id": None, "unit_code": "E48"}],
    }
    response = client().post(
        "/v1/purchasing/receipts",
        headers=headers(True),
        json={
            "code": "REC-SRV-WH",
            "purchase_order_id": "por_service",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "lines": [{"order_line_id": "pol_service", "quantity": 1, "warehouse_id": "wh_forbidden"}],
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "service_warehouse_not_allowed"
    assert authority.warehouse_calls == []
    assert authority.inventory_calls == []


def test_inventory_line_reports_conditional_module_requirement(monkeypatch):
    value = authorities.PurchasingAuthorityClient(SimpleNamespace(
        inventory_service_url="http://inventory.local",
        admin_service_url="http://admin.local",
        authorization_timeout_seconds=1,
    ))

    def rejected(*args, **kwargs):
        raise ErclaveError("purchasing_dependency_rejected", "Rejected", status_code=422, details={"status": 403})

    monkeypatch.setattr(value, "_call", rejected)
    with pytest.raises(ErclaveError) as captured:
        value.item(TENANT, "itm_1", "Bearer local")
    assert captured.value.code == "purchasing_inventory_required"
    assert captured.value.status_code == 422
