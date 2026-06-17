from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .config import get_settings


def create_database_engine() -> Engine:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("ERCLAVE_DATABASE_URL is required to create a database engine.")
    return create_engine(settings.database_url, pool_pre_ping=True)

