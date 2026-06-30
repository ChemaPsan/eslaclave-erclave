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
    status: str = "active"


def parse_permission_codes(raw_permissions: str) -> tuple[str, ...]:
    return tuple(
        permission.strip().strip("\"'")
        for permission in raw_permissions.split(",")
        if permission.strip()
    )


def derive_permission_seed(code: str, required_module: str, source_file: str) -> PermissionSeed:
    parts = code.split(".")
    if len(parts) < 3:
        raise ValueError(f"Permission code must have at least 3 segments: {code}")

    if parts[0] in MODULE_CODES or parts[0] in {"public", "external"}:
        module_code = parts[0]
        resource_parts = parts[1:-1]
    elif parts[0] == "internal":
        if len(parts) > 2 and parts[1] in MODULE_CODES:
            module_code = parts[1]
            resource_parts = parts[2:-1]
        elif required_module in MODULE_CODES:
            module_code = required_module
            resource_parts = parts[1:-1]
        else:
            module_code = "admin"
            resource_parts = parts[1:-1]
    elif required_module in MODULE_CODES:
        module_code = required_module
        resource_parts = parts[:-1]
    else:
        module_code = parts[0]
        resource_parts = parts[1:-1]

    resource = ".".join(resource_parts) or "general"
    if len(resource) > 80:
        raise ValueError(f"Permission resource exceeds 80 chars for {code}: {resource}")

    return PermissionSeed(
        code=code,
        module_code=module_code,
        resource=resource,
        action=parts[-1],
        description=f"Seeded from {source_file}; required module: {required_module}.",
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
        if not permission_match:
            continue

        for code in parse_permission_codes(permission_match.group("permissions")):
            seeds[code] = derive_permission_seed(code, required_module, source_file)

    return tuple(seeds[code] for code in sorted(seeds))


def extract_permission_seeds(contracts_dir: Path) -> tuple[PermissionSeed, ...]:
    seeds: dict[str, PermissionSeed] = {}
    for contract_path in sorted(contracts_dir.glob("*.openapi.yaml")):
        if contract_path.name == "README.md":
            continue
        relative_source = f"contracts/api/{contract_path.name}"
        for seed in extract_permission_seeds_from_text(contract_path.read_text(encoding="utf-8"), relative_source):
            seeds[seed.code] = seed

    return tuple(seeds[code] for code in sorted(seeds))
