from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError, erclave_error_handler
from erclave_common.health import router as health_router
from erclave_common.middleware import CorrelationIdMiddleware, TenantContextMiddleware

from .api import router as admin_router


QA_FIREBASE_ORIGIN_REGEX = r"https://erclave(--[a-z0-9-]+)?\.web\.app|https://erclave\.firebaseapp\.com"
ALLOWED_ORIGINS = {
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://erclave.web.app",
    "https://erclave.firebaseapp.com",
}
ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
ALLOWED_HEADERS = "Accept, Accept-Language, Authorization, Content-Language, Content-Type, Idempotency-Key, X-Actor-Id, X-Correlation-Id, X-Tenant-Id"


def _is_allowed_origin(origin: str | None, allowed_origins: list[str], environment: str) -> bool:
    if not origin:
        return False
    if origin in allowed_origins:
        return True
    return environment == "qa" and origin.startswith("https://erclave--") and origin.endswith(".web.app")


def _private_network_preflight_response(origin: str) -> PlainTextResponse:
    return PlainTextResponse(
        "OK",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": ALLOWED_METHODS,
            "Access-Control-Allow-Headers": ALLOWED_HEADERS,
            "Access-Control-Allow-Private-Network": "true",
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        },
    )


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
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=QA_FIREBASE_ORIGIN_REGEX if settings.environment == "qa" else None,
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
    )

    @app.middleware("http")
    async def allow_private_network_access(request, call_next):
        if (
            request.method == "OPTIONS"
            and request.headers.get("access-control-request-private-network") == "true"
            and _is_allowed_origin(request.headers.get("origin"), settings.cors_origin_list, settings.environment)
        ):
            return _private_network_preflight_response(request.headers["origin"])
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_exception_handler(ErclaveError, erclave_error_handler)
    return app


app = create_app()
