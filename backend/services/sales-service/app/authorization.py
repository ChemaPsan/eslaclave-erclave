from dataclasses import dataclass
import json
from urllib import error, request

from fastapi import Depends, Header

from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError


@dataclass(frozen=True)
class AuthorizedContext:
    tenant_id: str
    actor_id: str
    permission: str


class AdminSessionClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.admin_service_url.rstrip("/")
        self.timeout = settings.authorization_timeout_seconds

    def get_context(self, tenant_id: str, authorization: str) -> dict:
        call = request.Request(
            f"{self.base_url}/v1/session/context",
            headers={"Authorization": authorization, "X-Tenant-Id": tenant_id, "Accept": "application/json"},
            method="GET",
        )
        try:
            with request.urlopen(call, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))["data"]
        except error.HTTPError as exc:
            status = 401 if exc.code == 401 else 403 if exc.code in (403, 404) else 503
            raise ErclaveError("sales_authorization_denied", "Sales authorization failed.", status_code=status) from exc
        except (error.URLError, TimeoutError, KeyError, ValueError) as exc:
            raise ErclaveError("authorization_service_unavailable", "Authorization service is unavailable.", status_code=503) from exc


def get_admin_session_client(settings: Settings = Depends(get_settings)) -> AdminSessionClient:
    return AdminSessionClient(settings)


def require_sales_access(permission: str | tuple[str, ...]):
    def dependency(
        x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
        authorization: str | None = Header(default=None, alias="Authorization"),
        x_actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
        settings: Settings = Depends(get_settings),
        client: AdminSessionClient = Depends(get_admin_session_client),
    ) -> AuthorizedContext:
        if not x_tenant_id:
            raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
        required = (permission,) if isinstance(permission, str) else permission
        if settings.auth_mode != "firebase":
            return AuthorizedContext(x_tenant_id, x_actor_id or "usr_demo", required[0])
        if not authorization or not authorization.lower().startswith("bearer "):
            raise ErclaveError("auth_required", "Authorization Bearer token is required.", status_code=401)
        context = client.get_context(x_tenant_id, authorization)
        tenant = context.get("tenant") or {}
        user = context.get("user") or {}
        if tenant.get("id") != x_tenant_id or tenant.get("status") != "active":
            raise ErclaveError("tenant_access_denied", "Tenant access denied.", status_code=403)
        if "sales" not in context.get("active_modules", []):
            raise ErclaveError("module_not_enabled", "Sales module is not enabled.", status_code=403)
        if not any(item in context.get("permissions", []) for item in required):
            details = {"permission": required[0]} if len(required) == 1 else {"permissions_any": list(required)}
            raise ErclaveError("permission_denied", "Required Sales permission is missing.", status_code=403, details=details)
        actor_id = str(user.get("id") or "")
        if not actor_id:
            raise ErclaveError("authorization_service_unavailable", "Authorization context is incomplete.", status_code=503)
        return AuthorizedContext(x_tenant_id, actor_id, required[0])

    return dependency
