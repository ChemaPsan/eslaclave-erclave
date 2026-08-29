from dataclasses import dataclass
import json
from urllib import error,request
from fastapi import Depends,Header
from erclave_common.config import Settings,get_settings
from erclave_common.errors import ErclaveError

@dataclass(frozen=True)
class AuthorizedContext:
    tenant_id:str
    actor_id:str
    permission:str
    permissions:frozenset[str]

    def require(self,permission:str)->None:
        if permission not in self.permissions:
            raise ErclaveError("permission_denied","Required Maintenance permission is missing.",status_code=403,details={"permission":permission})

class AdminSessionClient:
    def __init__(self,settings):self.base_url=settings.admin_service_url.rstrip("/");self.timeout=settings.authorization_timeout_seconds
    def get_context(self,tenant,authorization):
        try:
            with request.urlopen(request.Request(f"{self.base_url}/v1/session/context",headers={"Authorization":authorization,"X-Tenant-Id":tenant}),timeout=self.timeout) as response:return json.loads(response.read())["data"]
        except (error.URLError,error.HTTPError,KeyError,ValueError) as exc:raise ErclaveError("maintenance_authorization_denied","Maintenance authorization failed.",status_code=403) from exc
def get_admin_session_client(settings:Settings=Depends(get_settings)):return AdminSessionClient(settings)
def require_maintenance_access(permission):
    def dependency(x_tenant_id:str|None=Header(None,alias="X-Tenant-Id"),authorization:str|None=Header(None,alias="Authorization"),x_actor_id:str|None=Header(None,alias="X-Actor-Id"),settings:Settings=Depends(get_settings),client=Depends(get_admin_session_client)):
        if not x_tenant_id:raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
        required=(permission,) if isinstance(permission,str) else tuple(permission)
        if settings.auth_mode!="firebase":return AuthorizedContext(x_tenant_id,x_actor_id or "usr_demo",required[0],frozenset(required))
        if not authorization or not authorization.lower().startswith("bearer "):raise ErclaveError("auth_required","Authorization Bearer token is required.",status_code=401)
        context=client.get_context(x_tenant_id,authorization);tenant=context.get("tenant") or {};user=context.get("user") or {}
        if tenant.get("id")!=x_tenant_id or tenant.get("status")!="active":raise ErclaveError("tenant_access_denied","Tenant access denied.",status_code=403)
        if "maintenance" not in context.get("active_modules",[]):raise ErclaveError("module_not_enabled","Maintenance module is not enabled.",status_code=403)
        if not any(item in context.get("permissions",[]) for item in required):raise ErclaveError("permission_denied","Required Maintenance permission is missing.",status_code=403,details={"permission":required[0]} if len(required)==1 else {"permissions_any":list(required)})
        return AuthorizedContext(x_tenant_id,str(user.get("id") or ""),required[0],frozenset(context.get("permissions",[])))
    return dependency
