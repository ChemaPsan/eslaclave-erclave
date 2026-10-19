from functools import lru_cache
from pathlib import Path

from alembic.script import ScriptDirectory
from fastapi import APIRouter, Response
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings


router = APIRouter(tags=["Technical"])


@lru_cache(maxsize=8)
def readiness_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})


@lru_cache(maxsize=1)
def expected_schema_heads() -> frozenset[str]:
    return frozenset(ScriptDirectory(str(Path(__file__).resolve().parents[2] / "alembic")).get_heads())


def database_readiness(database_url: str) -> bool:
    try:
        with readiness_engine(database_url).connect() as connection:
            heads = frozenset(connection.execute(text("select version_num from alembic_version")).scalars())
        return bool(heads) and heads == expected_schema_heads()
    except (SQLAlchemyError, OSError):
        return False


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
        "version": settings.version,
    }


@router.get("/ready", responses={503: {"description": "Database unavailable or migration head differs from this image (QA/production)."}})
def ready(response: Response) -> dict:
    settings = get_settings()
    configured = bool(settings.effective_database_url)
    # Remote release gates must observe the actual DB/schema, not just a URL.
    database_ready = configured
    if settings.environment != "local":
        database_ready = configured and database_readiness(settings.effective_database_url)
        if not database_ready:
            response.status_code = 503
    return {
        "status": "ready" if database_ready else "degraded",
        "service": settings.service_name,
        "database_configured": configured,
        "database_ready": database_ready,
    }


@router.get("/version")
def version() -> dict:
    settings = get_settings()
    return {
        "service": settings.service_name,
        "version": settings.version,
        "api_public_base_url": settings.api_public_base_url,
    }
