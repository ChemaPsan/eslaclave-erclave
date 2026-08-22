from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError,erclave_error_handler
from erclave_common.health import router as health_router
from erclave_common.middleware import CorrelationIdMiddleware,TenantContextMiddleware
from .api import router

_VALIDATION_MESSAGES={
    "invalid_nss":"El NSS debe contener exactamente 11 digitos.",
    "invalid_nss_check_digit":"El digito verificador del NSS no es valido.",
    "invalid_curp":"La CURP debe tener 18 caracteres y un formato valido.",
    "invalid_rfc":"El RFC de persona fisica debe tener 13 caracteres y un formato valido.",
    "hire_date_in_future":"La fecha de ingreso no puede estar en el futuro.",
    "invalid_birth_date":"La fecha de nacimiento debe ser anterior a la fecha de ingreso.",
}

async def hr_validation_error_handler(request:Request,exc:RequestValidationError)->JSONResponse:
    issues=[]
    for error in exc.errors():
        field=".".join(str(item) for item in error.get("loc",()) if item not in {"body","query","path"}) or "request"
        raw_code=str((error.get("ctx") or {}).get("error") or "")
        code=next((item for item in _VALIDATION_MESSAGES if item in raw_code),"invalid_field")
        if code=="invalid_field" and field in {"nss","curp","rfc"} and error.get("type") in {"string_too_short","string_too_long"}:
            code=f"invalid_{field}"
        issues.append({"field":field,"code":code})
    first=issues[0] if issues else {"field":"request","code":"invalid_field"}
    message=_VALIDATION_MESSAGES.get(first["code"],f"Revisa el campo {first['field']}; el valor no cumple el formato requerido.")
    correlation_id=getattr(request.state,"correlation_id",None)
    return JSONResponse(status_code=422,content={"error":{"code":first["code"],"message":message,"correlation_id":correlation_id,"details":{"issues":issues}}})
def create_app():
    settings=get_settings();app=FastAPI(title="ERClave HR Service",version=settings.version)
    app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_methods=["GET","POST","PATCH","OPTIONS"],allow_headers=["Content-Type","X-Tenant-Id","X-Actor-Id","X-Correlation-Id","Idempotency-Key","Authorization"])
    app.add_middleware(CorrelationIdMiddleware);app.add_middleware(TenantContextMiddleware);app.add_exception_handler(ErclaveError,erclave_error_handler);app.add_exception_handler(RequestValidationError,hr_validation_error_handler);app.include_router(health_router);app.include_router(router);return app
app=create_app()
