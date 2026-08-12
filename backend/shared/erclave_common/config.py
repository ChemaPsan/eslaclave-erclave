from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["local", "qa", "prod"]
AuthMode = Literal["demo", "firebase"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ERCLAVE_",
        env_file=".env",
        extra="ignore",
    )

    environment: Environment = "local"
    service_name: str = "admin-service"
    version: str = "0.1.0"
    api_public_base_url: str = "http://localhost:8000"
    admin_service_url: str = "http://localhost:8000"
    authorization_timeout_seconds: float = 5.0
    app_public_base_url: str = "http://localhost:4173"
    cors_origins: str = "http://127.0.0.1:4173,http://localhost:4173,https://erclave.web.app,https://erclave.firebaseapp.com"
    auth_mode: AuthMode = "demo"
    firebase_project_id: str | None = None
    firebase_web_api_key: str | None = None
    backoffice_admin_emails: str = ""
    database_url: str | None = None
    inventory_database_url: str | None = None
    hr_database_url: str | None = None
    log_level: str = Field(default="INFO")

    @model_validator(mode="after")
    def validate_environment_boundaries(self) -> "Settings":
        if self.environment == "local":
            return self

        local_hosts = {"localhost", "127.0.0.1", "::1"}

        def require_public_https(value: str, variable: str) -> None:
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() in local_hosts:
                raise ValueError(f"{variable} must be a public HTTPS URL in QA and production.")

        require_public_https(self.api_public_base_url, "ERCLAVE_API_PUBLIC_BASE_URL")
        if self.service_name == "admin-service":
            require_public_https(self.app_public_base_url, "ERCLAVE_APP_PUBLIC_BASE_URL")
        else:
            require_public_https(self.admin_service_url, "ERCLAVE_ADMIN_SERVICE_URL")

        if self.auth_mode != "firebase" or not self.firebase_project_id:
            raise ValueError("QA and production require Firebase auth and ERCLAVE_FIREBASE_PROJECT_ID.")
        if not self.effective_database_url:
            raise ValueError("QA and production require a service database URL from Secret Manager.")

        origins = self.cors_origin_list
        if not origins:
            raise ValueError("ERCLAVE_CORS_ORIGINS must contain at least one public HTTPS origin.")
        for origin in origins:
            require_public_https(origin, "ERCLAVE_CORS_ORIGINS")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def effective_database_url(self) -> str | None:
        if self.service_name == "inventory-service":
            return self.inventory_database_url or self.database_url
        if self.service_name == "hr-service":
            return self.hr_database_url or self.database_url
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
