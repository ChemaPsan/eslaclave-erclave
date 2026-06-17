from fastapi import FastAPI

from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError, erclave_error_handler
from erclave_common.health import router as health_router
from erclave_common.middleware import CorrelationIdMiddleware, TenantContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ERClave Admin Service",
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_exception_handler(ErclaveError, erclave_error_handler)
    app.include_router(health_router)
    return app


app = create_app()

