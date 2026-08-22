from datetime import date

from fastapi.testclient import TestClient

import app.api as admin_api
from app.main import app
from app.auth import AuthenticatedActor, get_authenticated_actor
from app.repositories import get_admin_repository
from erclave_common.config import Settings, get_settings
from app.schemas import (
    BackofficeTenantRead,
    BackofficeUsageDailyRead,
    BackofficeUsageSummaryRead,
    CodeSequenceAllocationRead,
    CodeSequenceRead,
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
    UnitOfMeasureRead,
)


TENANT_ID = "ten_demo"
USER_ID = "usr_demo"
ROLE_ID = "rol_demo"
PERMISSION_ID = "per_demo"


def test_private_network_cors_preflight_is_allowed_for_local_frontend():
    client = TestClient(app)
    response = client.options(
        "/v1/provisioning/tenant-onboarding",
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,idempotency-key,x-correlation-id",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4173"
    assert response.headers["access-control-allow-private-network"] == "true"


def test_local_api_rejects_qa_frontend_origin():
    client = TestClient(app)
    response = client.options(
        "/v1/provisioning/tenant-onboarding",
        headers={
            "Origin": "https://erclave.web.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,idempotency-key,x-correlation-id",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


class FakeAdminRepository:
    session_permissions = [
        "admin.tenant.read",
        "admin.role.read",
        "admin.role.create",
        "admin.role.update",
        "admin.role.permissions.manage",
        "production.product_service.read",
        "admin.unit.read",
        "admin.unit.create",
        "admin.unit.update",
        "production.order.create",
    ]

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

    def list_units_of_measure(self, tenant_id, include_inactive=False, q=None):
        return [UnitOfMeasureRead(id="uom_h87",code="H87",name_es="Pieza",name_en="Piece",symbol="pz",category="count",decimal_places=0,system_default=True,status="active")] if tenant_id==TENANT_ID else []

    def get_unit_of_measure(self, tenant_id, code, active_only=False):
        items=self.list_units_of_measure(tenant_id)
        return items[0] if items and code.upper()=="H87" else None

    def create_unit_of_measure(self, tenant_id, payload, idempotency_key, correlation_id, actor_email=None):
        return UnitOfMeasureRead(id="uom_custom",system_default=False,status="active",**payload.model_dump())

    def update_unit_of_measure(self, tenant_id, unit_id, payload, idempotency_key, correlation_id, actor_email=None):
        if unit_id!="uom_h87": return None
        return UnitOfMeasureRead(id="uom_h87",code="H87",name_es="Pieza",name_en="Piece",symbol="pz",category="count",decimal_places=0,system_default=True,status=payload.status or "active")

    def list_code_sequences(self, tenant_id):
        return [CodeSequenceRead(id="seq_op",document_type="production.order",module_code="production",name_es="Orden de produccion",name_en="Production order",prefix="OP",separator="-",next_number=7,padding=6,mode="managed",system_default=True,status="active")]

    def update_code_sequence(self, tenant_id, sequence_id, payload, idempotency_key, correlation_id, actor_email=None):
        if sequence_id != "seq_op": return None
        current=self.list_code_sequences(tenant_id)[0]
        return current.model_copy(update=payload.model_dump(exclude_none=True))

    def allocate_business_code(self, tenant_id, document_type, payload, idempotency_key, correlation_id, actor_email=None):
        if document_type != "production.order": return None
        return CodeSequenceAllocationRead(document_type=document_type,mode="managed",code="OP-000007",sequence_number=7)

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
            EntitlementRead(module_code="admin", status="active", tenant_enabled=True, effective_active=True, limits={}),
            EntitlementRead(module_code="production", status="active", tenant_enabled=True, effective_active=True, limits={}),
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

    def list_session_tenants_by_email(self, email: str):
        if email.lower() != "admin.qa@erclave.local":
            return []
        return [
            {
                "tenant": self.get_tenant(TENANT_ID),
                "user_status": "active",
                "membership_status": "active",
                "roles": ["owner"],
            }
        ]

    def list_backoffice_tenants(self, search: str | None = None, limit: int = 50):
        if search and search.lower() not in {"demo", "demo-qa", "erclave demo qa"}:
            return []
        return [
            BackofficeTenantRead(
                id=TENANT_ID,
                slug="demo-qa",
                legal_name="ERClave Demo QA",
                commercial_name="ERClave Demo QA",
                status="active",
                plan_id="qa-demo",
                timezone="America/Mexico_City",
                locale="es-MX",
                owner_email="admin.qa@erclave.local",
                active_memberships=1,
                total_memberships=1,
                modules=["admin", "production"],
                entitlements=self.list_entitlements(TENANT_ID),
                legal_entities_count=1,
                branches_count=1,
            )
        ]

    def update_backoffice_tenant(self, tenant_id, changes, idempotency_key, correlation_id, actor_email=None):
        tenant = self.get_tenant(tenant_id)
        if tenant is None:
            return None
        return TenantRead(**{**tenant.model_dump(), **changes})

    def set_backoffice_entitlement(self, tenant_id, module_code, status, limits, source, idempotency_key, correlation_id, actor_email=None):
        if tenant_id != TENANT_ID:
            return None
        return EntitlementRead(
            module_code=module_code,
            status=status,
            source=source,
            tenant_enabled=True,
            effective_active=status == "active",
            limits=limits,
        )

    def set_backoffice_tenant_status(
        self,
        tenant_id: str,
        new_status: str,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID:
            return None
        return BackofficeTenantRead(
            id=TENANT_ID,
            slug="demo-qa",
            legal_name="ERClave Demo QA",
            commercial_name="ERClave Demo QA",
            status=new_status,
            plan_id="qa-demo",
            timezone="America/Mexico_City",
            locale="es-MX",
            owner_email="admin.qa@erclave.local",
            active_memberships=0 if new_status == "suspended" else 1,
            total_memberships=1,
            modules=["admin", "production"],
        )

    def delete_backoffice_tenant(
        self,
        tenant_id: str,
        idempotency_key: str,
        correlation_id: str,
    ):
        if tenant_id != TENANT_ID:
            return None
        return {
            "tenant": self.get_tenant(tenant_id).model_dump(),
            "deleted": True,
            "removed_memberships": 1,
            "removed_global_users": 1,
            "firebase_emails": ["admin.qa@erclave.local"],
        }

    def list_backoffice_usage(self, from_date, to_date, tenant_id: str | None = None, limit: int = 200):
        if tenant_id and tenant_id != TENANT_ID:
            return [], BackofficeUsageSummaryRead()
        metrics = [
            BackofficeUsageDailyRead(
                tenant_id=TENANT_ID,
                tenant_slug="demo-qa",
                tenant_name="ERClave Demo QA",
                usage_date=date(2026, 7, 6),
                active_users=3,
                api_requests=128,
                storage_mb="42.50",
                estimated_cost_mxn="19.75",
                source="test",
            )
        ]
        return metrics[:limit], BackofficeUsageSummaryRead(
            tenants=1,
            days=1,
            active_users=3,
            api_requests=128,
            storage_mb="42.50",
            estimated_cost_mxn="19.75",
        )

    def update_entitlement_preference(
        self,
        tenant_id: str,
        module_code: str,
        enabled: bool,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ):
        if tenant_id != TENANT_ID:
            return None
        return EntitlementRead(module_code=module_code, status="active", tenant_enabled=enabled, effective_active=enabled, limits={})

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

    def get_role(self, tenant_id: str, role_id: str):
        if tenant_id != TENANT_ID or role_id != ROLE_ID:
            return None
        return RoleRead(id=ROLE_ID, code="owner", name="Owner", status="active", permissions=["admin.tenant.read"])

    def list_permissions(self, tenant_id: str, limit: int = 200):
        return [
            PermissionRead(
                id=PERMISSION_ID,
                code="admin.tenant.read",
                module_code="admin",
                resource="tenant",
                action="read",
                status="active",
                display_name_es="Ver tenants",
                display_name_en="View tenants",
                description_es="Permite consultar tenants.",
                description_en="Allows viewing tenants.",
                classification="tenant",
                assignable_to_tenant_role=True,
                risk_level="low",
                entitlement_status="active",
                available=True,
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
        assignments: list[dict],
        expected_revision: int,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ):
        if tenant_id != TENANT_ID or role_id != ROLE_ID or assignments != [{"permission_id": PERMISSION_ID, "scope": {}}]:
            return None
        return RoleRead(
            id=ROLE_ID,
            code="owner",
            name="Owner",
            status="active",
            permissions=["admin.tenant.read"],
            permission_revision=expected_revision + 1,
        )


def client_with_fake_repo() -> TestClient:
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="demo")
    return TestClient(app)


class FakeAdminRepositoryWithEntitlementPermission(FakeAdminRepository):
    session_permissions = ["admin.tenant.read", "admin.entitlement.manage", "production.product_service.read"]


class FakeAdminRepositoryWithPolicyPermission(FakeAdminRepository):
    session_permissions = ["admin.tenant.read", "internal.policy.evaluate", "production.product_service.read"]


class FakeAdminRepositoryWithModuleDependencyError(FakeAdminRepository):
    def set_backoffice_entitlement(self, *args, **kwargs):
        raise ValueError("module_dependencies_required:hr,production")

    def update_entitlement_preference(self, *args, **kwargs):
        raise ValueError("module_dependency_in_use:sales")


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


def test_unit_catalog_lists_active_tenant_units():
    response = client_with_fake_repo().get("/v1/catalogs/units-of-measure", headers={"X-Tenant-Id": TENANT_ID})
    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "H87"


def test_unit_catalog_creates_custom_unit():
    response = client_with_fake_repo().post("/v1/catalogs/units-of-measure", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-unit-create-001"}, json={"code":"SVC","name_es":"Servicio","name_en":"Service","symbol":"svc","category":"other","decimal_places":2})
    assert response.status_code == 201
    assert response.json()["data"]["system_default"] is False


def test_unit_catalog_rejects_unknown_active_code():
    response = client_with_fake_repo().get("/v1/catalogs/units-of-measure/by-code/NOPE", headers={"X-Tenant-Id": TENANT_ID})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "unit_of_measure_not_found"


def test_unit_catalog_create_requires_idempotency_key():
    response = client_with_fake_repo().post("/v1/catalogs/units-of-measure", headers={"X-Tenant-Id": TENANT_ID}, json={"code":"SVC","name_es":"Servicio","name_en":"Service","symbol":"svc","category":"other","decimal_places":2})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_unit_catalog_updates_with_idempotency_key():
    response = client_with_fake_repo().patch("/v1/catalogs/units-of-measure/uom_h87", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-unit-update-001"}, json={"status": "inactive"})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"


def test_unit_catalog_update_requires_idempotency_key():
    response = client_with_fake_repo().patch("/v1/catalogs/units-of-measure/uom_h87", headers={"X-Tenant-Id": TENANT_ID}, json={"status": "inactive"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


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


def test_onboard_tenant_rejects_sales_without_active_dependencies():
    response = client_with_fake_repo().post(
        "/v1/provisioning/tenant-onboarding",
        headers={"Idempotency-Key": "test-onboarding-sales-dependencies"},
        json={
            "slug": "Cliente-Ventas",
            "commercial_name": "Cliente Ventas",
            "source": {"type": "manual", "id": "sales-dependencies"},
            "owner": {"email": "owner.ventas@cliente.com", "display_name": "Owner Ventas"},
            "modules": [
                {"module_code": "admin", "status": "active"},
                {"module_code": "sales", "status": "active"},
            ],
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "module_dependencies_required"
    assert response.json()["error"]["details"]["dependencies"] == ["hr", "production"]


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


def test_backoffice_lists_tenants_with_search():
    client = client_with_fake_repo()

    response = client.get("/v1/backoffice/tenants?search=demo")

    assert response.status_code == 200
    assert response.json()["data"][0]["slug"] == "demo-qa"
    assert response.json()["data"][0]["owner_email"] == "admin.qa@erclave.local"
    assert response.json()["data"][0]["modules"] == ["admin", "production"]


def test_backoffice_lists_module_catalog_with_runtime_status():
    response = client_with_fake_repo().get("/v1/backoffice/modules")

    assert response.status_code == 200
    modules = {item["code"]: item for item in response.json()["data"]}
    assert modules["production"]["implementation_status"] == "implemented"
    assert modules["sales"]["implementation_status"] == "implemented"
    assert modules["sales"]["dependencies"] == ["hr", "production"]


def test_backoffice_module_catalog_requires_internal_allowlist():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase", backoffice_admin_emails="internal@erclave.local")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(uid="tenant-owner", email="admin.qa@erclave.local", name="Tenant owner")

    response = TestClient(app).get("/v1/backoffice/modules")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "backoffice_admin_required"


def test_backoffice_updates_tenant_profile():
    response = client_with_fake_repo().patch(
        f"/v1/backoffice/tenants/{TENANT_ID}",
        headers={"Idempotency-Key": "test-backoffice-update-001"},
        json={"commercial_name": "ERClave Demo Editado", "plan_id": "premium"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["commercial_name"] == "ERClave Demo Editado"
    assert response.json()["data"]["plan_id"] == "premium"


def test_backoffice_grants_implemented_module():
    response = client_with_fake_repo().put(
        f"/v1/backoffice/tenants/{TENANT_ID}/entitlements/inventory",
        headers={"Idempotency-Key": "test-backoffice-entitlement-001"},
        json={"status": "active", "source": "manual", "limits": {"warehouses": 3}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["effective_active"] is True
    assert response.json()["data"]["limits"] == {"warehouses": 3}


def test_backoffice_reports_missing_sales_dependencies():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepositoryWithModuleDependencyError()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="demo")
    response = TestClient(app).put(
        f"/v1/backoffice/tenants/{TENANT_ID}/entitlements/sales",
        headers={"Idempotency-Key": "test-sales-dependencies-001"},
        json={"status": "active"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "module_dependencies_required"
    assert response.json()["error"]["details"]["dependencies"] == ["hr", "production"]


def test_backoffice_rejects_enabling_planned_module():
    response = client_with_fake_repo().put(
        f"/v1/backoffice/tenants/{TENANT_ID}/entitlements/billing",
        headers={"Idempotency-Key": "test-backoffice-entitlement-planned"},
        json={"status": "active"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "module_not_implemented"


def test_backoffice_suspends_tenant():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/backoffice/tenants/{TENANT_ID}/status",
        headers={"Idempotency-Key": "test-backoffice-suspend-001"},
        json={"status": "suspended"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "suspended"


def test_backoffice_deletes_tenant_and_firebase_identity(monkeypatch):
    client = client_with_fake_repo()
    deleted_emails = []
    monkeypatch.setattr(admin_api, "delete_firebase_user_by_email", lambda email, settings: deleted_emails.append(email))

    response = client.delete(
        f"/v1/backoffice/tenants/{TENANT_ID}",
        headers={"Idempotency-Key": "test-backoffice-delete-001"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True
    assert response.json()["data"]["removed_memberships"] == 1
    assert deleted_emails == ["admin.qa@erclave.local"]


def test_backoffice_lists_usage_metrics():
    client = client_with_fake_repo()

    response = client.get("/v1/backoffice/usage?from_date=2026-07-01&to_date=2026-07-07")

    assert response.status_code == 200
    assert response.json()["data"][0]["tenant_id"] == TENANT_ID
    assert response.json()["data"][0]["api_requests"] == 128
    assert response.json()["summary"]["estimated_cost_mxn"] == "19.75"


def test_backoffice_usage_rejects_invalid_date_range():
    client = client_with_fake_repo()

    response = client.get("/v1/backoffice/usage?from_date=2026-07-07&to_date=2026-07-01")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_usage_date_range"


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


def test_list_session_tenants_uses_firebase_actor_email_when_enabled():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="admin.qa@erclave.local",
        name="Admin QA",
    )
    client = TestClient(app)

    response = client.get("/v1/session/tenants")

    assert response.status_code == 200
    assert response.json()["data"][0]["tenant"]["id"] == TENANT_ID
    assert response.json()["data"][0]["roles"] == ["owner"]


def test_list_tenant_entitlements_returns_modules():
    client = client_with_fake_repo()

    response = client.get(f"/v1/tenants/{TENANT_ID}/entitlements")

    assert response.status_code == 200
    assert [item["module_code"] for item in response.json()["data"]] == ["admin", "production"]


def test_list_tenant_entitlements_allows_firebase_tenant_reader():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user",
        email="admin.qa@erclave.local",
        name="Admin QA",
    )
    client = TestClient(app)

    response = client.get(f"/v1/tenants/{TENANT_ID}/entitlements")

    assert response.status_code == 200
    assert [item["module_code"] for item in response.json()["data"]] == ["admin", "production"]


def test_update_tenant_entitlement_preference_returns_updated_module():
    client = client_with_fake_repo()

    response = client.put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-001"},
        json={"enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["module_code"] == "inventory"
    assert response.json()["data"]["status"] == "active"
    assert response.json()["data"]["tenant_enabled"] is False
    assert response.json()["data"]["effective_active"] is False


def test_tenant_cannot_disable_module_required_by_active_sales():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepositoryWithModuleDependencyError()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="demo")
    response = TestClient(app).put(
        f"/v1/tenants/{TENANT_ID}/entitlements/production",
        headers={"Idempotency-Key": "test-sales-dependent-001"},
        json={"enabled": False},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "module_dependency_in_use"
    assert response.json()["error"]["details"]["dependents"] == ["sales"]


def test_tenant_cannot_change_contractual_entitlement_fields():
    response = client_with_fake_repo().put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-contract-denied"},
        json={"status": "active", "source": "manual", "limits": {}},
    )

    assert response.status_code == 422


def test_upsert_tenant_entitlement_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.put(
        f"/v1/tenants/{TENANT_ID}/entitlements/inventory",
        json={"enabled": False},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_upsert_tenant_entitlement_returns_404_for_missing_tenant():
    client = client_with_fake_repo()

    response = client.put(
        "/v1/tenants/ten_missing/entitlements/inventory",
        headers={"Idempotency-Key": "test-entitlement-404"},
        json={"enabled": True},
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
        json={"enabled": False},
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
        json={"enabled": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["tenant_enabled"] is False


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


def test_document_template_returns_tenant_defaults():
    client = client_with_fake_repo()

    response = client.get("/v1/document-template", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"] == {
        "logo_data_url": None,
        "primary_color": "#6106A0",
        "accent_color": "#F557D3",
        "text_color": "#190F34",
        "footer_text": None,
        "show_page_number": True,
    }


def test_document_template_updates_valid_logo_and_can_remove_it():
    client = client_with_fake_repo()
    valid_logo = "data:image/png;base64,iVBORw0KGgo="
    payload = {
        "logo_data_url": valid_logo,
        "primary_color": "#112233",
        "accent_color": "#445566",
        "text_color": "#778899",
        "footer_text": "Documento del tenant",
        "show_page_number": False,
    }

    response = client.put(
        "/v1/document-template",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-document-template-001"},
        json=payload,
    )
    remove_response = client.put(
        "/v1/document-template",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-document-template-002"},
        json={**payload, "logo_data_url": None},
    )

    assert response.status_code == 200
    assert response.json()["data"]["logo_data_url"] == valid_logo
    assert remove_response.status_code == 200
    assert remove_response.json()["data"]["logo_data_url"] is None


def test_document_template_rejects_missing_idempotency_and_fake_image_content():
    client = client_with_fake_repo()
    payload = {
        "logo_data_url": "data:image/png;base64,bm90IGEgcG5n",
        "primary_color": "#112233",
        "accent_color": "#445566",
        "text_color": "#778899",
        "footer_text": None,
        "show_page_number": True,
    }

    invalid_logo = client.put(
        "/v1/document-template",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-document-template-invalid"},
        json=payload,
    )
    missing_idempotency = client.put(
        "/v1/document-template",
        headers={"X-Tenant-Id": TENANT_ID},
        json={**payload, "logo_data_url": None},
    )

    assert invalid_logo.status_code == 422
    assert missing_idempotency.status_code == 400


def test_document_template_update_denies_missing_firebase_permission():
    app.dependency_overrides[get_admin_repository] = lambda: FakeAdminRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[get_authenticated_actor] = lambda: AuthenticatedActor(
        uid="firebase-user", email="admin.qa@erclave.local", name="Admin QA"
    )
    client = TestClient(app)

    response = client.put(
        "/v1/document-template",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-document-template-denied"},
        json={
            "logo_data_url": None,
            "primary_color": "#112233",
            "accent_color": "#445566",
            "text_color": "#778899",
            "footer_text": None,
            "show_page_number": True,
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


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

    response = client.get("/v1/permissions", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "admin.tenant.read"


def test_list_permissions_requires_tenant_context():
    client = client_with_fake_repo()

    response = client.get("/v1/permissions")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


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
        json={"assignments": [{"permission_id": PERMISSION_ID, "scope": {}}], "expected_revision": 1},
    )

    assert response.status_code == 200
    assert response.json()["data"]["permissions"] == ["admin.tenant.read"]


def test_replace_role_permissions_accepts_legacy_payload_with_server_revision():
    client = client_with_fake_repo()

    response = client.put(
        f"/v1/roles/{ROLE_ID}/permissions",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-role-permissions-legacy"},
        json={"permission_ids": [PERMISSION_ID], "scope": {}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["permission_revision"] == 2


def test_list_code_sequences_returns_tenant_catalog():
    response = client_with_fake_repo().get("/v1/catalogs/code-sequences", headers={"X-Tenant-Id": TENANT_ID})
    assert response.status_code == 200
    assert response.json()["data"][0]["document_type"] == "production.order"


def test_update_code_sequence_switches_to_manual_mode():
    response = client_with_fake_repo().patch(
        "/v1/catalogs/code-sequences/seq_op",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-sequence-update-001"},
        json={"mode": "manual"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["mode"] == "manual"


def test_allocate_business_code_returns_managed_folio():
    response = client_with_fake_repo().post(
        "/v1/catalogs/code-sequences/production.order/next",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-sequence-next-001"},
        json={"manual_code": None},
    )
    assert response.status_code == 200
    assert response.json()["data"]["code"] == "OP-000007"
