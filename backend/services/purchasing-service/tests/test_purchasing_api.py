import importlib
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from erclave_common.errors import ErclaveError
from erclave_common.organization_client import OrganizationAccess
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in list(sys.modules):
    if name == "app" or name.startswith("app."):
        del sys.modules[name]

main = importlib.import_module("app.main")
repositories = importlib.import_module("app.repositories")
authorities = importlib.import_module("app.authorities")

TENANT = "ten_739ee59d765d5e14818674800d"
DIVISION = "div_purchasing_test"
CONTEXT = {"division_ref_id": DIVISION, "society_ref_id": "soc_purchasing_test",
           "division_code": "TEST", "division_name": "Purchasing test", "cost_currency": "MXN"}


class FakeRepository:
    def __init__(self):
        self.order = None
        self.receipt = None
        self.completed_movements = None

    def create_requisition(self, tenant, payload, key, request_hash, actor, snapshots, *, context, organization_access, code_mode=None):
        assert tenant == TENANT
        assert context == CONTEXT
        assert organization_access.division(DIVISION)["society_id"] == CONTEXT["society_ref_id"]
        assert code_mode == "managed"
        return {
            "id": "pre_service",
            "code": payload.code,
            "status": "draft",
            "organization_context": context,
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

    def issue_order(self, tenant, order_id, key, request_hash, actor, *, organization_access):
        assert organization_access.division(DIVISION)["society_id"] == CONTEXT["society_ref_id"]
        self.order = {**self.order, "status": "issued"}
        return self.order

    def receipt_replay(self, tenant, key, request_hash):
        return None

    def document_replay(self, tenant, operation, key, request_hash, scope):
        assert tenant == TENANT
        assert scope.tenant_id == TENANT
        return None

    def prepare_receipt(self, tenant, payload, key, request_hash, actor, snapshots=None, *, organization_access, code_mode=None):
        assert organization_access.division(DIVISION)["society_id"] == CONTEXT["society_ref_id"]
        assert snapshots == {}
        assert code_mode == "managed"
        self.receipt = {
            "id": "rcp_service",
            "code": payload.code,
            "purchase_order_id": payload.purchase_order_id,
            "status": "pending_confirmation",
            "organization_context": self.order["organization_context"],
            "lines": [{"id": "rcl_service", "reconciliation_status": "pending"}],
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
        self.catalog_calls = []
        self.inventory_calls = []
        self.warehouse_calls = []
        self.invalid_units = set()
        self.revoked = False
        self.code_calls = []

    def allocate_code(self, tenant, document_type, manual_code, authorization, command_key):
        self.code_calls.append((tenant, document_type, manual_code, command_key))
        return {"code": "ADM-000001", "mode": "managed"}

    def organization_access(self, tenant, permission, authorization, actor):
        assert tenant == TENANT
        return OrganizationAccess(tenant, actor, (permission,), () if self.revoked else (
            {"id": DIVISION, "code": "TEST", "name": "Purchasing test", "society_id": CONTEXT["society_ref_id"]},
        ), False, False, authorization, ({"id": CONTEXT["society_ref_id"], "base_currency": "MXN"},))

    def list_catalog(self, tenant, catalog, authorization):
        self.catalog_calls.append((tenant, catalog, authorization))
        values = {
            "currencies": [
                {"code": "MXN", "name_es": "Peso mexicano", "name_en": "Mexican peso", "status": "active"},
                {"code": "CAD", "name_es": "Dólar canadiense", "name_en": "Canadian dollar", "status": "active"},
            ],
            "payment_terms": [
                {"code": "cash", "name_es": "Contado", "name_en": "Cash", "status": "active"},
                {"code": "credit_45", "name_es": "Crédito 45 días", "name_en": "Net 45", "status": "active"},
            ],
        }
        return values[catalog]

    def require_unit(self, tenant, code, authorization):
        self.units.append((tenant, code))
        if code in self.invalid_units:
            raise ErclaveError("purchase_unit_not_found", "Unit is inactive.", status_code=422)
        return {"code": code, "status": "active"}

    def require_catalog(self, tenant, catalog, code, authorization):
        return next(row for row in self.list_catalog(tenant, catalog, authorization) if row["code"] == code)

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
    authority.catalog_calls.clear()
    authority.inventory_calls.clear()
    authority.warehouse_calls.clear()
    authority.invalid_units.clear()
    authority.revoked = False
    authority.code_calls.clear()


def teardown_function():
    main.app.dependency_overrides.clear()


def service_line():
    return {"line_type": "service", "description": "  Diagnostico especializado  ", "quantity": 1, "unit_code": " e48 "}


@pytest.mark.parametrize('action,target', [('submit', 'submitted'), ('approve', 'approved')])
def test_requisition_transition_needs_own_scope_without_inventory_read(action, target, monkeypatch):
    current = {'id': 'req_physical', 'organization_context': CONTEXT,
               'lines': [{'line_type': 'inventory_item', 'inventory_item_ref_id': 'item_scoped'}]}
    monkeypatch.setattr(repo, 'get_requisition', lambda tenant, id_: current, raising=False)
    def transition(tenant, id_, status, reason, key, request_hash, actor, *, organization_access):
        assert tenant == TENANT and status == target
        assert organization_access.permissions == ('purchasing.requisition.' + action,)
        organization_access.division(DIVISION)
        return {**current, 'status': status}
    monkeypatch.setattr(repo, 'transition_requisition', transition, raising=False)
    response = client().post('/v1/purchasing/requisitions/req_physical/' + action, headers=headers(True))
    assert response.status_code == 200
    assert response.json()['data']['status'] == target
    assert not authority.inventory_calls and not authority.catalog_calls


def test_reference_data_returns_active_admin_catalogs_for_supplier_forms():
    response = client().get("/v1/purchasing/reference-data", headers=headers())

    assert response.status_code == 200
    assert [item["code"] for item in response.json()["data"]["currencies"]] == ["MXN", "CAD"]
    assert [item["code"] for item in response.json()["data"]["payment_terms"]] == ["cash", "credit_45"]
    assert authority.catalog_calls == [
        (TENANT, "currencies", None),
        (TENANT, "payment_terms", None),
    ]


def test_service_requisition_uses_active_admin_unit_without_inventory_lookup():
    response = client().post(
        "/v1/purchasing/requisitions",
        headers=headers(True),
        json={"code": "REQ-SRV-1", "division_ref_id": DIVISION, "required_date": date.today().isoformat(), "lines": [service_line()]},
    )

    assert response.status_code == 201
    assert response.json()["data"]["organization_context"] == CONTEXT
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
    assert response.json()["data"]["code"] == "ADM-000001"
    assert authority.code_calls == [(TENANT, "purchasing.requisition", "REQ-SRV-1", "purchasing-service-test")]


def test_service_requisition_rejects_inactive_unit_with_stable_error():
    authority.invalid_units.add("E48")
    response = client().post(
        "/v1/purchasing/requisitions",
        headers=headers(True),
        json={"code": "REQ-SRV-2", "division_ref_id": DIVISION, "required_date": date.today().isoformat(), "lines": [service_line()]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "purchase_unit_not_found"
    assert authority.inventory_calls == []
    assert authority.code_calls == []


def test_issue_revalidates_service_unit_without_inventory_lookup():
    repo.order = {
        "id": "por_service",
        "organization_context": CONTEXT,
        "currency": "MXN",
        "payment_terms": "cash",
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


def test_service_receipt_waits_for_requester_acceptance_without_inventory_movement():
    repo.order = {"id": "por_service", "status": "issued", "organization_context": CONTEXT,
                  "lines": [{"id": "pol_service", "line_type": "service", "inventory_item_ref_id": None, "unit_code": "E48"}]}
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
    assert response.json()["data"]["status"] == "pending_confirmation"
    assert response.json()["data"]["organization_context"] == CONTEXT
    assert repo.completed_movements is None
    assert authority.warehouse_calls == []
    assert authority.inventory_calls == []
    assert response.json()["data"]["code"] == "ADM-000001"


def test_service_receipt_rejects_warehouse_before_inventory_lookup():
    repo.order = {
        "id": "por_service",
        "organization_context": CONTEXT,
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


@pytest.mark.parametrize("revoked", [False, True])
def test_service_requisition_requires_explicit_authorized_division(revoked):
    authority.revoked = revoked
    payload = {"code": "REQ-SCOPE", "required_date": date.today().isoformat(), "lines": [service_line()]}
    if revoked:
        payload["division_ref_id"] = DIVISION
    response = client().post("/v1/purchasing/requisitions", headers=headers(True), json=payload)
    assert response.status_code == (403 if revoked else 422)
    assert response.json()["error"]["code"] == ("assignment_division_denied" if revoked else "purchasing_document_context_required")
    assert authority.inventory_calls == []
    assert authority.units == []


def test_inventory_line_reports_conditional_module_requirement(monkeypatch):
    value = authorities.PurchasingAuthorityClient(SimpleNamespace(
        environment="local",
        costing_service_url="http://127.0.0.1:8012",
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


def test_supplier_allocation_rejects_code_exceeding_local_limit(monkeypatch):
    value = authorities.PurchasingAuthorityClient(SimpleNamespace(
        environment="local",
        costing_service_url="http://127.0.0.1:8012",
        inventory_service_url="http://inventory.local",
        admin_service_url="http://admin.local",
        authorization_timeout_seconds=1,
    ))
    calls = []
    def allocated(url, tenant, authorization, method="GET", payload=None, key=None, preserve_codes=()):
        calls.append((url, tenant, method, payload, key))
        return {"document_type": "purchasing.supplier", "mode": "managed", "code": "S" * 41}
    monkeypatch.setattr(value, "_call", allocated)
    with pytest.raises(ErclaveError) as captured:
        value.allocate_code(TENANT, "purchasing.supplier", None, None, "supplier-key-123")
    assert captured.value.code == "purchasing_code_too_long"
    assert captured.value.status_code == 422
    assert calls[0][1:4] == (TENANT, "POST", {"manual_code": None})
    assert calls[0][4].startswith("purchasing-")
