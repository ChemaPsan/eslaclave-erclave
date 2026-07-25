import pytest
from pydantic import ValidationError

from erclave_common.config import Settings


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
        Settings(environment="qa", app_public_base_url=app_public_base_url)


def test_qa_accepts_public_https_app_url():
    settings = Settings(environment="qa", app_public_base_url="https://erclave.web.app")

    assert settings.app_public_base_url == "https://erclave.web.app"


def test_other_services_do_not_require_admin_frontend_url():
    settings = Settings(
        environment="qa",
        service_name="production-service",
        app_public_base_url="http://localhost:4173",
    )

    assert settings.service_name == "production-service"
