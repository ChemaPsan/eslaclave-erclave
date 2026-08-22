from dataclasses import dataclass
from pathlib import Path
import re

from .catalog import MODULE_CODES


PERMISSION_LINE_RE = re.compile(r"x-permissions:\s*\[(?P<permissions>[^\]]*)\]")
REQUIRED_MODULE_RE = re.compile(r"x-required-module:\s*(?P<module>[A-Za-z0-9_-]+)")


@dataclass(frozen=True)
class PermissionSeed:
    code: str
    module_code: str
    resource: str
    action: str
    description: str
    display_name_es: str
    display_name_en: str
    description_es: str
    description_en: str
    classification: str
    assignable_to_tenant_role: bool
    risk_level: str
    sort_order: int
    status: str = "active"


MODULE_LABELS = {
    "admin": ("Administracion", "Administration"), "production": ("Produccion", "Production"),
    "hr": ("Recursos Humanos", "Human Resources"), "inventory": ("Almacenes", "Inventory"),
    "sales": ("Ventas", "Sales"), "billing": ("Suscripcion", "Subscription"),
    "integrations": ("Integraciones", "Integrations"),
}
MODULE_ORDER = {"admin": 10, "production": 20, "hr": 25, "inventory": 30, "sales": 40, "billing": 50, "integrations": 70}
RESOURCE_LABELS = {
    "business_unit": ("unidades de negocio", "business units"), "entitlement": ("modulos del tenant", "tenant modules"),
    "role": ("roles", "roles"), "role.permissions": ("permisos de roles", "role permissions"),
    "setting": ("configuracion", "settings"), "tenant": ("datos del tenant", "tenant data"), "user": ("usuarios", "users"),
    "area": ("areas", "areas"), "position": ("puestos", "positions"), "worker": ("trabajadores", "workers"), "machine": ("maquinaria", "machines"),
    "order": ("ordenes", "orders"), "order.status": ("estado de ordenes", "order status"), "order_stage": ("etapas de orden", "order stages"),
    "product_service": ("productos y servicios", "products and services"), "product_service.status": ("estado de productos y servicios", "product and service status"),
    "recipe": ("recetas", "recipes"), "availability": ("disponibilidad", "availability"), "balance": ("inventario", "inventory balances"),
    "item": ("articulos", "items"), "kardex": ("kardex", "kardex"), "location": ("ubicaciones", "locations"),
    "movement": ("movimientos", "movements"), "reservation": ("reservas", "reservations"), "warehouse": ("almacenes", "warehouses"),
    "customer": ("clientes", "customers"), "delivery": ("entregas", "deliveries"), "quote": ("cotizaciones", "quotes"),
    "catalog": ("catalogos", "catalogs"),
    "return": ("devoluciones", "returns"), "subscription": ("suscripciones", "subscriptions"),
    "api_client": ("clientes API", "API clients"), "scope": ("alcances de integracion", "integration scopes"), "usage": ("uso de integraciones", "integration usage"),
}
ACTION_LABELS = {
    "read": ("Ver", "View"), "list": ("Ver", "View"), "create": ("Crear", "Create"), "update": ("Editar", "Edit"),
    "delete": ("Eliminar", "Delete"), "disable": ("Deshabilitar", "Disable"), "invite": ("Invitar", "Invite"),
    "manage": ("Administrar", "Manage"), "approve": ("Aprobar", "Approve"), "submit": ("Enviar", "Submit"),
    "obsolete": ("Marcar obsoletas", "Mark obsolete"), "validate": ("Validar", "Validate"), "reverse": ("Revertir", "Reverse"),
    "release": ("Liberar", "Release"), "fulfill": ("Surtir", "Fulfill"), "expire": ("Vencer", "Expire"),
    "cancel": ("Cancelar", "Cancel"), "suspend": ("Suspender", "Suspend"), "reactivate": ("Reactivar", "Reactivate"),
    "confirm": ("Confirmar", "Confirm"),
    "rotate_secret": ("Rotar secreto de", "Rotate secret for"), "check": ("Consultar", "Check"),
}
ACTION_ORDER = {"read": 10, "list": 10, "create": 20, "update": 30, "submit": 40, "approve": 50, "confirm": 52, "validate": 55, "manage": 60, "disable": 70, "delete": 90}


def parse_permission_codes(raw_permissions: str) -> tuple[str, ...]:
    return tuple(permission.strip().strip("\"'") for permission in raw_permissions.split(",") if permission.strip())


def derive_permission_seed(code: str, required_module: str, source_file: str) -> PermissionSeed:
    parts = code.split(".")
    if len(parts) < 3:
        raise ValueError(f"Permission code must have at least 3 segments: {code}")
    if parts[0] in MODULE_CODES or parts[0] in {"public", "external"}:
        module_code, resource_parts = parts[0], parts[1:-1]
    elif parts[0] == "internal":
        if len(parts) > 2 and parts[1] in MODULE_CODES:
            module_code, resource_parts = parts[1], parts[2:-1]
        elif required_module in MODULE_CODES:
            module_code, resource_parts = required_module, parts[1:-1]
        else:
            module_code, resource_parts = "admin", parts[1:-1]
    elif required_module in MODULE_CODES:
        module_code, resource_parts = required_module, parts[:-1]
    else:
        module_code, resource_parts = parts[0], parts[1:-1]
    resource = ".".join(resource_parts) or "general"
    if len(resource) > 80:
        raise ValueError(f"Permission resource exceeds 80 chars for {code}: {resource}")
    action = parts[-1]
    classification = "integration" if parts[0] == "external" else parts[0] if parts[0] in {"internal", "public"} else "tenant"
    if code.startswith("billing.manual_activation."):
        classification = "internal"
    risk = ("critical" if action in {"delete", "suspend", "reactivate", "reverse", "rotate_secret"}
            else "high" if action in {"create", "update", "approve", "manage", "invite", "disable", "cancel"}
            else "low" if action in {"read", "list", "check"} else "standard")
    resource_es, resource_en = RESOURCE_LABELS.get(resource, (resource.replace(".", " ").replace("_", " "), resource.replace(".", " ").replace("_", " ")))
    action_es, action_en = ACTION_LABELS.get(action, (action.replace("_", " ").title(), action.replace("_", " ").title()))
    label_es, label_en = f"{action_es} {resource_es}", f"{action_en} {resource_en}"
    module_es, module_en = MODULE_LABELS.get(module_code, (module_code, module_code))
    return PermissionSeed(
        code=code, module_code=module_code, resource=resource, action=action,
        description=f"Seeded from {source_file}; required module: {required_module}.",
        display_name_es=label_es, display_name_en=label_en,
        description_es=f"Permite {label_es.lower()} dentro de {module_es}.",
        description_en=f"Allows users to {label_en.lower()} in {module_en}.",
        classification=classification, assignable_to_tenant_role=classification == "tenant", risk_level=risk,
        sort_order=MODULE_ORDER.get(module_code, 90) * 100 + ACTION_ORDER.get(action, 80),
    )


def extract_permission_seeds_from_text(content: str, source_file: str) -> tuple[PermissionSeed, ...]:
    required_module = "admin"
    seeds: dict[str, PermissionSeed] = {}
    for line in content.splitlines():
        required_match = REQUIRED_MODULE_RE.search(line)
        if required_match:
            required_module = required_match.group("module").strip()
            continue
        permission_match = PERMISSION_LINE_RE.search(line)
        if permission_match:
            for code in parse_permission_codes(permission_match.group("permissions")):
                seeds[code] = derive_permission_seed(code, required_module, source_file)
    return tuple(seeds[code] for code in sorted(seeds))


def extract_permission_seeds(contracts_dir: Path) -> tuple[PermissionSeed, ...]:
    seeds: dict[str, PermissionSeed] = {}
    for contract_path in sorted(contracts_dir.glob("*.openapi.yaml")):
        relative_source = f"contracts/api/{contract_path.name}"
        for seed in extract_permission_seeds_from_text(contract_path.read_text(encoding="utf-8"), relative_source):
            seeds[seed.code] = seed
    return tuple(seeds[code] for code in sorted(seeds))
