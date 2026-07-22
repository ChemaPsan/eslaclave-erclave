import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))
for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        del sys.modules[module_name]

main_module = importlib.import_module("app.main")
repositories_module = importlib.import_module("app.repositories")
schemas_module = importlib.import_module("app.schemas")
authorization_module = importlib.import_module("app.authorization")
from erclave_common.config import Settings

app = main_module.app
get_production_repository = repositories_module.get_production_repository
ProductServiceRead = schemas_module.ProductServiceRead
RecipeRead = schemas_module.RecipeRead
RecipeVersionRead = schemas_module.RecipeVersionRead


TENANT_ID = "ten_demo"
OTHER_TENANT_ID = "ten_other_tenant"
PRODUCT_SERVICE_ID = "prs_demo"


class FakeProductionRepository:
    def list_product_services(self, tenant_id: str, limit: int = 50, status: str | None = None, q: str | None = None, type_: str | None = None):
        if tenant_id != TENANT_ID:
            return []
        return [
            ProductServiceRead(
                id=PRODUCT_SERVICE_ID,
                code="pan-caja",
                name="Pan de caja",
                type="product",
                category="Panificacion",
                base_unit="pza",
                status="active",
                target_price=42.5,
                standard_cost=20.0,
                responsible_area="Produccion",
            )
        ]

    def get_product_service(self, tenant_id: str, product_service_id: str):
        if tenant_id != TENANT_ID or product_service_id != PRODUCT_SERVICE_ID:
            return None
        return ProductServiceRead(
            id=PRODUCT_SERVICE_ID,
            code="pan-caja",
            name="Pan de caja",
            type="product",
            category="Panificacion",
            base_unit="pza",
            status="active",
        )

    def create_product_service(
        self,
        tenant_id: str,
        code: str,
        name: str,
        type_: str,
        category: str | None,
        base_unit: str,
        target_price: float | None,
        responsible_area: str | None,
        idempotency_key: str,
        request_hash: str,
        actor_id: str,
    ):
        if code == "duplicado":
            return None
        return ProductServiceRead(
            id="prs_new",
            code=code.lower(),
            name=name,
            type=type_,
            category=category,
            base_unit=base_unit,
            status="active",
            target_price=target_price,
            responsible_area=responsible_area,
        )

    def update_product_service(
        self,
        tenant_id: str,
        product_service_id: str,
        name: str | None,
        category: str | None,
        base_unit: str | None,
        target_price: float | None,
        responsible_area: str | None,
    ):
        if tenant_id != TENANT_ID or product_service_id != PRODUCT_SERVICE_ID:
            return None
        return ProductServiceRead(
            id=PRODUCT_SERVICE_ID,
            code="pan-caja",
            name=name or "Pan de caja",
            type="product",
            category=category or "Panificacion",
            base_unit=base_unit or "pza",
            status="active",
            target_price=target_price,
            responsible_area=responsible_area,
        )

    def update_product_service_status(self, tenant_id: str, product_service_id: str, status: str, idempotency_key: str, request_hash: str, actor_id: str):
        if tenant_id != TENANT_ID or product_service_id != PRODUCT_SERVICE_ID:
            return None
        return ProductServiceRead(
            id=PRODUCT_SERVICE_ID,
            code="pan-caja",
            name="Pan de caja",
            type="product",
            category="Panificacion",
            base_unit="pza",
            status=status,
        )

    def _version(self, status="draft", complete=True):
        resources = [{"id": "rrs_demo", "resource_type": "other", "resource_code": "agua", "resource_name": "Agua", "quantity": 1, "unit": "l", "unit_cost": 2, "total_cost": 2, "sort_order": 1}] if complete else []
        stages = [{"id": "rst_demo", "name": "Mezclar", "expected_minutes": 10, "sort_order": 1, "status": "active"}] if complete else []
        return RecipeVersionRead(id="rcv_demo", recipe_id="rec_demo", version_number=1, status=status, base_quantity=1, base_unit="pza", standard_cost=2, resources=resources, stages=stages)

    def list_recipes(self, tenant_id: str, limit: int = 50):
        return [self.get_recipe(tenant_id, "rec_demo")] if tenant_id == TENANT_ID else []

    def get_recipe(self, tenant_id: str, recipe_id: str):
        if tenant_id != TENANT_ID or recipe_id != "rec_demo":
            return None
        return RecipeRead(id="rec_demo", product_service_id=PRODUCT_SERVICE_ID, code="rec-pan", name="Receta pan", status="draft", versions=[self._version()])

    def create_recipe(self, tenant_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str):
        if tenant_id != TENANT_ID or payload.product_service_id != PRODUCT_SERVICE_ID:
            return None
        return RecipeRead(id="rec_demo", product_service_id=payload.product_service_id, code=payload.code.lower(), name=payload.name, status="draft", versions=[self._version(complete=bool(payload.resources and payload.stages))])

    def create_recipe_version(self, tenant_id: str, recipe_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str):
        return self._version(complete=bool(payload.resources and payload.stages)) if tenant_id == TENANT_ID and recipe_id == "rec_demo" else None

    def update_recipe_version(self, tenant_id: str, version_id: str, payload, idempotency_key: str, request_hash: str, actor_id: str):
        return self._version(complete=bool(payload.resources and payload.stages)) if tenant_id == TENANT_ID and version_id == "rcv_demo" else None

    def transition_recipe_version(self, tenant_id: str, version_id: str, action: str, approved_by: str, approval_notes: str | None, effective_from: str | None, idempotency_key: str, request_hash: str):
        if tenant_id != TENANT_ID or version_id != "rcv_demo":
            return None
        statuses = {"submit": "pending_approval", "approve": "approved", "obsolete": "obsolete"}
        return self._version(statuses[action])


def client_with_fake_repo() -> TestClient:
    app.dependency_overrides[get_production_repository] = lambda: FakeProductionRepository()
    app.dependency_overrides[authorization_module.get_settings] = lambda: Settings(auth_mode="demo")
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


class FakeAdminSessionClient:
    def __init__(self, context: dict):
        self.context = context

    def get_context(self, tenant_id: str, authorization: str) -> dict:
        return self.context


def firebase_client(permissions: list[str], active_modules: list[str] | None = None, tenant_status: str = "active") -> TestClient:
    context = {
        "tenant": {"id": TENANT_ID, "status": tenant_status},
        "user": {"id": "usr_authenticated"},
        "permissions": permissions,
        "active_modules": active_modules if active_modules is not None else ["production"],
    }
    app.dependency_overrides[get_production_repository] = lambda: FakeProductionRepository()
    app.dependency_overrides[authorization_module.get_settings] = lambda: Settings(auth_mode="firebase")
    app.dependency_overrides[authorization_module.get_admin_session_client] = lambda: FakeAdminSessionClient(context)
    return TestClient(app)


def test_firebase_mode_requires_bearer_token():
    response = firebase_client(["production.product_service.read"]).get(
        "/v1/production/product-services", headers={"X-Tenant-Id": TENANT_ID}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "auth_required"


def test_firebase_mode_denies_missing_permission():
    response = firebase_client([]).get(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Authorization": "Bearer test-token"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_firebase_mode_denies_inactive_module():
    response = firebase_client(["production.product_service.read"], active_modules=[]).get(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Authorization": "Bearer test-token"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "module_not_enabled"


def test_firebase_mode_allows_exact_permission():
    response = firebase_client(["production.product_service.read"]).get(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200


def test_list_product_services_requires_tenant_header():
    client = client_with_fake_repo()

    response = client.get("/v1/production/product-services")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "tenant_required"


def test_list_product_services_returns_catalog():
    client = client_with_fake_repo()

    response = client.get("/v1/production/product-services", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"][0]["code"] == "pan-caja"


def test_list_product_services_does_not_leak_other_tenant_data():
    client = client_with_fake_repo()

    response = client.get("/v1/production/product-services", headers={"X-Tenant-Id": OTHER_TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_create_product_service_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"code": "galleta", "name": "Galleta", "type": "product", "base_unit": "pza"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_create_product_service_returns_created_item():
    client = client_with_fake_repo()

    response = client.post(
        "/v1/production/product-services",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-product-create"},
        json={"code": "Galleta", "name": "Galleta", "type": "product", "base_unit": "pza"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["code"] == "galleta"


def test_get_product_service_returns_item():
    client = client_with_fake_repo()

    response = client.get(f"/v1/production/product-services/{PRODUCT_SERVICE_ID}", headers={"X-Tenant-Id": TENANT_ID})

    assert response.status_code == 200
    assert response.json()["data"]["id"] == PRODUCT_SERVICE_ID


def test_get_product_service_from_other_tenant_returns_404():
    client = client_with_fake_repo()

    response = client.get(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": OTHER_TENANT_ID},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_service_not_found"


def test_update_product_service_returns_updated_item():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"name": "Pan de caja actualizado", "target_price": 44.0},
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Pan de caja actualizado"


def test_update_product_service_from_other_tenant_returns_404():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": OTHER_TENANT_ID},
        json={"name": "No debe cruzar tenant"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "product_service_not_found"


def test_update_product_service_status_requires_idempotency_key():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}/status",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"status": "inactive", "reason": "QA"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_update_product_service_status_returns_updated_status():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}/status",
        headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "test-product-status"},
        json={"status": "inactive", "reason": "QA"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "inactive"


RECIPE_PAYLOAD = {
    "product_service_id": PRODUCT_SERVICE_ID,
    "code": "REC-PAN",
    "name": "Receta pan",
    "base_quantity": 1,
    "base_unit": "pza",
    "resources": [{"resource_type": "other", "resource_code": "agua", "resource_name": "Agua", "quantity": 1, "unit": "l", "unit_cost": 2}],
    "stages": [{"name": "Mezclar", "expected_minutes": 10}],
}


def test_create_recipe_requires_idempotency_key():
    response = client_with_fake_repo().post("/v1/production/recipes", headers={"X-Tenant-Id": TENANT_ID}, json=RECIPE_PAYLOAD)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "idempotency_key_required"


def test_create_recipe_returns_initial_draft_version():
    response = client_with_fake_repo().post("/v1/production/recipes", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-create-01"}, json=RECIPE_PAYLOAD)
    assert response.status_code == 201
    assert response.json()["data"]["versions"][0]["status"] == "draft"
    assert response.json()["data"]["versions"][0]["standard_cost"] == 2


def test_recipe_read_does_not_leak_other_tenant_data():
    response = client_with_fake_repo().get("/v1/production/recipes/rec_demo", headers={"X-Tenant-Id": OTHER_TENANT_ID})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "recipe_not_found"


def test_submit_recipe_version_requires_idempotency_key():
    response = client_with_fake_repo().post("/v1/production/recipe-versions/rcv_demo/submit", headers={"X-Tenant-Id": TENANT_ID})
    assert response.status_code == 400


def test_recipe_version_can_be_submitted_and_approved():
    client = client_with_fake_repo()
    submitted = client.post("/v1/production/recipe-versions/rcv_demo/submit", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-submit-01"})
    approved = client.post("/v1/production/recipe-versions/rcv_demo/approve", headers={"X-Tenant-Id": TENANT_ID, "Idempotency-Key": "recipe-approve-01"}, json={})
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "pending_approval"
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "approved"
