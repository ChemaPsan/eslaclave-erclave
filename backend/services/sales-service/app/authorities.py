import json
from urllib import error, parse, request

from fastapi import Depends

from erclave_common.config import Settings, get_settings
from erclave_common.errors import ErclaveError

from .schemas import ProductReference, WorkerReference


class SalesAuthorityClient:
    def __init__(self, settings: Settings):
        self.admin_url = settings.admin_service_url.rstrip("/")
        self.hr_url = settings.hr_service_url.rstrip("/")
        self.production_url = settings.production_service_url.rstrip("/")
        self.inventory_url = settings.inventory_service_url.rstrip("/")
        self.timeout = settings.authorization_timeout_seconds

    def _call(self, url: str, tenant_id: str, authorization: str | None, method: str = "GET", payload: dict | None = None, idempotency_key: str | None = None) -> dict:
        headers = {"Authorization": authorization or "", "X-Tenant-Id": tenant_id, "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        call = request.Request(url, headers=headers, data=json.dumps(payload).encode("utf-8") if payload is not None else None, method=method)
        try:
            with request.urlopen(call, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))["data"]
        except error.HTTPError as exc:
            if exc.code == 404:
                raise ErclaveError("authoritative_reference_not_found", "An authoritative Sales reference does not exist or is inactive.", status_code=422) from exc
            raise ErclaveError("authority_validation_denied", "An authority rejected Sales reference validation.", status_code=403 if exc.code in (401, 403) else 503) from exc
        except (error.URLError, TimeoutError, KeyError, ValueError) as exc:
            raise ErclaveError("authority_unavailable", "A Sales authority is unavailable.", status_code=503) from exc

    def _get(self, url: str, tenant_id: str, authorization: str | None) -> dict:
        return self._call(url, tenant_id, authorization)

    def get_worker(self, tenant_id: str, worker_id: str, authorization: str | None) -> WorkerReference:
        rows = self._get(f"{self.hr_url}/v1/hr/workers/sales-eligible", tenant_id, authorization)
        row = next((item for item in rows if item.get("id") == worker_id), None)
        if row is None:
            raise ErclaveError("sales_responsible_invalid", "Responsible must be an active HR worker in an active position.", status_code=422)
        return WorkerReference.model_validate(row)

    def get_product(self, tenant_id: str, product_id: str, authorization: str | None) -> ProductReference:
        row = self._get(f"{self.production_url}/v1/production/product-services/{parse.quote(product_id)}", tenant_id, authorization)
        if row.get("status") != "active":
            raise ErclaveError("product_service_inactive", "Quoted product or service must be active.", status_code=422)
        product = ProductReference.model_validate(row)
        if product.type == "product" and not product.inventory_item_id:
            raise ErclaveError("product_inventory_mapping_required", "A sold product must map to an authoritative Inventory item.", status_code=422)
        return product

    def get_inventory_item(self, tenant_id: str, item_id: str, authorization: str | None) -> dict:
        row = self._get(f"{self.inventory_url}/v1/inventory/items/{parse.quote(item_id)}", tenant_id, authorization)
        if row.get("status") != "active" or row.get("type") != "finishedGood":
            raise ErclaveError("inventory_item_invalid", "Mapped Inventory item must be an active finished good.", status_code=422)
        return row

    def require_unit(self, tenant_id: str, code: str, authorization: str | None) -> str:
        row = self._get(f"{self.admin_url}/v1/catalogs/units-of-measure/by-code/{parse.quote(code.upper())}", tenant_id, authorization)
        return str(row["code"]).upper()

    def list_catalog(self, tenant_id: str, catalog_code: str, authorization: str | None) -> list[dict]:
        return self._get(f"{self.admin_url}/v1/catalogs/commercial/{parse.quote(catalog_code)}", tenant_id, authorization)

    def require_catalog_item(self, tenant_id: str, catalog_code: str, code: str, authorization: str | None) -> str:
        row = self._get(f"{self.admin_url}/v1/catalogs/commercial/{parse.quote(catalog_code)}/by-code/{parse.quote(code)}", tenant_id, authorization)
        return str(row["code"])

    def reserve_stock(self, tenant_id: str, order_id: str, order_line_id: str, inventory_item_id: str, warehouse_id: str, quantity, unit: str, authorization: str | None, idempotency_key: str) -> dict:
        return self._call(f"{self.inventory_url}/v1/inventory/reservation-requests", tenant_id, authorization, "POST", {
            "inventory_item_id": inventory_item_id, "warehouse_id": warehouse_id, "quantity": str(quantity), "unit": unit,
            "source": {"type": "sales_order", "id": order_id, "line_id": order_line_id},
        }, idempotency_key)

    def release_reservation(self, tenant_id: str, reservation_id: str, reason: str, authorization: str | None, idempotency_key: str) -> dict:
        return self._call(f"{self.inventory_url}/v1/inventory/reservations/{parse.quote(reservation_id)}/release", tenant_id, authorization, "POST", {"reason": reason}, idempotency_key)

    def consume_reservation(self, tenant_id: str, reservation_id: str, quantity, reason: str, authorization: str | None, idempotency_key: str) -> dict:
        return self._call(f"{self.inventory_url}/v1/inventory/reservations/{parse.quote(reservation_id)}/consume", tenant_id, authorization, "POST", {"reason": reason, "quantity": str(quantity)}, idempotency_key)

    def request_production(self, tenant_id: str, order_id: str, order_line, due_date, authorization: str | None, idempotency_key: str) -> dict:
        return self._call(f"{self.production_url}/v1/production/order-requests", tenant_id, authorization, "POST", {
            "sales_order_id": order_id, "sales_order_line_id": order_line.id, "product_service_id": order_line.product_service_id,
            "quantity": str(order_line.ordered_quantity - order_line.delivered_quantity), "unit": order_line.unit,
            "requested_due_date": due_date.isoformat() if due_date else None,
        }, idempotency_key)


def get_sales_authority_client(settings: Settings = Depends(get_settings)) -> SalesAuthorityClient:
    return SalesAuthorityClient(settings)
