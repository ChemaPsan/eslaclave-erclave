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
}


def test_local_environment_allows_local_app_url():
    settings = Settings(environment="local", app_public_base_url="http://localhost:4173")

    assert settings.app_public_base_url == "http://localhost:4173"


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
