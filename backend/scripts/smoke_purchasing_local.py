from __future__ import annotations

import json
import os
from datetime import date, timedelta
from urllib import error, request
from uuid import uuid4

from sqlalchemy import create_engine, text


TENANT_ID = "ten_739ee59d765d5e14818674800d"
ACTOR_EMAIL = "admin.qa@erclave.local"
ACTOR_PASSWORD = "LocalDemo123!"
AUTH_URL = "http://127.0.0.1:9099"
PURCHASING_URL = "http://127.0.0.1:8010"
INVENTORY_URL = "http://127.0.0.1:8004"


def call(base: str, path: str, token: str, method: str = "GET", payload=None, key: str | None = None):
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": TENANT_ID, "Accept": "application/json"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if key:
        headers["Idempotency-Key"] = key
    with request.urlopen(request.Request(f"{base}{path}", data=body, headers=headers, method=method), timeout=10) as response:
        return json.loads(response.read()).get("data")


def main() -> int:
    database_url = os.environ.get("ERCLAVE_DATABASE_URL", "")
    if "@127.0.0.1:5434/erclave_local" not in database_url:
        raise RuntimeError("Guardrail: smoke only accepts Local erclave_local on 127.0.0.1:5434.")
    login_payload = json.dumps({"email": ACTOR_EMAIL, "password": ACTOR_PASSWORD, "returnSecureToken": True}).encode()
    with request.urlopen(request.Request(f"{AUTH_URL}/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo-api-key", data=login_payload, headers={"Content-Type": "application/json"}, method="POST"), timeout=10) as response:
        token = json.loads(response.read())["idToken"]

    suffix = uuid4().hex[:8].upper()
    key_prefix = f"smoke-{suffix.lower()}"
    entity_ids: list[str] = []
    movement_ids: list[str] = []
    inventory_keys: list[str] = []
    engine = create_engine(database_url)
    try:
        items = [item for item in call(INVENTORY_URL, "/v1/inventory/items?status=active", token) if item["status"] == "active"][:2]
        warehouses = [item for item in call(INVENTORY_URL, "/v1/inventory/warehouses", token) if item["status"] == "active"]
        if len(items) < 2 or not warehouses:
            raise RuntimeError("Local smoke requires two active Inventory items and one active warehouse.")
        warehouse = call(INVENTORY_URL, f"/v1/inventory/warehouses/{warehouses[0]['id']}", token)
        if warehouse["id"] != warehouses[0]["id"]:
            raise AssertionError("Warehouse detail boundary returned an unexpected resource.")

        supplier = call(PURCHASING_URL, "/v1/purchasing/suppliers", token, "POST", {
            "code": f"SMK-{suffix}", "commercial_name": "Proveedor Smoke CHG-232", "legal_name": "PROVEEDOR SMOKE CHG 232 SA DE CV",
            "tax_id": f"SMK260824{suffix[:3]}", "tax_regime": "601", "billing_email": f"smoke-{suffix.lower()}@example.com",
            "fiscal_postal_code": "01234", "fiscal_country": "MX", "currency": "MXN", "payment_terms": "cash"
        }, f"{key_prefix}-supplier")
        entity_ids.append(supplier["id"])
        requisition_lines = [{"line_type": "inventory_item", "inventory_item_id": item["id"], "description": item["name"], "quantity": 2, "unit_code": item["base_unit"]} for item in items]
        requisition = call(PURCHASING_URL, "/v1/purchasing/requisitions", token, "POST", {"code": f"REQ-{suffix}", "required_date": str(date.today() + timedelta(days=7)), "priority": "normal", "source_type": "manual", "lines": requisition_lines}, f"{key_prefix}-req")
        entity_ids.append(requisition["id"])
        call(PURCHASING_URL, f"/v1/purchasing/requisitions/{requisition['id']}/submit", token, "POST", key=f"{key_prefix}-submit")
        call(PURCHASING_URL, f"/v1/purchasing/requisitions/{requisition['id']}/approve", token, "POST", key=f"{key_prefix}-approve")
        order_lines = [{**line, "unit_price": 10 + index} for index, line in enumerate(requisition_lines)]
        mismatch = [{**line, "quantity": 3 if index == 0 else line["quantity"]} for index, line in enumerate(order_lines)]
        try:
            call(PURCHASING_URL, "/v1/purchasing/orders", token, "POST", {"code": f"BAD-{suffix}", "requisition_id": requisition["id"], "supplier_id": supplier["id"], "currency": "MXN", "payment_terms": "cash", "lines": mismatch}, f"{key_prefix}-mismatch")
            raise AssertionError("Mismatched order was unexpectedly accepted.")
        except error.HTTPError as exc:
            if exc.code != 409:
                raise
        order = call(PURCHASING_URL, "/v1/purchasing/orders", token, "POST", {"code": f"OC-{suffix}", "requisition_id": requisition["id"], "supplier_id": supplier["id"], "currency": "MXN", "payment_terms": "cash", "lines": order_lines}, f"{key_prefix}-order")
        entity_ids.append(order["id"])
        edited_lines = [{**line, "unit_price": line["unit_price"] + 1} for line in order_lines]
        order = call(PURCHASING_URL, f"/v1/purchasing/orders/{order['id']}", token, "PATCH", {"code": order["code"], "requisition_id": requisition["id"], "supplier_id": supplier["id"], "currency": "MXN", "payment_terms": "cash", "lines": edited_lines}, f"{key_prefix}-order-edit")
        order = call(PURCHASING_URL, f"/v1/purchasing/orders/{order['id']}/issue", token, "POST", key=f"{key_prefix}-issue")
        receipt_lines = [{"order_line_id": line["id"], "quantity": 1, "warehouse_id": warehouse["id"]} for line in order["lines"]]
        try:
            invalid_lines = [{**line, "warehouse_id": "wh_missing"} for line in receipt_lines]
            call(PURCHASING_URL, "/v1/purchasing/receipts", token, "POST", {"code": f"BADREC-{suffix}", "purchase_order_id": order["id"], "received_at": "2026-08-24T18:00:00Z", "lines": invalid_lines}, f"{key_prefix}-bad-warehouse")
            raise AssertionError("Invalid warehouse was unexpectedly persisted.")
        except error.HTTPError as exc:
            if exc.code != 422:
                raise
        receipt = call(PURCHASING_URL, "/v1/purchasing/receipts", token, "POST", {"code": f"REC-{suffix}", "purchase_order_id": order["id"], "received_at": "2026-08-24T18:00:00Z", "supplier_document_reference": f"REM-{suffix}", "lines": receipt_lines}, f"{key_prefix}-receipt")
        entity_ids.append(receipt["id"])
        movement_ids.extend(line["inventory_movement_ref_id"] for line in receipt["lines"] if line["inventory_movement_ref_id"])
        inventory_keys.extend(line["inventory_idempotency_key"] for line in receipt["lines"])
        if receipt["status"] != "completed" or len(movement_ids) != 2:
            raise AssertionError("Multi-line receipt did not complete both Inventory movements.")
        cancelled = call(PURCHASING_URL, f"/v1/purchasing/orders/{order['id']}/cancel", token, "POST", {"reason": "Fin de smoke CHG-232"}, f"{key_prefix}-cancel-order")
        if cancelled["status"] != "cancelled" or any(float(line["received_quantity"]) != 1 for line in cancelled["lines"]):
            raise AssertionError("Partial receipt quantities were not preserved when cancelling the order.")
        print(json.dumps({"warehouse_detail": "ok", "invalid_warehouse_status": 422, "mismatch_status": 409, "receipt_status": receipt["status"], "receipt_lines": len(receipt["lines"]), "movement_count": len(movement_ids), "cancelled_after_partial": cancelled["status"]}))
        return 0
    finally:
        with engine.begin() as connection:
            if movement_ids:
                connection.execute(text("delete from inventory.audit_events where tenant_id=:tenant and entity_id=any(:ids)"), {"tenant": TENANT_ID, "ids": movement_ids})
                connection.execute(text("delete from inventory.movements where tenant_id=:tenant and id=any(:ids)"), {"tenant": TENANT_ID, "ids": movement_ids})
            if inventory_keys:
                connection.execute(text("delete from inventory.idempotency_records where tenant_id=:tenant and idempotency_key=any(:keys)"), {"tenant": TENANT_ID, "keys": inventory_keys})
            connection.execute(text("delete from purchasing.audit_events where tenant_id=:tenant and (entity_id=any(:ids) or actor_id='smoke')"), {"tenant": TENANT_ID, "ids": entity_ids or ["none"]})
            connection.execute(text("delete from purchasing.idempotency_records where tenant_id=:tenant and idempotency_key like :prefix"), {"tenant": TENANT_ID, "prefix": f"{key_prefix}%"})
            connection.execute(text("delete from purchasing.purchase_receipt_lines where tenant_id=:tenant and receipt_id=any(select id from purchasing.purchase_receipts where tenant_id=:tenant and code=:code)"), {"tenant": TENANT_ID, "code": f"REC-{suffix}"})
            connection.execute(text("delete from purchasing.purchase_receipts where tenant_id=:tenant and code=:code"), {"tenant": TENANT_ID, "code": f"REC-{suffix}"})
            connection.execute(text("delete from purchasing.purchase_order_lines where tenant_id=:tenant and purchase_order_id=any(select id from purchasing.purchase_orders where tenant_id=:tenant and code=:code)"), {"tenant": TENANT_ID, "code": f"OC-{suffix}"})
            connection.execute(text("delete from purchasing.purchase_orders where tenant_id=:tenant and code=:code"), {"tenant": TENANT_ID, "code": f"OC-{suffix}"})
            connection.execute(text("delete from purchasing.requisition_lines where tenant_id=:tenant and requisition_id=any(select id from purchasing.requisitions where tenant_id=:tenant and code=:code)"), {"tenant": TENANT_ID, "code": f"REQ-{suffix}"})
            connection.execute(text("delete from purchasing.requisitions where tenant_id=:tenant and code=:code"), {"tenant": TENANT_ID, "code": f"REQ-{suffix}"})
            connection.execute(text("delete from purchasing.suppliers where tenant_id=:tenant and code=:code"), {"tenant": TENANT_ID, "code": f"SMK-{suffix}"})


if __name__ == "__main__":
    raise SystemExit(main())
