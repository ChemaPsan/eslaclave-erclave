from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError, erclave_error_handler
from erclave_common.health import router as health_router
from erclave_common.middleware import CorrelationIdMiddleware, TenantContextMiddleware
from .api import router
def create_app():
    settings=get_settings(); app=FastAPI(title="ERClave Inventory Service",version=settings.version)
    app.add_middleware(CORSMiddleware,allow_origins=["http://127.0.0.1:4173","http://localhost:4173","https://erclave.web.app"],allow_methods=["GET","POST","PATCH","OPTIONS"],allow_headers=["Content-Type","X-Tenant-Id","X-Actor-Id","X-Correlation-Id","Idempotency-Key","Authorization"])
    app.add_middleware(CorrelationIdMiddleware); app.add_middleware(TenantContextMiddleware); app.add_exception_handler(ErclaveError,erclave_error_handler); app.include_router(health_router); app.include_router(router); return app
app=create_app()
