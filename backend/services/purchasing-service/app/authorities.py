import json
from urllib import error, parse, request
from fastapi import Depends
from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError

class PurchasingAuthorityClient:
    def __init__(self,settings): self.inventory=settings.inventory_service_url.rstrip("/"); self.admin=settings.admin_service_url.rstrip("/"); self.timeout=settings.authorization_timeout_seconds
    def _call(self,url,tenant,authorization,method="GET",payload=None,key=None):
        headers={"X-Tenant-Id":tenant,"Accept":"application/json"}
        if authorization: headers["Authorization"]=authorization
        if key: headers["Idempotency-Key"]=key
        body=None
        if payload is not None: body=json.dumps(payload).encode(); headers["Content-Type"]="application/json"
        try:
            with request.urlopen(request.Request(url,headers=headers,data=body,method=method),timeout=self.timeout) as response:return json.loads(response.read())["data"]
        except error.HTTPError as exc:
            raise ErclaveError("purchasing_dependency_rejected","An authoritative service rejected Purchasing data.",status_code=422,details={"status":exc.code}) from exc
        except (error.URLError,TimeoutError,KeyError,ValueError) as exc: raise ErclaveError("purchasing_dependency_unavailable","An authoritative service is unavailable.",status_code=503) from exc
    def require_catalog(self,tenant,catalog,code,authorization):
        item=self._call(f"{self.admin}/v1/catalogs/commercial/{parse.quote(catalog)}/by-code/{parse.quote(code)}",tenant,authorization)
        if item.get("status")!="active": raise ErclaveError("catalog_item_not_found","Catalog item is not active.",status_code=422)
        return item
    def item(self,tenant,item_id,authorization): return self._call(f"{self.inventory}/v1/inventory/items/{item_id}",tenant,authorization)
    def warehouse(self,tenant,warehouse_id,authorization): return self._call(f"{self.inventory}/v1/inventory/warehouses/{warehouse_id}",tenant,authorization)
    def receive(self,tenant,line,receipt_id,order_id,authorization,key):
        return self._call(f"{self.inventory}/v1/inventory/purchase-receipts",tenant,authorization,"POST",{"movement_type":"entry","inventory_item_id":line["inventory_item_id"],"warehouse_id":line["warehouse_id"],"quantity":str(line["quantity"]),"unit":line["unit_code"],"unit_cost":str(line["unit_price"]),"reason":f"Purchase receipt {receipt_id}","source":{"type":"purchase_order","id":order_id,"line_id":line["order_line_id"]},"occurred_at":line["received_at"]},key)
def get_purchasing_authority_client(settings:Settings=Depends(get_settings)): return PurchasingAuthorityClient(settings)
