import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from erclave_common.config import Settings


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        del sys.modules[module_name]

main = importlib.import_module("app.main")
repositories = importlib.import_module("app.repositories")
schemas = importlib.import_module("app.schemas")
authorization = importlib.import_module("app.authorization")

app = main.app
TENANT_ID = "ten_demo_qa"
OTHER_TENANT_ID = "ten_other"


class TrackingRepository:
    def __init__(self):
        self.calls = []

    def list_items(self, tenant_id, q=None):
        self.calls.append(("list_items", tenant_id, q))
        if tenant_id != TENANT_ID:
            raise AssertionError("A foreign tenant reached the inventory repository")
        return [
            schemas.ItemRead(
                id="itm_demo",
                code="demo",
                name="Articulo Demo QA",
                type="rawMaterial",
                base_unit="kg",
                inventory_policy="standard",
                status="active",
            )
        ]

    def list_balances(self, tenant_id, **options):
        self.calls.append(("list_balances", tenant_id, options))
        if tenant_id != TENANT_ID:
            raise AssertionError("A foreign tenant reached the balance repository")
        return [
            schemas.BalanceRead(
                inventory_item_id="itm_demo",
                item_code="demo",
                item_name="Articulo Demo QA",
                item_type="rawMaterial",
                item_status="active",
                inventory_policy="standard",
                warehouse_id="whs_demo",
                warehouse_code="demo",
                warehouse_name="Almacen Demo",
                on_hand_quantity=7,
                reserved_quantity=0,
                available_quantity=7,
                unit="kg",
                stock_status="normal",
            )
        ], schemas.Page(limit=options["limit"], has_more=False)

    def update_item(self, tenant_id, item_id, payload, key, request_hash, actor_id):
        self.calls.append(("update_item", tenant_id, item_id, payload.suggested_warehouse_id))
        if tenant_id != TENANT_ID:
            raise AssertionError("A foreign tenant reached item update")
        if payload.suggested_warehouse_id == "whs_other_tenant":
            return None
        return schemas.ItemRead(
            id=item_id,
            code="demo",
            name=payload.name or "Articulo Demo QA",
            type="rawMaterial",
            base_unit="kg",
            inventory_policy="standard",
            suggested_warehouse_id=payload.suggested_warehouse_id,
            status="active",
        )


class SessionClient:
    def __init__(self, context):
        self.context = context

    def get_context(self, tenant_id, authorization_header):
        assert authorization_header == "Bearer valid-demo-token"
        return self.context


def session_context(*, tenant_id=TENANT_ID, permissions=()):
    return {
        "tenant": {"id": tenant_id, "status": "active"},
        "user": {"id": "usr_demo_qa"},
        "active_modules": ["inventory"],
        "permissions": list(permissions),
    }


def make_client(repository, context):
    app.dependency_overrides[repositories.get_inventory_repository] = lambda: repository
    app.dependency_overrides[authorization.get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[authorization.get_admin_session_client] = lambda: SessionClient(context)
    return TestClient(app)


def auth_headers(tenant_id=TENANT_ID, command=False):
    headers = {
        "Authorization": "Bearer valid-demo-token",
        "X-Tenant-Id": tenant_id,
    }
    if command:
        headers["Idempotency-Key"] = "security-test-1"
    return headers


def teardown_function():
    app.dependency_overrides.clear()


def test_token_for_another_tenant_is_rejected_before_filtered_item_query():
    repository = TrackingRepository()
    client = make_client(
        repository,
        session_context(tenant_id=OTHER_TENANT_ID, permissions=("inventory.item.read",)),
    )

    response = client.get(
        "/v1/inventory/items?q=demo&status=active&limit=25&cursor=foreign-cursor",
        headers=auth_headers(),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "tenant_access_denied"
    assert repository.calls == []


def test_balance_read_requires_exact_permission():
    repository = TrackingRepository()
    client = make_client(repository, session_context(permissions=("inventory.item.read",)))

    response = client.get("/v1/inventory/balances", headers=auth_headers())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"
    assert response.json()["error"]["details"]["permission"] == "inventory.balance.read"
    assert repository.calls == []


def test_balance_filters_and_cursor_cannot_change_authorized_tenant_scope():
    repository = TrackingRepository()
    client = make_client(repository, session_context(permissions=("inventory.balance.read",)))

    response = client.get(
        "/v1/inventory/balances?warehouse_id=whs_other_tenant&inventory_item_id=itm_other&limit=10&cursor=foreign-cursor",
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["inventory_item_id"] == "itm_demo"
    assert repository.calls[0][0:2] == ("list_balances", TENANT_ID)
    assert repository.calls[0][2]["warehouse_id"] == "whs_other_tenant"
    assert repository.calls[0][2]["inventory_item_id"] == "itm_other"


def test_patch_item_rejects_suggested_warehouse_from_another_tenant():
    repository = TrackingRepository()
    client = make_client(repository, session_context(permissions=("inventory.item.update",)))

    response = client.patch(
        "/v1/inventory/items/itm_demo",
        headers=auth_headers(command=True),
        json={"suggested_warehouse_id": "whs_other_tenant"},
    )

    assert response.status_code in (404, 409)
    assert response.json()["error"]["code"] in ("item_not_found", "suggested_warehouse_invalid")
    assert repository.calls == [
        ("update_item", TENANT_ID, "itm_demo", "whs_other_tenant")
    ]
