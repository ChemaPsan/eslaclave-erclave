from fastapi import Request
from fastapi.responses import JSONResponse


class ErclaveError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


async def erclave_error_handler(request: Request, exc: ErclaveError) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    details = dict(exc.details)
    cause = exc
    while cause is not None:
        service = getattr(cause, "dependency_service", None)
        if service in {"admin", "hr", "inventory", "production", "maintenance", "external"}:
            details.setdefault("dependency_service", service)
            break
        cause = cause.__cause__
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": correlation_id,
                "details": details,
            }
        },
    )
