import pytest
from pydantic import ValidationError

from erclave_common.config import Settings


QA_SETTINGS = {
    "environment": "qa",
    "api_public_base_url": "https://admin-service-qa.example.run.app",
    "app_public_base_url": "https://erclave.web.app",
    "cors_origins": "https://erclave.web.app,https://erclave.firebaseapp.com",
    "auth_mode": "firebase",
    "firebase_project_id": "erclave",
    "database_url": "postgresql+psycopg://user:password@db/erclave_qa",
    "hr_service_url": "https://hr-service-qa.example.run.app",
    "inventory_service_url": "https://inventory-service-qa.example.run.app",
    "production_service_url": "https://production-service-qa.example.run.app",
    "maintenance_service_url": "https://maintenance-service-qa.example.run.app",
    "purchasing_service_url": "https://purchasing-service-qa.example.run.app",
    "sales_service_url": "https://sales-service-qa.example.run.app",
    "costing_service_url": "https://costing-service-qa.example.run.app",
}


@pytest.fixture(autouse=True)
def clear_inherited_firebase_emulator(monkeypatch):
    # A test process started by the Local launcher must still exercise the
    # intended QA configuration, rather than accidentally inheriting its emulator.
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)


def test_local_environment_allows_local_app_url():
    settings = Settings(environment="local", app_public_base_url="http://localhost:4173")

    assert settings.app_public_base_url == "http://localhost:4173"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("api_public_base_url", "https://admin-service-qa.example.run.app"),
        ("database_url", "postgresql+psycopg://user:password@127.0.0.1:5432/erclave_qa"),
        ("database_url", "postgresql+psycopg://user:password@qa-db.example/erclave_local"),
        ("firebase_project_id", "erclave"),
        ("purchasing_service_url", "https://purchasing-service-qa.example.run.app"),
    ],
)
def test_local_environment_rejects_qa_resources(field, value):
    with pytest.raises(ValidationError):
        Settings(environment="local", **{field: value})


@pytest.mark.parametrize(
    "app_public_base_url",
    [
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "https://localhost",
        "http://erclave.web.app",
        "not-a-url",
    ],
)
def test_qa_rejects_non_public_or_insecure_app_url(app_public_base_url):
    with pytest.raises(ValidationError, match="public HTTPS URL"):
        Settings(**{**QA_SETTINGS, "app_public_base_url": app_public_base_url})


def test_qa_accepts_public_https_app_url():
    settings = Settings(**QA_SETTINGS)

    assert settings.app_public_base_url == "https://erclave.web.app"


def test_other_services_do_not_require_admin_frontend_url():
    settings = Settings(**{
        **QA_SETTINGS,
        "service_name": "production-service",
        "app_public_base_url": "http://localhost:4173",
        "admin_service_url": "https://admin-service-qa.example.run.app",
    })

    assert settings.service_name == "production-service"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("api_public_base_url", "http://localhost:8000", "ERCLAVE_API_PUBLIC_BASE_URL"),
        ("admin_service_url", "http://localhost:8000", "ERCLAVE_ADMIN_SERVICE_URL"),
        ("hr_service_url", "http://localhost:8006", "ERCLAVE_HR_SERVICE_URL"),
        ("inventory_service_url", "http://localhost:8004", "ERCLAVE_INVENTORY_SERVICE_URL"),
        ("cors_origins", "https://erclave.web.app,http://localhost:4173", "ERCLAVE_CORS_ORIGINS"),
    ],
)
def test_non_local_service_rejects_local_runtime_urls(field, value, message):
    values = {
        **QA_SETTINGS,
        "service_name": "production-service",
        "admin_service_url": "https://admin-service-qa.example.run.app",
        field: value,
    }
    with pytest.raises(ValidationError, match=message):
        Settings(**values)


def test_qa_requires_firebase_and_database_configuration():
    for values in [
        {**QA_SETTINGS, "auth_mode": "demo"},
        {**QA_SETTINGS, "firebase_project_id": None},
        {**QA_SETTINGS, "database_url": None},
    ]:
        with pytest.raises(ValidationError):
            Settings(**values)


def test_inventory_uses_its_service_database_url_for_readiness():
    settings = Settings(**{
        **QA_SETTINGS,
        "database_url": None,
        "service_name": "inventory-service",
        "api_public_base_url": "https://inventory-service-qa.example.run.app",
        "admin_service_url": "https://admin-service-qa.example.run.app",
        "inventory_database_url": "postgresql+psycopg://user:password@db/erclave_qa",
    })

    assert settings.effective_database_url == settings.inventory_database_url


@pytest.mark.parametrize(
    ("service_name", "field", "message"),
    [
        ("inventory-service", "production_service_url", "ERCLAVE_PRODUCTION_SERVICE_URL"),
        ("inventory-service", "maintenance_service_url", "ERCLAVE_MAINTENANCE_SERVICE_URL"),
        ("inventory-service", "purchasing_service_url", "ERCLAVE_PURCHASING_SERVICE_URL"),
        ("sales-service", "inventory_service_url", "ERCLAVE_INVENTORY_SERVICE_URL"),
        ("production-service", "sales_service_url", "ERCLAVE_SALES_SERVICE_URL"),
        ("inventory-service", "sales_service_url", "ERCLAVE_SALES_SERVICE_URL"),
    ],
)
def test_authority_consumers_reject_local_dependency_urls(service_name, field, message):
    values = {
        **QA_SETTINGS,
        "service_name": service_name,
        "api_public_base_url": f"https://{service_name}-qa.example.run.app",
        "admin_service_url": "https://admin-service-qa.example.run.app",
        field: "http://localhost:8000",
    }
    with pytest.raises(ValidationError, match=message):
        Settings(**values)


@pytest.mark.parametrize("environment", ["qa", "prod"])
@pytest.mark.parametrize("service_name", ["admin-service", "production-service", "inventory-service", "hr-service"])
def test_active_basic_catalog_requires_its_public_costing_url(environment, service_name):
    values = {**QA_SETTINGS, "environment": environment, "service_name": service_name,
              "admin_service_url": QA_SETTINGS["api_public_base_url"],
              "cost_center_catalog_enabled": True, "costing_service_url": "http://127.0.0.1:8014"}
    with pytest.raises(ValidationError, match="ERCLAVE_COSTING_SERVICE_URL"):
        Settings(**values)
    settings = Settings(**{**values, "costing_service_url": QA_SETTINGS["costing_service_url"]})
    assert settings.cost_center_catalog_enabled is True


@pytest.mark.parametrize("service_name", ["admin-service", "production-service", "inventory-service", "hr-service"])
def test_disabled_basic_catalog_keeps_costing_an_optional_dependency(service_name):
    settings = Settings(**{**QA_SETTINGS, "service_name": service_name,
                           "admin_service_url": QA_SETTINGS["api_public_base_url"],
                           "cost_center_catalog_enabled": False, "costing_service_url": "http://localhost:8014"})
    assert settings.cost_center_catalog_enabled is False


@pytest.mark.parametrize("environment", ["qa", "prod"])
def test_firebase_emulator_is_rejected_outside_local(environment, monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
    with pytest.raises(ValidationError, match="FIREBASE_AUTH_EMULATOR_HOST"):
        Settings(**{**QA_SETTINGS, "environment": environment})


def test_local_firebase_emulator_is_allowed(monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
    assert Settings(environment="local", firebase_project_id="demo-erclave").environment == "local"


@pytest.mark.parametrize("url", ["https://user:secret@api.example.invalid", "https://api.example.invalid?token=secret", "https://api.example.invalid#local"])
def test_runtime_authority_urls_reject_embedded_credentials_query_and_fragment(url):
    with pytest.raises(ValidationError, match="ERCLAVE_SALES_SERVICE_URL"):
        Settings(**{**QA_SETTINGS, "service_name": "production-service",
                    "admin_service_url": QA_SETTINGS["api_public_base_url"], "sales_service_url": url})


def test_costing_catalog_requires_admin_authority_and_its_service_database():
    values = {**QA_SETTINGS, "service_name": "costing-service", "database_url": None,
              "cost_center_catalog_enabled": True,
              "costing_database_url": QA_SETTINGS["database_url"],
              "admin_service_url": QA_SETTINGS["api_public_base_url"]}
    assert Settings(**values).effective_database_url == values["costing_database_url"]
    with pytest.raises(ValidationError, match="ERCLAVE_ADMIN_SERVICE_URL"):
        Settings(**{**values, "admin_service_url": "http://localhost:8000"})
    with pytest.raises(ValidationError, match="service database URL"):
        Settings(**{**values, "costing_database_url": None})
