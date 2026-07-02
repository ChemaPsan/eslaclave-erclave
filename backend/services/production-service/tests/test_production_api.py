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

app = main_module.app
get_production_repository = repositories_module.get_production_repository
ProductServiceRead = schemas_module.ProductServiceRead


TENANT_ID = "ten_demo"
PRODUCT_SERVICE_ID = "prs_demo"


class FakeProductionRepository:
    def list_product_services(self, tenant_id: str, limit: int = 50, status: str | None = None, q: str | None = None, type_: str | None = None):
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

    def update_product_service_status(self, tenant_id: str, product_service_id: str, status: str):
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


def client_with_fake_repo() -> TestClient:
    app.dependency_overrides[get_production_repository] = lambda: FakeProductionRepository()
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


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


def test_update_product_service_returns_updated_item():
    client = client_with_fake_repo()

    response = client.patch(
        f"/v1/production/product-services/{PRODUCT_SERVICE_ID}",
        headers={"X-Tenant-Id": TENANT_ID},
        json={"name": "Pan de caja actualizado", "target_price": 44.0},
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Pan de caja actualizado"


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
