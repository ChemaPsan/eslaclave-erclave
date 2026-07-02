from fastapi.testclient import TestClient

from app.main import app
from app.repositories import get_admin_repository
from app.schemas import EntitlementRead, PermissionRead, PolicyDecision, RoleRead, SessionContextRead, TenantRead, UserRead


TENANT_ID = "ten_demo"
USER_ID = "usr_demo"
ROLE_ID = "rol_demo"
PERMISSION_ID = "per_demo"


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

    def get_session_context(self, tenant_id: str, actor_id: str):
        if tenant_id != TENANT_ID or actor_id != USER_ID:
            return None
        return SessionContextRead(
            tenant=self.get_tenant(tenant_id),
            user=self.list_users(tenant_id)[0],
            entitlements=self.list_entitlements(tenant_id),
            permissions=["admin.tenant.read", "production.product_service.read"],
            active_modules=["admin", "production"],
        )

    def upsert_entitlement(
        self,
        tenant_id: str,
        module_code: str,
        status: str,
        limits: dict,
        source: str,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID:
            return None
        return EntitlementRead(module_code=module_code, status=status, limits=limits)

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

    def invite_user(
        self,
        tenant_id: str,
        email: str,
        display_name: str,
        role_ids: list[str],
        idempotency_key: str,
        correlation_id: str,
    ):
        return UserRead(
            id="usr_invited",
            email=email.lower(),
            display_name=display_name,
            status="invited",
            roles=["owner"] if role_ids else [],
        )

    def update_user(
        self,
        tenant_id: str,
        user_id: str,
        display_name: str | None,
        role_ids: list[str] | None,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID or user_id != USER_ID:
            return None
        return UserRead(
            id=USER_ID,
            email="admin.qa@erclave.local",
            display_name=display_name or "Admin QA ERClave",
            status="active",
            roles=["owner"] if role_ids else [],
        )

    def disable_user(self, tenant_id: str, user_id: str, idempotency_key: str, correlation_id: str):
        if tenant_id != TENANT_ID or user_id != USER_ID:
            return None
        return UserRead(
            id=USER_ID,
            email="admin.qa@erclave.local",
            display_name="Admin QA ERClave",
            status="disabled",
            roles=["owner"],
        )

    def list_roles(self, tenant_id: str, limit: int = 50):
        return [RoleRead(id=ROLE_ID, code="owner", name="Owner", status="active", permissions=["admin.tenant.read"])]

    def list_permissions(self, limit: int = 200):
        return [
            PermissionRead(
                id=PERMISSION_ID,
                code="admin.tenant.read",
                module_code="admin",
                resource="tenant",
                action="read",
                status="active",
            )
        ]

    def create_role(
        self,
        tenant_id: str,
        code: str,
        name: str,
        description: str | None,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID:
            return None
        return RoleRead(id="rol_new", code=code.lower(), name=name, status="active", permissions=[])

    def update_role(
        self,
        tenant_id: str,
        role_id: str,
        name: str | None,
        description: str | None,
        status: str | None,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID or role_id != ROLE_ID:
            return None
        return RoleRead(id=ROLE_ID, code="owner", name=name or "Owner", status=status or "active", permissions=["admin.tenant.read"])

    def replace_role_permissions(
        self,
        tenant_id: str,
        role_id: str,
        permission_ids: list[str],
        scope: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID or role_id != ROLE_ID or permission_ids != [PERMISSION_ID]:
            return None
        return RoleRead(id=ROLE_ID, code="owner", name="Owner", status="active", permissions=["admin.tenant.read"])


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


def test_get_session_context_returns_tenant_user_modules_and_permissions():
    client = client_with_fake_repo()

    response = client.get("/v1/session/context", headers={"X-Tenant-Id": TENANT_ID, "X-Actor-Id": USER_ID})

    assert response.status_code == 200
    assert response.json()["data"]["tenant"]["id"] == TENANT_ID
    assert response.json()["data"]["user"]["id"] == USER_ID
    assert response.json()["data"]["active_modules"] == ["admin", "production"]
    assert "production.product_service.read" in response.json()["data"]["permissions"]


def test_get_session_context_requires_actor_header():
    client = client_with_fake_repo()

    response = client.get("/v1/session/context", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "actor_required"


def test_get_session_context_returns_404_for_unknown_actor():
    client = client_with_fake_repo()

    response = client.get("/v1/session/context", headers={"X-Tenant-Id": TENANT_ID, "X-Actor-Id": "usr_missing"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "session_context_not_found"


def test_list_tenant_entitlements_returns_modules():
    client = client_with_fake_repo()

    response = client.get(f"/v1/tenants/{TENANT_ID}/entitlements")

    assert response.status_code == 200
    assert [item["module_code"] for item in response.json()["data"]] == ["admin", "production"]


def test_upsert_tenant_entitlement_returns_updated_module():
    client = client_with_fake_repo()

    response = client.put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-001"},
        json={"status": "inactive", "limits": {"locations": 2}, "source": "manual"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == {
        "module_code": "inventory",
        "status": "inactive",
        "limits": {"locations": 2},
    }


def test_upsert_tenant_entitlement_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        json={"status": "inactive", "limits": {"locations": 2}, "source": "manual"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_upsert_tenant_entitlement_returns_404_for_missing_tenant():
    client = client_with_fake_repo()

    response = client.put(
        "/v1/tenants/ten_missing/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-404"},
        json={"status": "active", "limits": {}, "source": "manual"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "tenant_not_found"


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


def test_invite_user_requires_tenant_header():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/users/invitations",
        json={"email": "new.qa@erclave.local", "display_name": "New QA", "role_ids": ["rol_demo"]},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


def test_invite_user_returns_created_user():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/users/invitations",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-invite-001"},
        json={"email": "New.QA@erclave.local", "display_name": "New QA", "role_ids": ["rol_demo"]},
    )

    assert response.status_code == 201
    assert response.json()["data"]["email"] == "new.qa@erclave.local"
    assert response.json()["data"]["status"] == "invited"
    assert response.json()["data"]["roles"] == ["owner"]


def test_update_user_returns_updated_user():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/users/{USER_ID}",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-update-001"},
        json={"display_name": "Admin QA Actualizado", "role_ids": ["rol_demo"]},
    )

    assert response.status_code == 200
    assert response.json()["data"]["display_name"] == "Admin QA Actualizado"


def test_disable_user_returns_disabled_membership():
    client = client_with_fake_repo()

    response = client.post(
        f"/v1/users/{USER_ID}/disable",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-disable-001"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "disabled"


def test_list_roles_returns_roles_for_tenant():
    client = client_with_fake_repo()

    response = client.get("/v1/roles", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "owner"
    assert response.json()["data"][0]["permissions"] == ["admin.tenant.read"]


def test_list_permissions_returns_permission_catalog():
    client = client_with_fake_repo()

    response = client.get("/v1/permissions")

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "admin.tenant.read"


def test_create_role_requires_tenant_header():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/roles",
        headers={"Idempotency-Key": "test-role-create-001"},
        json={"code": "supervisor", "name": "Supervisor"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


def test_create_role_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/roles",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"code": "supervisor", "name": "Supervisor"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_create_role_returns_created_role():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/roles",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-role-create-001"},
        json={"code": "Supervisor", "name": "Supervisor"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["code"] == "supervisor"


def test_update_role_returns_updated_role():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/roles/{ROLE_ID}",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-role-update-001"},
        json={"name": "Owner QA", "status": "active"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Owner QA"


def test_replace_role_permissions_returns_role_with_permissions():
    client = client_with_fake_repo()

    response = client.put(
        f"/v1/roles/{ROLE_ID}/permissions",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-role-permissions-001"},
        json={"permission_ids": [PERMISSION_ID], "scope": {}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["permissions"] == ["admin.tenant.read"]
