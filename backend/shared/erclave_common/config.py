from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["local", "qa", "prod"]


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
    database_url: str | None = None
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()

