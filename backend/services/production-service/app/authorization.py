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
        session_request = request.Request(
            f"{self.base_url}/v1/session/context",
            headers={"Authorization": authorization, "X-Tenant-Id": tenant_id, "Accept": "application/json"},
            method="GET",
        )
        try:
            with request.urlopen(session_request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))["data"]
        except error.HTTPError as exc:
            if exc.code == 401:
                raise ErclaveError("invalid_token", "Authentication token is invalid or expired.", status_code=401) from exc
            if exc.code in (403, 404):
                raise ErclaveError("tenant_access_denied", "Authenticated actor cannot access this tenant.", status_code=403) from exc
            raise ErclaveError("authorization_service_unavailable", "Authorization service is unavailable.", status_code=503) from exc
        except (error.URLError, TimeoutError, KeyError, ValueError) as exc:
            raise ErclaveError("authorization_service_unavailable", "Authorization service is unavailable.", status_code=503) from exc


def get_admin_session_client(settings: Settings = Depends(get_settings)) -> AdminSessionClient:
    return AdminSessionClient(settings)


def require_production_access(permission: str):
    def dependency(
        x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
        authorization: str | None = Header(default=None, alias="Authorization"),
        x_actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
        settings: Settings = Depends(get_settings),
        client: AdminSessionClient = Depends(get_admin_session_client),
    ) -> AuthorizedContext:
        if not x_tenant_id:
            raise ErclaveError("tenant_required", "X-Tenant-Id header is required.", status_code=400)
        if settings.auth_mode != "firebase":
            return AuthorizedContext(tenant_id=x_tenant_id, actor_id=x_actor_id or "usr_demo", permission=permission)
        if not authorization or not authorization.lower().startswith("bearer ") or not authorization.split(" ", 1)[1].strip():
            raise ErclaveError("auth_required", "Authorization Bearer token is required.", status_code=401)

        context = client.get_context(x_tenant_id, authorization)
        tenant = context.get("tenant") or {}
        user = context.get("user") or {}
        if tenant.get("id") != x_tenant_id or tenant.get("status") != "active":
            raise ErclaveError("tenant_access_denied", "Authenticated actor cannot access this tenant.", status_code=403)
        if "production" not in context.get("active_modules", []):
            raise ErclaveError("module_not_enabled", "Production module is not enabled for this tenant.", status_code=403)
        if permission not in context.get("permissions", []):
            raise ErclaveError("permission_denied", "Authenticated actor does not have the required permission.", status_code=403, details={"permission": permission})
        actor_id = str(user.get("id") or "")
        if not actor_id:
            raise ErclaveError("authorization_service_unavailable", "Authorization context is incomplete.", status_code=503)
        return AuthorizedContext(tenant_id=x_tenant_id, actor_id=actor_id, permission=permission)

    return dependency
