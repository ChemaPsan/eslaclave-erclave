from dataclasses import dataclass
import json
from urllib import error, request
from fastapi import Depends, Header
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError

@dataclass(frozen=True)
class AuthorizedContext: tenant_id: str; actor_id: str; permission: str
class AdminSessionClient:
    def __init__(self, settings): self.base_url=settings.admin_service_url.rstrip("/"); self.timeout=settings.authorization_timeout_seconds
    def get_context(self, tenant_id, authorization):
        req=request.Request(f"{self.base_url}/v1/session/context",headers={"Authorization":authorization,"X-Tenant-Id":tenant_id},method="GET")
        try:
            with request.urlopen(req,timeout=self.timeout) as response: return json.loads(response.read())["data"]
        except error.HTTPError as exc:
            raise ErclaveError("authorization_denied","Inventory authorization failed.",status_code=401 if exc.code==401 else 403) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc:
            raise ErclaveError("authorization_service_unavailable","Authorization service is unavailable.",status_code=503) from exc
def get_admin_session_client(settings: Settings=Depends(get_settings)): return AdminSessionClient(settings)
def require_inventory_access(permission):
    def dependency(x_tenant_id: str|None=Header(None,alias="X-Tenant-Id"), authorization: str|None=Header(None,alias="Authorization"), x_actor_id: str|None=Header(None,alias="X-Actor-Id"), settings: Settings=Depends(get_settings), client: AdminSessionClient=Depends(get_admin_session_client)):
        if not x_tenant_id: raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
        if settings.auth_mode != "firebase": return AuthorizedContext(x_tenant_id,x_actor_id or "usr_demo",permission)
        if not authorization or not authorization.lower().startswith("bearer "): raise ErclaveError("auth_required","Authorization Bearer token is required.",status_code=401)
        context=client.get_context(x_tenant_id,authorization); tenant=context.get("tenant") or {}; user=context.get("user") or {}
        if tenant.get("id") != x_tenant_id or tenant.get("status") != "active": raise ErclaveError("tenant_access_denied","Tenant access denied.",status_code=403)
        if "inventory" not in context.get("active_modules",[]): raise ErclaveError("module_not_enabled","Inventory module is not enabled.",status_code=403)
        if permission not in context.get("permissions",[]): raise ErclaveError("permission_denied","Required permission is missing.",status_code=403,details={"permission":permission})
        return AuthorizedContext(x_tenant_id,str(user.get("id") or ""),permission)
    return dependency
