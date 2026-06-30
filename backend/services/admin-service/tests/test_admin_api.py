from fastapi.testclient import TestClient

from app.main import app
from app.repositories import get_admin_repository
from app.schemas import EntitlementRead, PolicyDecision, RoleRead, TenantRead, UserRead


TENANT_ID = "ten_demo"
USER_ID = "usr_demo"


class FakeAdminRepository:
    def get_tenant(self, tenant_id: str):
        if tenant_id != TENANT_ID:
            return None
        return TenantRead(
            id=TENANT_ID,
            slug="demo-qa",
            legal_name="ERClave Demo QA",
            commercial_name="ERClave Demo QA",
            status="active",
            plan_id="qa-demo",
            timezone="America/Mexico_City",
            locale="es-MX",
        )

    def list_entitlements(self, tenant_id: str):
        return [
            EntitlementRead(module_code="admin", status="active", limits={}),
            EntitlementRead(module_code="production", status="active", limits={}),
        ]

    def evaluate_policy(self, tenant_id: str, actor_id: str, module: str, resource: str, action: str):
        allowed = tenant_id == TENANT_ID and actor_id == USER_ID and f"{module}.{resource}.{action}" == "admin.tenant.read"
        return PolicyDecision(
            allowed=allowed,
            reason="allowed" if allowed else "permission_not_granted",
            matched_permissions=["admin.tenant.read"] if allowed else [],
        )

    def list_users(self, tenant_id: str, limit: int = 50):
        return [
            UserRead(
                id=USER_ID,
                email="admin.qa@erclave.local",
                display_name="Admin QA ERClave",
                status="active",
                roles=["owner"],
            )
        ]

    def list_roles(self, tenant_id: str, limit: int = 50):
        return [RoleRead(id="rol_demo", code="owner", name="Owner", status="active")]


def client_with_fake_repo() -> TestClient:
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_get_tenant_returns_tenant():
    client = client_with_fake_repo()

    response = client.get(f"/v1/tenants/{TENANT_ID}")

    assert response.status_code == 200
    assert response.json()["data"]["slug"] == "demo-qa"


def test_get_tenant_returns_404_for_missing_tenant():
    client = client_with_fake_repo()

    response = client.get("/v1/tenants/ten_missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "tenant_not_found"


def test_list_tenant_entitlements_returns_modules():
    client = client_with_fake_repo()

    response = client.get(f"/v1/tenants/{TENANT_ID}/entitlements")

    assert response.status_code == 200
    assert [item["module_code"] for item in response.json()["data"]] == ["admin", "production"]


def test_policy_evaluate_returns_allowed_decision():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/policy/evaluate",
        json={
            "tenant_id": TENANT_ID,
            "actor_id": USER_ID,
            "module": "admin",
            "resource": "tenant",
            "action": "read",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["allowed"] is True
    assert response.json()["data"]["matched_permissions"] == ["admin.tenant.read"]


def test_list_users_requires_tenant_header():
    client = client_with_fake_repo()

    response = client.get("/v1/users")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


def test_list_users_returns_users_for_tenant():
    client = client_with_fake_repo()

    response = client.get("/v1/users", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"][0]["email"] == "admin.qa@erclave.local"


def test_list_roles_returns_roles_for_tenant():
    client = client_with_fake_repo()

    response = client.get("/v1/roles", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "owner"
