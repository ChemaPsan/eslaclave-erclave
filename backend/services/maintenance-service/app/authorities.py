import json
from urllib import error,parse,request
from fastapi import Depends
from erclave_common.config import Settings,get_settings
from erclave_common.errors import ErclaveError

class MaintenanceAuthorityClient:
    def __init__(self,settings):
        self.hr=settings.hr_service_url.rstrip("/");self.inventory=settings.inventory_service_url.rstrip("/");self.production=settings.production_service_url.rstrip("/");self.timeout=settings.authorization_timeout_seconds
    def _call(self,url,tenant,authorization,method="GET",payload=None,key=None):
        headers={"X-Tenant-Id":tenant,"Accept":"application/json"}
        if authorization:headers["Authorization"]=authorization
        if key:headers["Idempotency-Key"]=key
        body=None
        if payload is not None:body=json.dumps(payload).encode();headers["Content-Type"]="application/json"
        try:
            with request.urlopen(request.Request(url,headers=headers,data=body,method=method),timeout=self.timeout) as response:return json.loads(response.read())["data"]
        except error.HTTPError as exc:
            try:details=json.loads(exc.read()).get("error",{})
            except Exception:details={}
            raise ErclaveError(details.get("code","maintenance_dependency_rejected"),details.get("message","An authoritative service rejected Maintenance data."),status_code=exc.code if exc.code<500 else 503) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc:raise ErclaveError("maintenance_dependency_unavailable","An authoritative service is unavailable.",status_code=503) from exc
    def workers(self,tenant,authorization):return self._call(f"{self.hr}/v1/hr/workers/maintenance-eligible",tenant,authorization)
    def machine(self,tenant,machine_id,authorization):return self._call(f"{self.production}/v1/production/machines/{parse.quote(machine_id)}",tenant,authorization)
    def production_order(self,tenant,order_id,authorization):return self._call(f"{self.production}/v1/production/orders/{parse.quote(order_id)}",tenant,authorization)
    def block_machine(self,tenant,machine_id,order_id,source_order_id,authorization,key):return self._call(f"{self.production}/v1/production/machines/{parse.quote(machine_id)}/maintenance-block",tenant,authorization,"POST",{"maintenance_order_id":order_id,"production_order_id":source_order_id},key)
    def release_machine(self,tenant,machine_id,order_id,authorization,key):return self._call(f"{self.production}/v1/production/machines/{parse.quote(machine_id)}/maintenance-release",tenant,authorization,"POST",{"maintenance_order_id":order_id},key)
    def warehouse(self,tenant,warehouse_id,authorization):return self._call(f"{self.inventory}/v1/inventory/warehouses/{parse.quote(warehouse_id)}",tenant,authorization)
    def item(self,tenant,item_id,authorization):return self._call(f"{self.inventory}/v1/inventory/items/{parse.quote(item_id)}",tenant,authorization)
    def reserve(self,tenant,order_id,request_id,line,warehouse_id,authorization,key):return self._call(f"{self.inventory}/v1/inventory/reservation-requests",tenant,authorization,"POST",{"inventory_item_id":line["item_id"],"warehouse_id":warehouse_id,"quantity":line["quantity"],"unit":line["unit_code"],"source":{"type":"maintenance_order","id":order_id,"line_id":line["line_id"]}},key)
    def consume(self,tenant,reservation_id,quantity,authorization,key):return self._call(f"{self.inventory}/v1/inventory/reservations/{parse.quote(reservation_id)}/consume",tenant,authorization,"POST",{"reason":"Maintenance material issue","quantity":quantity},key)
    def release_reservation(self,tenant,reservation_id,authorization,key):return self._call(f"{self.inventory}/v1/inventory/reservations/{parse.quote(reservation_id)}/release",tenant,authorization,"POST",{"reason":"Maintenance request cancelled"},key)
def get_maintenance_authority_client(settings:Settings=Depends(get_settings)):return MaintenanceAuthorityClient(settings)
