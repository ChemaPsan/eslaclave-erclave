from fastapi.testclient import TestClient

import app.api as admin_api
from app.main import app
from app.auth import AuthenticatedActor, get_authenticated_actor
from app.repositories import get_admin_repository
from erclave_common.config import Settings, get_settings
from app.schemas import (
    EntitlementRead,
    PermissionRead,
    PolicyDecision,
    RoleRead,
    SessionBranchRead,
    SessionContextRead,
    SessionScopeRead,
    SettingRead,
    TenantRead,
    UserRead,
)


TENANT_ID = "ten_demo"
USER_ID = "usr_demo"
ROLE_ID = "rol_demo"
PERMISSION_ID = "per_demo"


def test_private_network_cors_preflight_is_allowed_for_firebase_host():
    client = TestClient(app)
    response = client.options(
        "/v1/provisioning/tenant-onboarding",
        headers={
            "Origin": "https://erclave.web.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,idempotency-key,x-correlation-id",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://erclave.web.app"
    assert response.headers["access-control-allow-private-network"] == "true"


class FakeAdminRepository:
    session_permissions = ["admin.tenant.read", "production.product_service.read"]

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

    def create_tenant(
        self,
        slug: str,
        commercial_name: str,
        legal_name: str | None,
        plan_id: str | None,
        timezone: str,
        locale: str,
        source: dict,
        organization_profile: dict | None,
        idempotency_key: str,
        correlation_id: str,
    ):
        assert organization_profile is not None
        assert organization_profile["corporate"]["commercial_name"] == commercial_name
        return TenantRead(
            id="ten_new",
            slug=slug.lower(),
            legal_name=legal_name,
            commercial_name=commercial_name,
            status="provisioning",
            plan_id=plan_id,
            timezone=timezone,
            locale=locale,
        )

    def onboard_tenant(
        self,
        slug: str,
        commercial_name: str,
        legal_name: str | None,
        plan_id: str | None,
        timezone: str,
        locale: str,
        source: dict,
        owner: dict,
        organization_profile: dict | None,
        modules: list[dict],
        idempotency_key: str,
        correlation_id: str,
    ):
        assert source == {"type": "manual", "id": "qa-onboarding"}
        assert owner["email"] == "owner.nuevo@cliente.com"
        assert owner["branch_ids"] == ["*"]
        assert modules[0]["module_code"] == "admin"
        tenant = TenantRead(
            id="ten_new",
            slug=slug.lower(),
            legal_name=legal_name,
            commercial_name=commercial_name,
            status="active",
            plan_id=plan_id,
            timezone=timezone,
            locale=locale,
        )
        owner_user = UserRead(
            id="usr_owner_new",
            email=owner["email"],
            display_name=owner["display_name"],
            status=owner["status"],
            roles=["owner"],
        )
        return {
            "tenant": tenant,
            "owner": owner_user,
            "entitlements": [EntitlementRead(module_code="admin", status="active", limits={})],
            "organization": SettingRead(
                key="organization.profile",
                module_code="admin",
                value=organization_profile or {"corporate": {"commercial_name": commercial_name}, "legal_entities": [], "branches": []},
            ),
            "session_context": None,
        }

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
            roles=[RoleRead(id=ROLE_ID, code="owner", name="Owner", status="active", permissions=[])],
            entitlements=self.list_entitlements(tenant_id),
            entitlement_limits={"admin": {}, "production": {}},
            permissions=self.session_permissions,
            active_modules=["admin", "production"],
            scope=SessionScopeRead(
                branch_ids=["suc_demo"],
                branches=[
                    SessionBranchRead(
                        id="suc_demo",
                        name="Matriz QA",
                        code="MTZ",
                        status="active",
                    )
                ],
                all_branches=True,
            ),
        )

    def get_session_context_by_email(self, tenant_id: str, email: str):
        if email.lower() != "admin.qa@erclave.local":
            return None
        return self.get_session_context(tenant_id, USER_ID)

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

    def list_settings(self, tenant_id: str, module_code: str | None = None):
        if tenant_id != TENANT_ID:
            return []
        settings = [
            SettingRead(
                key="organization.profile",
                module_code="admin",
                value={"corporate": {"commercial_name": "ERClave Demo QA"}},
            )
        ]
        return [item for item in settings if module_code is None or item.module_code == module_code]

    def upsert_setting(
        self,
        tenant_id: str,
        key: str,
        module_code: str | None,
        value: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID:
            return None
        return SettingRead(key=key, module_code=module_code, value=value)

    def create_legal_entity(self, tenant_id: str, payload: dict, idempotency_key: str, correlation_id: str):
        if tenant_id != TENANT_ID:
            return None
        return {"id": "rso_demo", "status": "active", **payload}

    def update_legal_entity(
        self,
        tenant_id: str,
        legal_entity_id: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID or legal_entity_id != "rso_demo":
            return None
        return {"id": legal_entity_id, "status": "active", "legal_name": "Razon social QA", **payload}

    def set_legal_entity_status(
        self,
        tenant_id: str,
        legal_entity_id: str,
        status: str,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID or legal_entity_id != "rso_demo":
            return None
        return {"id": legal_entity_id, "legal_name": "Razon social QA", "status": status}

    def create_branch(self, tenant_id: str, payload: dict, idempotency_key: str, correlation_id: str):
        if tenant_id != TENANT_ID:
            return None
        return {"id": "suc_demo", "status": "active", **payload}

    def update_branch(self, tenant_id: str, branch_id: str, payload: dict, idempotency_key: str, correlation_id: str):
        if tenant_id != TENANT_ID or branch_id != "suc_demo":
            return None
        return {"id": branch_id, "status": "active", "name": "Matriz QA", **payload}

    def set_branch_status(self, tenant_id: str, branch_id: str, status: str, idempotency_key: str, correlation_id: str):
        if tenant_id != TENANT_ID or branch_id != "suc_demo":
            return None
        return {"id": branch_id, "name": "Matriz QA", "status": status}

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

    def get_user_for_tenant(self, tenant_id: str, user_id: str):
        if tenant_id != TENANT_ID or user_id != USER_ID:
            return None
        return self.list_users(tenant_id)[0]

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

    def delete_user(self, tenant_id: str, user_id: str, idempotency_key: str, correlation_id: str):
        if tenant_id != TENANT_ID or user_id != USER_ID:
            return None
        return UserRead(
            id=USER_ID,
            email="admin.qa@erclave.local",
            display_name="Admin QA ERClave",
            status="deleted",
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
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="demo")
    return TestClient(app)


class FakeAdminRepositoryWithEntitlementPermission(FakeAdminRepository):
    session_permissions = ["admin.tenant.read", "admin.entitlement.manage", "production.product_service.read"]


class FakeAdminRepositoryWithPolicyPermission(FakeAdminRepository):
    session_permissions = ["admin.tenant.read", "internal.policy.evaluate", "production.product_service.read"]


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


def test_get_tenant_requires_bearer_token_in_firebase_mode():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    client = TestClient(app)

    response = client.get(f"/v1/tenants/{TENANT_ID}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_required"


def test_create_tenant_accepts_initial_organization_profile():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/tenants",
        headers={"Idempotency-Key": "test-tenant-create-001"},
        json={
            "slug": "Nuevo-Cliente",
            "commercial_name": "Nuevo Cliente",
            "legal_name": "Nuevo Cliente S.A. de C.V.",
            "plan_id": "qa-demo",
            "source": {"type": "provisioning", "id": "req_001"},
            "organization_profile": {
                "corporate": {
                    "commercial_name": "Nuevo Cliente",
                    "legal_name": "Nuevo Cliente S.A. de C.V.",
                    "tax_id": "",
                    "phone": "",
                    "contact_name": "",
                    "contact_email": "",
                    "contact_phone": "",
                    "contact_position": "",
                },
                "legal_entities": [],
                "branches": [],
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["slug"] == "nuevo-cliente"
    assert response.json()["data"]["status"] == "provisioning"


def test_onboard_tenant_creates_tenant_owner_modules_and_organization():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/provisioning/tenant-onboarding",
        headers={"Idempotency-Key": "test-tenant-onboarding-001"},
        json={
            "slug": "Cliente-Nuevo",
            "commercial_name": "Cliente Nuevo",
            "legal_name": "Cliente Nuevo S.A. de C.V.",
            "plan_id": "qa-demo",
            "source": {"type": "manual", "id": "qa-onboarding"},
            "owner": {
                "email": "owner.nuevo@cliente.com",
                "display_name": "Owner Cliente Nuevo",
            },
            "organization_profile": {
                "corporate": {
                    "commercial_name": "Cliente Nuevo",
                    "legal_name": "Cliente Nuevo S.A. de C.V.",
                    "tax_id": "",
                    "phone": "",
                    "contact_name": "Owner Cliente Nuevo",
                    "contact_email": "owner.nuevo@cliente.com",
                    "contact_phone": "",
                    "contact_position": "Direccion",
                },
                "legal_entities": [],
                "branches": [],
            },
            "modules": [{"module_code": "admin", "status": "active", "limits": {}}],
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["tenant"]["slug"] == "cliente-nuevo"
    assert response.json()["data"]["owner"]["email"] == "owner.nuevo@cliente.com"
    assert response.json()["data"]["owner"]["roles"] == ["owner"]
    assert response.json()["data"]["entitlements"][0]["module_code"] == "admin"
    assert response.json()["data"]["organization"]["key"] == "organization.profile"
    assert response.json()["data"]["invitation"] == {
        "provider": "demo",
        "email": "owner.nuevo@cliente.com",
        "email_sent": False,
        "reset_link": None,
        "delivery": "disabled",
    }


def test_onboard_tenant_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/provisioning/tenant-onboarding",
        json={
            "slug": "Cliente-Nuevo",
            "commercial_name": "Cliente Nuevo",
            "source": {"type": "manual", "id": "qa-onboarding"},
            "owner": {"email": "owner.nuevo@cliente.com", "display_name": "Owner Cliente Nuevo"},
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_onboard_tenant_sends_firebase_invitation_when_enabled(monkeypatch):
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        auth_mode="firebase",
        firebase_web_api_key="fake-api-key",
        backoffice_admin_emails="backoffice@erclave.local",
    )
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-backoffice",
        email="backoffice@erclave.local",
        name="Backoffice",
    )
    calls = {"ensured": [], "invited": []}

    def fake_ensure_firebase_user(email, display_name, settings):
        calls["ensured"].append((email, display_name, settings.auth_mode))

    def fake_create_firebase_password_invitation(email, settings):
        calls["invited"].append((email, settings.firebase_web_api_key))
        return {
            "provider": "firebase",
            "email": email.lower(),
            "email_sent": True,
            "reset_link": None,
            "delivery": "firebase_email",
        }

    monkeypatch.setattr(admin_api, "ensure_firebase_user", fake_ensure_firebase_user)
    monkeypatch.setattr(admin_api, "create_firebase_password_invitation", fake_create_firebase_password_invitation)
    client = TestClient(app)

    response = client.post(
        "/v1/provisioning/tenant-onboarding",
        headers={"Idempotency-Key": "test-tenant-onboarding-firebase-001"},
        json={
            "slug": "Cliente-Nuevo",
            "commercial_name": "Cliente Nuevo",
            "source": {"type": "manual", "id": "qa-onboarding"},
            "owner": {"email": "owner.nuevo@cliente.com", "display_name": "Owner Cliente Nuevo"},
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["invitation"]["email_sent"] is True
    assert calls["ensured"] == [("owner.nuevo@cliente.com", "Owner Cliente Nuevo", "firebase")]
    assert calls["invited"] == [("owner.nuevo@cliente.com", "fake-api-key")]


def test_onboard_tenant_requires_backoffice_allowlist_in_firebase_mode(monkeypatch):
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        auth_mode="firebase",
        backoffice_admin_emails="backoffice@erclave.local",
    )
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="externo@cliente.com",
        name="Externo",
    )
    monkeypatch.setattr(admin_api, "ensure_firebase_user", lambda *args, **kwargs: None)
    client = TestClient(app)

    response = client.post(
        "/v1/provisioning/tenant-onboarding",
        headers={"Idempotency-Key": "test-tenant-onboarding-denied-001"},
        json={
            "slug": "Cliente-Nuevo",
            "commercial_name": "Cliente Nuevo",
            "source": {"type": "manual", "id": "qa-onboarding"},
            "owner": {"email": "owner.nuevo@cliente.com", "display_name": "Owner Cliente Nuevo"},
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "backoffice_admin_required"


def test_get_session_context_returns_tenant_user_modules_and_permissions():
    client = client_with_fake_repo()

    response = client.get("/v1/session/context", headers={"X-Tenant-Id": TENANT_ID, "X-Actor-Id": USER_ID})

    assert response.status_code == 200
    assert response.json()["data"]["tenant"]["id"] == TENANT_ID
    assert response.json()["data"]["user"]["id"] == USER_ID
    assert response.json()["data"]["roles"][0]["code"] == "owner"
    assert response.json()["data"]["active_modules"] == ["admin", "production"]
    assert response.json()["data"]["entitlement_limits"] == {"admin": {}, "production": {}}
    assert response.json()["data"]["scope"]["branches"][0]["id"] == "suc_demo"
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


def test_get_session_context_uses_firebase_actor_email_when_enabled():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="admin.qa@erclave.local",
        name="Admin QA",
    )
    client = TestClient(app)

    response = client.get("/v1/session/context", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"]["user"]["id"] == USER_ID


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


def test_upsert_tenant_entitlement_denies_missing_firebase_permission():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="admin.qa@erclave.local",
        name="Admin QA",
    )
    client = TestClient(app)

    response = client.put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-denied"},
        json={"status": "inactive", "limits": {"locations": 2}, "source": "manual"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_upsert_tenant_entitlement_allows_firebase_permission():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepositoryWithEntitlementPermission()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="admin.qa@erclave.local",
        name="Admin QA",
    )
    client = TestClient(app)

    response = client.put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-allowed"},
        json={"status": "inactive", "limits": {"locations": 2}, "source": "manual"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"


def test_list_settings_returns_admin_settings():
    client = client_with_fake_repo()

    response = client.get("/v1/settings", headers={"X-Tenant-Id": TENANT_ID}, params={"module_code": "admin"})

    assert response.status_code == 200
    assert response.json()["data"][0]["key"] == "organization.profile"


def test_upsert_setting_returns_updated_setting():
    client = client_with_fake_repo()

    response = client.put(
        "/v1/settings/organization.profile",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-setting-001"},
        json={
            "module_code": "admin",
            "value": {
                "corporate": {
                    "commercial_name": "ERClave Demo QA",
                    "contact_name": "Administracion",
                }
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["module_code"] == "admin"
    assert response.json()["data"]["value"]["corporate"]["contact_name"] == "Administracion"


def test_create_legal_entity_returns_created_item():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/organization/legal-entities",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-rso-create-001"},
        json={"legal_name": "Razon social QA", "tax_id": "RFC000000XXX"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["id"] == "rso_demo"
    assert response.json()["data"]["status"] == "active"


def test_update_legal_entity_returns_updated_item():
    client = client_with_fake_repo()

    response = client.patch(
        "/v1/organization/legal-entities/rso_demo",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-rso-update-001"},
        json={"contact_name": "Administracion"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["contact_name"] == "Administracion"


def test_deactivate_legal_entity_returns_inactive_item():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/organization/legal-entities/rso_demo/deactivate",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-rso-deactivate-001"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"


def test_create_branch_returns_created_item():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/organization/branches",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-branch-create-001"},
        json={"name": "Matriz QA", "code": "MTZ"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["id"] == "suc_demo"
    assert response.json()["data"]["status"] == "active"


def test_update_branch_returns_updated_item():
    client = client_with_fake_repo()

    response = client.patch(
        "/v1/organization/branches/suc_demo",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-branch-update-001"},
        json={"phone": "+52 55 0000 0000"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["phone"] == "+52 55 0000 0000"


def test_deactivate_branch_returns_inactive_item():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/organization/branches/suc_demo/deactivate",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-branch-deactivate-001"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"


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


def test_policy_evaluate_rejects_actor_mismatch_in_firebase_mode():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepositoryWithPolicyPermission()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="admin.qa@erclave.local",
        name="Admin QA",
    )
    client = TestClient(app)

    response = client.post(
        "/v1/policy/evaluate",
        json={
            "tenant_id": TENANT_ID,
            "actor_id": "usr_other",
            "module": "admin",
            "resource": "tenant",
            "action": "read",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "actor_mismatch"


def test_list_users_requires_tenant_header():
    client = client_with_fake_repo()

    response = client.get("/v1/users")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


def test_list_users_requires_bearer_token_in_firebase_mode():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    client = TestClient(app)

    response = client.get("/v1/users", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_required"


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


def test_delete_user_returns_deleted_user():
    client = client_with_fake_repo()

    response = client.delete(
        f"/v1/users/{USER_ID}",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-delete-001"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "deleted"


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
