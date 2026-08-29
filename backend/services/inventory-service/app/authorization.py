from dataclasses import dataclass
import json
from urllib import error, request
from urllib.parse import quote
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
class UnitCatalogClient:
    def __init__(self,settings): self.base_url=settings.admin_service_url.rstrip("/"); self.timeout=settings.authorization_timeout_seconds
    def resolve_active(self,tenant_id,code,authorization=None):
        normalized=code.strip().upper()
        req=request.Request(f"{self.base_url}/v1/catalogs/units-of-measure/by-code/{normalized}",headers={"Authorization":authorization or "","X-Tenant-Id":tenant_id},method="GET")
        try:
            with request.urlopen(req,timeout=self.timeout) as response:return json.loads(response.read().decode("utf-8"))["data"]
        except error.HTTPError as exc:
            if exc.code==404: raise ErclaveError("unit_of_measure_invalid","Unit of measure is not active in the tenant catalog.",status_code=422,details={"code":normalized}) from exc
            raise ErclaveError("unit_catalog_validation_denied","Unit catalog rejected validation.",status_code=403 if exc.code in (401,403) else 503) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc: raise ErclaveError("unit_catalog_unavailable","Unit-of-measure catalog is unavailable.",status_code=503) from exc
    def require_active(self,tenant_id,code,authorization=None):
        return self.resolve_active(tenant_id,code,authorization)["code"].upper()
def get_unit_catalog_client(settings: Settings=Depends(get_settings)): return UnitCatalogClient(settings)
class ProductionOrderClient:
    def __init__(self,settings): self.base_url=settings.production_service_url.rstrip("/"); self.timeout=settings.authorization_timeout_seconds
    def _get(self,path,tenant_id,authorization):
        req=request.Request(f"{self.base_url}{path}",headers={"Authorization":authorization or "","X-Tenant-Id":tenant_id},method="GET")
        try:
            with request.urlopen(req,timeout=self.timeout) as response:return json.loads(response.read().decode("utf-8"))["data"]
        except error.HTTPError as exc:
            if exc.code==404: raise ErclaveError("production_reference_not_found","The production order or product was not found.",status_code=404) from exc
            raise ErclaveError("production_reference_denied","Production rejected finished-goods receipt validation.",status_code=403 if exc.code in (401,403) else 503) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc: raise ErclaveError("production_service_unavailable","Production service is unavailable.",status_code=503) from exc
    def get_finished_goods_candidate(self,tenant_id,order_id,authorization=None): return self._get(f"/v1/production/finished-goods-candidates/{quote(str(order_id),safe='')}",tenant_id,authorization)
def get_production_order_client(settings: Settings=Depends(get_settings)): return ProductionOrderClient(settings)
def require_inventory_access(permission):
    def dependency(x_tenant_id: str|None=Header(None,alias="X-Tenant-Id"), authorization: str|None=Header(None,alias="Authorization"), x_actor_id: str|None=Header(None,alias="X-Actor-Id"), settings: Settings=Depends(get_settings), client: AdminSessionClient=Depends(get_admin_session_client)):
        if not x_tenant_id: raise ErclaveError("tenant_required","X-Tenant-Id header is required.",status_code=400)
        required=(permission,) if isinstance(permission,str) else tuple(permission)
        if settings.auth_mode != "firebase": return AuthorizedContext(x_tenant_id,x_actor_id or "usr_demo",required[0])
        if not authorization or not authorization.lower().startswith("bearer "): raise ErclaveError("auth_required","Authorization Bearer token is required.",status_code=401)
        context=client.get_context(x_tenant_id,authorization); tenant=context.get("tenant") or {}; user=context.get("user") or {}
        if tenant.get("id") != x_tenant_id or tenant.get("status") != "active": raise ErclaveError("tenant_access_denied","Tenant access denied.",status_code=403)
        if "inventory" not in context.get("active_modules",[]): raise ErclaveError("module_not_enabled","Inventory module is not enabled.",status_code=403)
        if not any(item in context.get("permissions",[]) for item in required): raise ErclaveError("permission_denied","Required permission is missing.",status_code=403,details={"permission":required[0]} if len(required)==1 else {"permissions_any":list(required)})
        return AuthorizedContext(x_tenant_id,str(user.get("id") or ""),required[0])
    return dependency
