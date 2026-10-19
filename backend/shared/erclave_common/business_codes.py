"""Idempotent Admin code authority for operational documents."""

import hashlib
import json
from urllib import error, parse, request

from fastapi import Depends

from .config import Settings, get_settings
from .errors import ErclaveError
from .transport import open_dependency


def derived_manual_code(prefix: str, tenant_id: str, *identity: str) -> str:
    """Stable visible code for an internally generated document in manual mode."""
    seed = json.dumps([tenant_id, *identity], separators=(",", ":"), ensure_ascii=False)
    return f"{prefix}-{hashlib.sha256(seed.encode()).hexdigest()[:24].upper()}"


def allocate_movement_code(folio, tenant_id: str, operation: str, stable_key: str, manual_code: str | None = None) -> str:
    if folio is not None:
        return folio(operation, stable_key, manual_code)
    # Direct local repository harnesses do not inject the HTTP authority.
    return manual_code or derived_manual_code("MOV", tenant_id, operation, stable_key)


class BusinessCodeClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.admin_service_url.rstrip("/")
        self.timeout = settings.authorization_timeout_seconds

    def allocate(self, tenant_id: str, document_type: str, authorization: str | None, key: str, manual_code: str | None = None) -> str:
        url = f"{self.base_url}/v1/catalogs/code-sequences/{parse.quote(document_type, safe='')}/next"
        payload = json.dumps({"manual_code": manual_code}).encode()
        call = request.Request(url, data=payload, method="POST", headers={
            "Authorization": authorization or "", "X-Tenant-Id": tenant_id,
            "Idempotency-Key": key, "Content-Type": "application/json",
        })
        try:
            with open_dependency(call, timeout=self.timeout, opener=request.urlopen) as response:
                result = json.loads(response.read())["data"]
            code = result["code"]
            if result.get("document_type") != document_type or not isinstance(code, str) or not code:
                raise ValueError("invalid code authority response")
            return code
        except error.HTTPError as exc:
            status = exc.code if exc.code in (401, 403, 404, 409, 422) else 503
            code = {
                404: "code_sequence_not_found", 409: "code_allocation_conflict",
                422: "manual_business_code_required", 401: "code_authority_denied",
                403: "code_authority_denied",
            }.get(status, "code_authority_unavailable")
            raise ErclaveError(code, "Business code could not be allocated.", status_code=status) from exc
        except (OSError, TimeoutError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ErclaveError("code_authority_unavailable", "Business code authority is unavailable.", status_code=503) from exc


def get_business_code_client(settings: Settings = Depends(get_settings)) -> BusinessCodeClient:
    return BusinessCodeClient(settings)
