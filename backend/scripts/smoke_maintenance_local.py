from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib import error, request
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy import create_engine, text


TENANT = "ten_739ee59d765d5e14818674800d"
ACTOR_EMAIL = "admin.qa@erclave.local"
LOCAL_APIS = {
    "admin": "http://127.0.0.1:8000",
    "production": "http://127.0.0.1:8002",
    "inventory": "http://127.0.0.1:8004",
    "hr": "http://127.0.0.1:8006",
    "maintenance": "http://127.0.0.1:8012",
}


def require_local(database_url: str) -> None:
    parsed = urlparse(database_url.replace("postgresql+psycopg", "postgresql", 1))
    if parsed.hostname != "127.0.0.1" or parsed.port != 5434 or parsed.path != "/erclave_local":
        raise RuntimeError("Maintenance smoke requires 127.0.0.1:5434/erclave_local.")
    if any(urlparse(value).hostname != "127.0.0.1" for value in LOCAL_APIS.values()):
        raise RuntimeError("Maintenance smoke accepts loopback APIs only.")


def call(url: str, token: str, method: str = "GET", payload: dict | None = None, key: str | None = None) -> dict:
    headers = {"Accept": "application/json", "X-Tenant-Id": TENANT, "Authorization": f"Bearer {token}"}
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    if key:
        headers["Idempotency-Key"] = key
        headers["X-Correlation-Id"] = key
    try:
        with request.urlopen(request.Request(url, data=body, headers=headers, method=method), timeout=10) as response:
            return json.loads(response.read()).get("data", {})
    except error.HTTPError as exc:
        details = exc.read().decode(errors="replace")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {details}") from exc


def firebase_token() -> str:
    body = json.dumps({"email": ACTOR_EMAIL, "password": "LocalDemo123!", "returnSecureToken": True}).encode()
    url = "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=demo-api-key"
    with request.urlopen(request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=10) as response:
        return json.loads(response.read())["idToken"]


def valid_nss(prefix: str) -> str:
    digits = [int(value) for value in prefix[:10]]
    products = [number * (1 if index % 2 == 0 else 2) for index, number in enumerate(digits)]
    check = (10 - sum(value // 10 + value % 10 for value in products) % 10) % 10
    return prefix[:10] + str(check)


def cleanup(engine, ids: dict[str, str], prefix: str) -> None:
    with engine.begin() as connection:
        order_id = ids.get("order")
        material_id = ids.get("material")
        if order_id:
            connection.execute(text("delete from maintenance.audit_events where tenant_id=:t and entity_id=any(:ids)"), {"t": TENANT, "ids": [value for value in [order_id, material_id, ids.get("time")] if value]})
            connection.execute(text("delete from maintenance.material_request_lines where tenant_id=:t and material_request_id in (select id from maintenance.material_requests where tenant_id=:t and order_id=:o)"), {"t": TENANT, "o": order_id})
            connection.execute(text("delete from maintenance.material_requests where tenant_id=:t and order_id=:o"), {"t": TENANT, "o": order_id})
            connection.execute(text("delete from maintenance.time_entries where tenant_id=:t and order_id=:o"), {"t": TENANT, "o": order_id})
            connection.execute(text("delete from maintenance.assignments where tenant_id=:t and order_id=:o"), {"t": TENANT, "o": order_id})
            connection.execute(text("delete from maintenance.orders where tenant_id=:t and id=:o"), {"t": TENANT, "o": order_id})
        connection.execute(text("delete from maintenance.idempotency_records where tenant_id=:t and (idempotency_key like :prefix or idempotency_key like :order_key or idempotency_key like :material_key)"), {"t": TENANT, "prefix": f"{prefix}%", "order_key": f"maintenance-{order_id or ''}%", "material_key": f"maintenance-{material_id or ''}%"})

        reservation_id = ids.get("reservation")
        item_id = ids.get("item")
        warehouse_id = ids.get("warehouse")
        movement_ids = [value for key, value in ids.items() if key.startswith("movement")]
        inventory_entities = [value for value in [reservation_id, item_id, warehouse_id, *movement_ids] if value]
        if inventory_entities:
            connection.execute(text("delete from inventory.audit_events where tenant_id=:t and entity_id=any(:ids)"), {"t": TENANT, "ids": inventory_entities})
        connection.execute(text("delete from inventory.idempotency_records where tenant_id=:t and (idempotency_key like :prefix or idempotency_key like :order_key or idempotency_key like :material_key)"), {"t": TENANT, "prefix": f"{prefix}%", "order_key": f"maintenance-{order_id or ''}%", "material_key": f"maintenance-{material_id or ''}%"})
        if reservation_id or movement_ids:
            connection.execute(text("delete from inventory.movements where tenant_id=:t and (source_id=:reservation or id=any(:ids))"), {"t": TENANT, "reservation": reservation_id or "", "ids": movement_ids or [""]})
        if reservation_id:
            connection.execute(text("delete from inventory.reservations where tenant_id=:t and id=:reservation"), {"t": TENANT, "reservation": reservation_id})
        if item_id:connection.execute(text("delete from inventory.items where tenant_id=:t and id=:id"), {"t": TENANT, "id": item_id})
        if warehouse_id:connection.execute(text("delete from inventory.warehouses where tenant_id=:t and id=:id"), {"t": TENANT, "id": warehouse_id})

        machine_id = ids.get("machine")
        if machine_id:
            connection.execute(text("delete from production.audit_events where tenant_id=:t and resource_id=:id"), {"t": TENANT, "id": machine_id})
            connection.execute(text("delete from production.machines where tenant_id=:t and id=:id"), {"t": TENANT, "id": machine_id})
        connection.execute(text("delete from production.idempotency_records where tenant_id=:t and (idempotency_key like :prefix or idempotency_key like :order_key)"), {"t": TENANT, "prefix": f"{prefix}%", "order_key": f"maintenance-{order_id or ''}%"})

        worker_id, position_id, area_id = ids.get("worker"), ids.get("position"), ids.get("area")
        hr_entities = [value for value in [worker_id, position_id, area_id] if value]
        if hr_entities:connection.execute(text("delete from hr.audit_events where tenant_id=:t and entity_id=any(:ids)"), {"t": TENANT, "ids": hr_entities})
        connection.execute(text("delete from hr.idempotency_records where tenant_id=:t and idempotency_key like :prefix"), {"t": TENANT, "prefix": f"{prefix}%"})
        if worker_id:connection.execute(text("delete from hr.workers where tenant_id=:t and id=:id"), {"t": TENANT, "id": worker_id})
        if position_id:connection.execute(text("delete from hr.labor_roles where tenant_id=:t and id=:id"), {"t": TENANT, "id": position_id})
        if area_id:connection.execute(text("delete from hr.labor_areas where tenant_id=:t and id=:id"), {"t": TENANT, "id": area_id})


def cleanup_stale_smoke(engine) -> None:
    """Remove only fixtures created by this smoke after an interrupted prior run."""
    with engine.begin() as connection:
        order_ids = connection.execute(text("select id from maintenance.orders where tenant_id=:t and title='Smoke de mantenimiento' and code like 'MT-%'"), {"t": TENANT}).scalars().all()
        material_ids = connection.execute(text("select id from maintenance.material_requests where tenant_id=:t and order_id=any(:ids)"), {"t": TENANT, "ids": order_ids or [""]}).scalars().all()
        time_ids = connection.execute(text("select id from maintenance.time_entries where tenant_id=:t and order_id=any(:ids)"), {"t": TENANT, "ids": order_ids or [""]}).scalars().all()
        if order_ids:
            connection.execute(text("delete from maintenance.audit_events where tenant_id=:t and entity_id=any(:ids)"), {"t": TENANT, "ids": [*order_ids, *material_ids, *time_ids]})
            connection.execute(text("delete from maintenance.material_request_lines where tenant_id=:t and material_request_id=any(:ids)"), {"t": TENANT, "ids": material_ids or [""]})
            connection.execute(text("delete from maintenance.material_requests where tenant_id=:t and order_id=any(:ids)"), {"t": TENANT, "ids": order_ids})
            connection.execute(text("delete from maintenance.time_entries where tenant_id=:t and order_id=any(:ids)"), {"t": TENANT, "ids": order_ids})
            connection.execute(text("delete from maintenance.assignments where tenant_id=:t and order_id=any(:ids)"), {"t": TENANT, "ids": order_ids})
            connection.execute(text("delete from maintenance.orders where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": order_ids})
        connection.execute(text("delete from maintenance.idempotency_records where tenant_id=:t and idempotency_key like 'smoke-maint-%'"), {"t": TENANT})

        item_ids = connection.execute(text("select id from inventory.items where tenant_id=:t and name like 'Refaccion Smoke %'"), {"t": TENANT}).scalars().all()
        warehouse_ids = connection.execute(text("select id from inventory.warehouses where tenant_id=:t and name like 'Refacciones Smoke %'"), {"t": TENANT}).scalars().all()
        reservation_ids = connection.execute(text("select id from inventory.reservations where tenant_id=:t and (inventory_item_id=any(:items) or source_id=any(:orders))"), {"t": TENANT, "items": item_ids or [""], "orders": order_ids or [""]}).scalars().all()
        movement_ids = connection.execute(text("select id from inventory.movements where tenant_id=:t and (inventory_item_id=any(:items) or source_id=any(:reservations) or source_id like 'smoke-maint-%')"), {"t": TENANT, "items": item_ids or [""], "reservations": reservation_ids or [""]}).scalars().all()
        entities = [*item_ids, *warehouse_ids, *reservation_ids, *movement_ids]
        if entities:connection.execute(text("delete from inventory.audit_events where tenant_id=:t and entity_id=any(:ids)"), {"t": TENANT, "ids": entities})
        connection.execute(text("delete from inventory.idempotency_records where tenant_id=:t and idempotency_key like 'smoke-maint-%'"), {"t": TENANT})
        for entity_id in [*order_ids, *material_ids]:connection.execute(text("delete from inventory.idempotency_records where tenant_id=:t and idempotency_key like :key"), {"t": TENANT, "key": f"maintenance-{entity_id}%"})
        if movement_ids:connection.execute(text("delete from inventory.movements where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": movement_ids})
        if reservation_ids:connection.execute(text("delete from inventory.reservations where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": reservation_ids})
        if item_ids:connection.execute(text("delete from inventory.items where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": item_ids})
        if warehouse_ids:connection.execute(text("delete from inventory.warehouses where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": warehouse_ids})

        machine_ids = connection.execute(text("select id from production.machines where tenant_id=:t and name like 'Maquina Smoke %'"), {"t": TENANT}).scalars().all()
        if machine_ids:
            connection.execute(text("delete from production.audit_events where tenant_id=:t and resource_id=any(:ids)"), {"t": TENANT, "ids": machine_ids})
            connection.execute(text("delete from production.machines where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": machine_ids})
        connection.execute(text("delete from production.idempotency_records where tenant_id=:t and idempotency_key like 'smoke-maint-%'"), {"t": TENANT})
        for order_id in order_ids:connection.execute(text("delete from production.idempotency_records where tenant_id=:t and idempotency_key like :key"), {"t": TENANT, "key": f"maintenance-{order_id}%"})

        area_ids = connection.execute(text("select id from hr.labor_areas where tenant_id=:t and name like 'Mantenimiento Smoke %'"), {"t": TENANT}).scalars().all()
        position_ids = connection.execute(text("select id from hr.labor_roles where tenant_id=:t and labor_area_id=any(:ids)"), {"t": TENANT, "ids": area_ids or [""]}).scalars().all()
        worker_ids = connection.execute(text("select id from hr.workers where tenant_id=:t and labor_position_id=any(:ids)"), {"t": TENANT, "ids": position_ids or [""]}).scalars().all()
        hr_entities = [*area_ids, *position_ids, *worker_ids]
        if hr_entities:connection.execute(text("delete from hr.audit_events where tenant_id=:t and entity_id=any(:ids)"), {"t": TENANT, "ids": hr_entities})
        connection.execute(text("delete from hr.idempotency_records where tenant_id=:t and idempotency_key like 'smoke-maint-%'"), {"t": TENANT})
        if worker_ids:connection.execute(text("delete from hr.workers where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": worker_ids})
        if position_ids:connection.execute(text("delete from hr.labor_roles where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": position_ids})
        if area_ids:connection.execute(text("delete from hr.labor_areas where tenant_id=:t and id=any(:ids)"), {"t": TENANT, "ids": area_ids})


def main() -> int:
    database_url = os.getenv("ERCLAVE_DATABASE_URL", "")
    if not database_url:
        env_path = Path(__file__).resolve().parents[1] / ".env"
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("ERCLAVE_INVENTORY_DATABASE_URL="):
                database_url = line.split("=", 1)[1]
                break
    require_local(database_url)
    engine = create_engine(database_url, pool_pre_ping=True)
    cleanup_stale_smoke(engine)
    suffix = uuid4().hex[:8].upper()
    digits = "".join(str(random.SystemRandom().randrange(10)) for _ in range(10))
    prefix = f"smoke-maint-{suffix.lower()}"
    ids: dict[str, str] = {}
    token = firebase_token()
    key = lambda action: f"{prefix}-{action}"
    try:
        area = call(f"{LOCAL_APIS['hr']}/v1/hr/areas", token, "POST", {"code": f"MNT-{suffix}", "name": f"Mantenimiento Smoke {suffix}"}, key("area"));ids["area"] = area["id"]
        position = call(f"{LOCAL_APIS['hr']}/v1/hr/positions", token, "POST", {"labor_area_id": area["id"], "position": f"Tecnico Smoke {suffix}", "recipe_name": f"Mantenimiento {suffix}", "intervenes_in_maintenance": True}, key("position"));ids["position"] = position["id"]
        worker = call(f"{LOCAL_APIS['hr']}/v1/hr/workers", token, "POST", {"employee_number": f"SM-{suffix}", "first_names": "Tecnico", "first_last_name": f"Smoke{suffix}", "curp": f"SOAT900101HDFMKL{suffix[:1]}0", "rfc": f"SOAT900101{suffix[:3]}", "nss": valid_nss(digits), "hire_date": "2026-01-01", "labor_position_id": position["id"]}, key("worker"));ids["worker"] = worker["id"]

        warehouse = call(f"{LOCAL_APIS['inventory']}/v1/inventory/warehouses", token, "POST", {"code": f"REF-{suffix}", "name": f"Refacciones Smoke {suffix}", "type": "spare_parts", "business_center": "Matriz", "location": "Pruebas", "owner": "Mantenimiento"}, key("warehouse"));ids["warehouse"] = warehouse["id"]
        item = call(f"{LOCAL_APIS['inventory']}/v1/inventory/items", token, "POST", {"code": f"R-{suffix}", "name": f"Refaccion Smoke {suffix}", "type": "sparePart", "base_unit": "H87", "inventory_policy": "standard", "suggested_warehouse_id": warehouse["id"], "default_unit_cost": 10}, key("item"));ids["item"] = item["id"]
        movement = call(f"{LOCAL_APIS['inventory']}/v1/inventory/movements", token, "POST", {"movement_type": "entry", "inventory_item_id": item["id"], "warehouse_id": warehouse["id"], "quantity": 5, "unit": "H87", "unit_cost": 10, "reason": "Fixture smoke mantenimiento", "source": {"type": "manual", "id": prefix}, "occurred_at": datetime.now(timezone.utc).isoformat()}, key("stock"));ids["movement_stock"] = movement["id"]

        machine = call(f"{LOCAL_APIS['production']}/v1/production/machines", token, "POST", {"code": f"MQ-{suffix}", "name": f"Maquina Smoke {suffix}", "machine_type": "Prueba", "area_ref_id": area["id"], "area_name": area["name"], "available_minutes_per_day": 480, "cost_per_minute": 1}, key("machine"));ids["machine"] = machine["id"]
        order = call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders", token, "POST", {"code": f"MT-{suffix}", "target_type": "production_machine", "production_machine_id": machine["id"], "source_type": "manual", "priority": "high", "title": "Smoke de mantenimiento", "description": "Validacion integral del flujo", "location": "Area de pruebas"}, key("order"));ids["order"] = order["id"]
        order = call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/transitions", token, "POST", {"transition": "request"}, key("request"))
        if order["integration_status"] != "completed":raise RuntimeError("Machine block did not reconcile.")
        call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/transitions", token, "POST", {"transition": "assign", "assigned_worker_id": worker["id"]}, key("assign"))
        call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/transitions", token, "POST", {"transition": "start"}, key("start"))
        ended = datetime.now(timezone.utc) - timedelta(minutes=1)
        time_entry = call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/time-entries", token, "POST", {"worker_id": worker["id"], "started_at": (ended - timedelta(minutes=20)).isoformat(), "ended_at": ended.isoformat(), "notes": "Smoke"}, key("time"));ids["time"] = time_entry["id"]
        material = call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/material-requests", token, "POST", {"warehouse_id": warehouse["id"], "lines": [{"item_id": item["id"], "quantity": 2, "unit_code": "H87"}]}, key("material"));ids["material"] = material["id"];ids["reservation"] = material["lines"][0]["reservation_id"]
        call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}", token, "PATCH", {"diagnosis": "Prueba controlada", "work_performed": "Validacion completa", "verification_notes": "Resultado correcto"}, key("evidence"))
        resolved = call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/transitions", token, "POST", {"transition": "resolve"}, key("resolve"))
        ids["movement_issue"] = resolved["material_requests"][0]["lines"][0]["inventory_movement_id"]
        closed = call(f"{LOCAL_APIS['maintenance']}/v1/maintenance/orders/{order['id']}/transitions", token, "POST", {"transition": "close"}, key("close"))
        machine_after = call(f"{LOCAL_APIS['production']}/v1/production/machines/{machine['id']}", token)
        if closed["status"] != "closed" or closed["integration_status"] != "completed" or machine_after["status"] != "active":
            raise RuntimeError("Maintenance smoke did not close with the machine released.")
        print(json.dumps({"status": "ok", "flow": "machine->assignment->time->parts->resolve->close", "tenant": TENANT}))
        return 0
    finally:
        cleanup(engine, ids, prefix)


if __name__ == "__main__":
    raise SystemExit(main())
