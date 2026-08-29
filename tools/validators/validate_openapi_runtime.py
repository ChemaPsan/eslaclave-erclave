"""Parse OpenAPI YAML and compare implemented operations with FastAPI routes."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts" / "api"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
SERVICE_APIS = {
    "admin-service.openapi.yaml": ROOT / "backend" / "services" / "admin-service" / "app" / "api.py",
    "production-service.openapi.yaml": ROOT / "backend" / "services" / "production-service" / "app" / "api.py",
    "inventory-service.openapi.yaml": ROOT / "backend" / "services" / "inventory-service" / "app" / "api.py",
    "hr-service.openapi.yaml": ROOT / "backend" / "services" / "hr-service" / "app" / "api.py",
    "sales-service.openapi.yaml": ROOT / "backend" / "services" / "sales-service" / "app" / "api.py",
    "purchasing-service.openapi.yaml": ROOT / "backend" / "services" / "purchasing-service" / "app" / "api.py",
    "maintenance-service.openapi.yaml": ROOT / "backend" / "services" / "maintenance-service" / "app" / "api.py",
}


def normalized_path(value: str) -> str:
    return re.sub(r"\{[^}/]+\}", "{}", value)


def runtime_operations(api_path: Path) -> dict[tuple[str, str], frozenset[str] | None]:
    tree = ast.parse(api_path.read_text(encoding="utf-8"), filename=str(api_path))
    prefix = ""
    constants: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                try:
                    constants[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
        if not any(isinstance(target, ast.Name) and target.id == "router" for target in node.targets):
            continue
        if isinstance(node.value, ast.Call):
            for keyword in node.value.keywords:
                if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    prefix = keyword.value.value
    operations: dict[tuple[str, str], frozenset[str] | None] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.lower()
            if method not in HTTP_METHODS or not decorator.args:
                continue
            route = decorator.args[0]
            if isinstance(route, ast.Constant) and isinstance(route.value, str):
                permissions: set[str] = set()
                defaults = [*node.args.defaults, *(item for item in node.args.kw_defaults if item is not None)]
                for default in defaults:
                    for call in ast.walk(default):
                        if not isinstance(call, ast.Call) or not call.args:
                            continue
                        name = call.func.id if isinstance(call.func, ast.Name) else ""
                        if not name.startswith("require_"):
                            continue
                        value_node = call.args[0]
                        value = constants.get(value_node.id) if isinstance(value_node, ast.Name) else None
                        if value is None:
                            try:
                                value = ast.literal_eval(value_node)
                            except (ValueError, TypeError):
                                continue
                        if isinstance(value, str):
                            permissions.add(value)
                        elif isinstance(value, (tuple, list, set)):
                            permissions.update(item for item in value if isinstance(item, str))
                operations[(method, normalized_path(prefix + route.value))] = frozenset(permissions) if permissions else None
    return operations


def validate_local_refs(document: dict, contract_name: str, errors: list[str]) -> None:
    stack: list[object] = [document]
    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(current)
            continue
        if not isinstance(current, dict):
            continue
        reference = current.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/"):
            target: object = document
            try:
                for segment in reference[2:].split("/"):
                    target = target[segment.replace("~1", "/").replace("~0", "~")]  # type: ignore[index]
            except (KeyError, TypeError):
                errors.append(f"{contract_name} contains unresolved reference {reference}")
        stack.extend(current.values())


def main() -> int:
    errors: list[str] = []
    for contract_path in sorted(CONTRACTS.glob("*.openapi.yaml")):
        try:
            document = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{contract_path.relative_to(ROOT)} is not valid YAML: {exc}")
            continue
        if not isinstance(document, dict) or document.get("openapi") != "3.1.0":
            errors.append(f"{contract_path.relative_to(ROOT)} must be an OpenAPI 3.1.0 object")
            continue
        contract_operations: dict[tuple[str, str], dict] = {}
        operation_ids: set[str] = set()
        normalized_routes: dict[str, str] = {}
        default_status = document.get("x-implementation-status", "implemented")
        validate_local_refs(document, contract_path.name, errors)
        for route, path_item in (document.get("paths") or {}).items():
            if not isinstance(path_item, dict):
                continue
            normalized_route = normalized_path(route)
            if normalized_route in normalized_routes and normalized_routes[normalized_route] != route:
                errors.append(f"{contract_path.name} has ambiguous templated paths {normalized_routes[normalized_route]} and {route}")
            normalized_routes[normalized_route] = route
            for method, operation in path_item.items():
                if method not in HTTP_METHODS or not isinstance(operation, dict):
                    continue
                key = (method, normalized_path(route))
                contract_operations[key] = operation
                operation_id = operation.get("operationId")
                if not operation_id:
                    errors.append(f"{contract_path.name} {method.upper()} {route} lacks operationId")
                elif operation_id in operation_ids:
                    errors.append(f"{contract_path.name} repeats operationId {operation_id}")
                else:
                    operation_ids.add(operation_id)
                status = operation.get("x-implementation-status", default_status)
                if status not in {"implemented", "planned"}:
                    errors.append(f"{contract_path.name} {method.upper()} {route} has invalid x-implementation-status {status!r}")
                if not operation.get("x-required-module"):
                    errors.append(f"{contract_path.name} {method.upper()} {route} lacks x-required-module")
                permissions = operation.get("x-permissions")
                if not isinstance(permissions, list) or not permissions:
                    errors.append(f"{contract_path.name} {method.upper()} {route} must declare x-permissions")

        api_path = SERVICE_APIS.get(contract_path.name)
        if api_path:
            runtime = runtime_operations(api_path)
            implemented = {
                key
                for key, operation in contract_operations.items()
                if operation.get("x-implementation-status", default_status) == "implemented"
            }
            for method, route in sorted(set(runtime) - implemented):
                errors.append(f"{contract_path.name} runtime route missing from implemented contract: {method.upper()} {route}")
            for method, route in sorted(implemented - set(runtime)):
                errors.append(f"{contract_path.name} contract route is not implemented or marked planned: {method.upper()} {route}")
            for key in sorted(implemented & set(runtime)):
                runtime_permissions = runtime[key]
                if runtime_permissions is None:
                    continue
                contract_permissions = frozenset(contract_operations[key].get("x-permissions") or [])
                if runtime_permissions != contract_permissions:
                    method, route = key
                    errors.append(
                        f"{contract_path.name} {method.upper()} {route} permission drift: "
                        f"runtime={sorted(runtime_permissions)} contract={sorted(contract_permissions)}"
                    )
        elif default_status != "planned":
            errors.append(f"{contract_path.name} has no runtime validator mapping and must declare top-level x-implementation-status: planned")

    if errors:
        print("[FAIL] OpenAPI parsing/runtime alignment failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("[OK] OpenAPI YAML parses and implemented operations match FastAPI routes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
