from fastapi import APIRouter

from .config import get_settings


router = APIRouter(tags=["Technical"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.service_name,
        "environment": settings.environment,
        "version": settings.version,
    }


@router.get("/ready")
def ready() -> dict:
    settings = get_settings()
    return {
        "status": "ready" if settings.database_url else "degraded",
        "service": settings.service_name,
        "database_configured": bool(settings.database_url),
    }


@router.get("/version")
def version() -> dict:
    settings = get_settings()
    return {
        "service": settings.service_name,
        "version": settings.version,
        "api_public_base_url": settings.api_public_base_url,
    }

