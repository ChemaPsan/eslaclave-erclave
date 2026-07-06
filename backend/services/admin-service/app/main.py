from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError, erclave_error_handler
from erclave_common.health import router as health_router
from erclave_common.middleware import CorrelationIdMiddleware, TenantContextMiddleware

from .api import router as admin_router


QA_FIREBASE_ORIGIN_REGEX = r"https://erclave(--[a-z0-9-]+)?\.web\.app|https://erclave\.firebaseapp\.com"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ERClave Admin Service",
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(health_router)
    app.include_router(admin_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "https://erclave.web.app",
            "https://erclave.firebaseapp.com",
        ],
        allow_origin_regex=QA_FIREBASE_ORIGIN_REGEX,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "X-Tenant-Id",
            "X-Actor-Id",
            "X-Correlation-Id",
            "Idempotency-Key",
            "Authorization",
        ],
        allow_private_network=True,
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_exception_handler(ErclaveError, erclave_error_handler)
    return app


app = create_app()
