from uuid import uuid4
import math
import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from .config import get_settings
from .transport import correlation, deadline


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        supplied = request.headers.get("X-Correlation-Id", "")
        correlation_id = supplied if re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", supplied) else f"corr_{uuid4().hex}"
        request.state.correlation_id = correlation_id
        budget = get_settings().operation_timeout_seconds
        try:
            incoming = float(request.headers.get("X-Request-Timeout-Ms", "")) / 1000
            if math.isfinite(incoming) and incoming > 0:
                budget = min(budget, incoming)
        except ValueError:
            pass
        correlation_token = correlation.set(correlation_id)
        deadline_token = deadline.set(time.monotonic() + budget)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-Id"] = correlation_id
            return response
        finally:
            correlation.reset(correlation_token)
            deadline.reset(deadline_token)


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Placeholder: real tenant validation must use token/session/API client, not this header alone.
        request.state.tenant_id = request.headers.get("X-Tenant-Id")
        return await call_next(request)
