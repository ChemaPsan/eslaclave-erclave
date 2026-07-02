from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError, erclave_error_handler
from erclave_common.health import router as health_router
from erclave_common.middleware import CorrelationIdMiddleware, TenantContextMiddleware

from .api import router as production_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ERClave Production Service",
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-Tenant-Id", "X-Correlation-Id", "Idempotency-Key", "Authorization"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_exception_handler(ErclaveError, erclave_error_handler)
    app.include_router(health_router)
    app.include_router(production_router)
    return app


app = create_app()
