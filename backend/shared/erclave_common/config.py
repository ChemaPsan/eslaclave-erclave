from functools import lru_cache
from typing import Literal

from pydantic import Field
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
    app_public_base_url: str = "http://localhost:4173"
    auth_mode: AuthMode = "demo"
    firebase_project_id: str | None = None
    firebase_web_api_key: str | None = None
    backoffice_admin_emails: str = ""
    database_url: str | None = None
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()
