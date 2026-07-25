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
    auth_mode: AuthMode = "demo"
    firebase_project_id: str | None = None
    firebase_web_api_key: str | None = None
    backoffice_admin_emails: str = ""
    database_url: str | None = None
    log_level: str = Field(default="INFO")

    @model_validator(mode="after")
    def validate_public_app_url(self) -> "Settings":
        if self.environment == "local" or self.service_name != "admin-service":
            return self

        parsed = urlparse(self.app_public_base_url)
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() in local_hosts:
            raise ValueError(
                "ERCLAVE_APP_PUBLIC_BASE_URL must be a public HTTPS URL in QA and production."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
