"""Reviewed, idempotent shadow import. The legacy JSON remains authoritative.

No API imports this module. Activation and live compatibility belong to CONT-02.
"""
from copy import deepcopy
import hashlib
import json

from sqlalchemy import select, text

from .models import (
    AuditEvent, Division, FiscalIssuer, OrganizationImport,
    OrganizationLegacyMapping, Society, new_id,
)


class OrganizationMigrationError(ValueError):
    def __init__(self, code: str, issues: list[dict] | None = None):
        super().__init__(code)
        self.code = code
        self.issues = issues or []


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def stable_id(tenant_id: str, kind: str, legacy_id: str) -> str:
    return f"{kind}_{digest([tenant_id, kind, legacy_id])[:26]}"


def build_plan(tenant_id: str, profile: dict, resolutions: dict | None = None) -> dict:
    """Resolve identities, never infer a missing parent or merge a shared RFC."""
    issues = []

    def fail(code, path):
        issues.append({"code": code, "path": path})

    def string(value, maximum=120, required=True):
        if value is None:
            return not required
        return isinstance(value, str) and len(value) <= maximum and (bool(value.strip()) or not required)

    if not string(tenant_id, 40) or not isinstance(profile, dict):
        raise OrganizationMigrationError("invalid_source")
    profile = deepcopy(profile)
    resolutions = deepcopy(resolutions) if resolutions is not None else {}
    if not isinstance(resolutions, dict) or set(resolutions) - {"issuer_aliases", "branch_societies"}:
        raise OrganizationMigrationError("invalid_resolutions")
    for name in ("issuer_aliases", "branch_societies"):
        if not isinstance(resolutions.get(name, {}), dict):
            raise OrganizationMigrationError("invalid_resolutions")
    if not isinstance(profile.get("corporate"), dict):
        fail("corporate_object_required", ["corporate"])
    if "tenant_id" in profile and profile["tenant_id"] != tenant_id:
        fail("tenant_mismatch", ["tenant_id"])
    records = {}
    for collection, label in (("legal_entities", "legal_name"), ("branches", "name")):
        items = profile.get(collection)
        records[collection] = {}
        if not isinstance(items, list):
            fail("collection_array_required", [collection])
            continue
        for index, item in enumerate(items):
            path = [collection, index]
            if not isinstance(item, dict):
                fail("record_object_required", path)
                continue
            identifier = item.get("id")
            if not string(identifier) or identifier != identifier.strip():
                fail("stable_id_required", path + ["id"])
                continue
            if identifier in records[collection]:
                fail("duplicate_id", path + ["id"])
            records[collection][identifier] = item
            if "tenant_id" in item and item["tenant_id"] != tenant_id:
                fail("tenant_mismatch", path + ["tenant_id"])
            if not string(item.get(label), 240):
                fail("invalid_name", path + [label])
            if item.get("status") not in ("active", "inactive"):
                fail("invalid_status", path + ["status"])
            code = item.get("code")
            if code not in (None, "") and (not string(code, 80) or code != code.strip()):
                fail("invalid_code", path + ["code"])
            for field in ("tax_id", "fiscal_regime", "cfdi_usage", "phone"):
                if field in item and not string(item[field], 80, required=False):
                    fail("invalid_text", path + [field])
            for field in ("address", "fiscal_address", "contact_name", "contact_email", "contact_phone", "contact_position"):
                if item.get(field) is not None and not isinstance(item[field], str):
                    fail("invalid_text", path + [field])
    if issues:
        raise OrganizationMigrationError("invalid_source", issues)

    legal, branches = records["legal_entities"], records["branches"]
    aliases = {key: key for key in legal}
    for key, target in resolutions.get("issuer_aliases", {}).items():
        if key not in legal or not isinstance(target, str) or target not in legal:
            raise OrganizationMigrationError("unknown_issuer_alias")
        aliases[key] = target
    if any(aliases[target] != target for target in aliases.values()):
        raise OrganizationMigrationError("issuer_alias_chain")
    normalized_tax = lambda value: (value or "").strip().upper()
    tax_groups = {}
    for key, item in legal.items():
        tax = normalized_tax(item.get("tax_id"))
        if tax:
            tax_groups.setdefault(tax, set()).add(aliases[key])
        if aliases[key] != key:
            canonical = legal[aliases[key]]
            if not tax or tax != normalized_tax(canonical.get("tax_id")):
                raise OrganizationMigrationError("issuer_alias_tax_mismatch")
            for field in ("legal_name", "fiscal_regime", "cfdi_usage", "fiscal_address"):
                if (item.get(field) or "").strip().casefold() != (canonical.get(field) or "").strip().casefold():
                    raise OrganizationMigrationError("issuer_alias_fiscal_conflict")
    if any(len(group) > 1 for group in tax_groups.values()):
        raise OrganizationMigrationError("shared_tax_identity_requires_resolution")
    branch_parents = {}
    overrides = resolutions.get("branch_societies", {})
    if set(overrides) - set(branches):
        raise OrganizationMigrationError("unknown_branch_resolution")
    for key, item in branches.items():
        parent = overrides.get(key, item.get("legal_entity_id"))
        if not isinstance(parent, str) or parent not in legal:
            raise OrganizationMigrationError("branch_society_requires_resolution")
        branch_parents[key] = parent

    source_hash = digest(profile)
    import_id = stable_id(tenant_id, "oim", source_hash)
    rows = {"fiscal_issuers": [], "societies": [], "divisions": [], "organization_legacy_mappings": []}
    for key in sorted(set(aliases.values())):
        item = legal[key]
        rows["fiscal_issuers"].append({
            "tenant_id": tenant_id, "id": stable_id(tenant_id, "emi", key),
            "code": f"EMI-MIG-{digest([tenant_id, key])[:12].upper()}",
            "legal_name": item["legal_name"], "tax_id": item.get("tax_id"),
            "fiscal_regime": item.get("fiscal_regime"), "cfdi_usage": item.get("cfdi_usage"),
            "fiscal_address": item.get("fiscal_address"), "status": item["status"],
            "contact": {field: item[field] for field in ("contact_name", "contact_email", "contact_phone", "contact_position") if field in item},
        })
    for key, item in sorted(legal.items()):
        society_id, issuer_id = stable_id(tenant_id, "soc", key), stable_id(tenant_id, "emi", aliases[key])
        rows["societies"].append({
            "tenant_id": tenant_id, "id": society_id,
            "code": item.get("code") or f"SOC-MIG-{digest([tenant_id, key])[:12].upper()}",
            "name": item["legal_name"], "issuer_id": issuer_id,
            "base_currency": "MXN", "status": item["status"],
        })
        rows["organization_legacy_mappings"].append({
            "tenant_id": tenant_id, "collection": "legal_entities", "legacy_id": key,
            "import_id": import_id, "society_id": society_id, "issuer_id": issuer_id,
            "division_id": None, "source_item": item,
        })
    for key, item in sorted(branches.items()):
        society_id, division_id = stable_id(tenant_id, "soc", branch_parents[key]), stable_id(tenant_id, "div", key)
        rows["divisions"].append({
            "tenant_id": tenant_id, "id": division_id, "society_id": society_id,
            "code": item.get("code") or f"DIV-MIG-{digest([tenant_id, key])[:12].upper()}",
            "name": item["name"], "address": item.get("address"),
            "phone": item.get("phone"), "status": item["status"],
        })
        rows["organization_legacy_mappings"].append({
            "tenant_id": tenant_id, "collection": "branches", "legacy_id": key,
            "import_id": import_id, "society_id": society_id, "issuer_id": None,
            "division_id": division_id, "source_item": item,
        })
    for collection in ("societies", "divisions", "fiscal_issuers"):
        codes = [row["code"].casefold() for row in rows[collection]]
        if len(set(codes)) != len(codes):
            raise OrganizationMigrationError("duplicate_target_code")
    result = {"version": 1, "tenant_id": tenant_id, "source_hash": source_hash,
              "import_id": import_id, "source_profile": profile, "resolutions": resolutions, "rows": rows}
    result["plan_hash"] = digest(result)
    return result


def read_profile(connection, tenant_id: str, *, lock=False) -> dict:
    row = connection.execute(text(
        "select value from admin.tenant_settings where tenant_id=:tenant and key='organization.profile'"
        + (" for update" if lock else "")
    ), {"tenant": tenant_id}).first()
    if row is None:
        raise OrganizationMigrationError("source_profile_missing")
    return row[0]


TABLES = {model.__table__.name: model.__table__ for model in (
    FiscalIssuer, Society, Division, OrganizationLegacyMapping,
)}


def apply_import(connection, tenant_id: str, *, expected_source_hash: str,
                 expected_plan_hash: str, operator: str, correlation_id: str,
                 resolutions: dict | None = None) -> dict:
    """Caller owns the transaction. Acquire tenant lock then recheck raw source.

    Never commit here; data, equivalences and audit must succeed atomically.
    """
    if not operator.strip() or len(operator) > 120 or not correlation_id.strip() or len(correlation_id) > 120:
        raise OrganizationMigrationError("operator_and_correlation_required")
    connection.execute(text("select pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                       {"key": f"admin.organization.import:{tenant_id}"})
    profile = read_profile(connection, tenant_id, lock=True)
    if digest(profile) != expected_source_hash:
        raise OrganizationMigrationError("source_changed")
    plan = build_plan(tenant_id, profile, resolutions)
    if plan["plan_hash"] != expected_plan_hash:
        raise OrganizationMigrationError("plan_changed")
    batch = OrganizationImport.__table__
    existing = connection.execute(select(batch).where(batch.c.tenant_id == tenant_id)).mappings().first()
    if existing:
        if existing["source_hash"] != plan["source_hash"] or existing["plan_hash"] != plan["plan_hash"]:
            raise OrganizationMigrationError("existing_import_changed")
        if existing["source_profile"] != profile or existing["resolutions"] != plan["resolutions"]:
            raise OrganizationMigrationError("target_changed")
        for name, table in TABLES.items():
            actual = connection.execute(select(table).where(table.c.tenant_id == tenant_id)).mappings().all()
            expected = plan["rows"][name]
            columns = {col for row in expected for col in row}
            if sorted((digest({key: row[key] for key in columns}) for row in actual)) != sorted(map(digest, expected)):
                raise OrganizationMigrationError("target_changed")
        return {"status": "already_applied", "counts": {name: len(rows) for name, rows in plan["rows"].items()}}
    for table in TABLES.values():
        if connection.execute(select(table.c.tenant_id).where(table.c.tenant_id == tenant_id).limit(1)).first():
            raise OrganizationMigrationError("target_not_empty")
    counts = {name: len(rows) for name, rows in plan["rows"].items()}
    if not any(counts.values()):
        return {"status": "empty", "counts": counts}
    if not connection.execute(text("""select id from admin.catalog_items
        where tenant_id=:tenant and catalog_code='currencies' and code='MXN' and status='active'"""),
        {"tenant": tenant_id}).first():
        raise OrganizationMigrationError("base_currency_not_active")
    connection.execute(batch.insert().values(
        tenant_id=tenant_id, id=plan["import_id"], source_hash=plan["source_hash"], plan_hash=plan["plan_hash"],
        source_profile=profile, resolutions=plan["resolutions"], operator=operator, correlation_id=correlation_id,
    ))
    for name, table in TABLES.items():
        if plan["rows"][name]:
            connection.execute(table.insert(), plan["rows"][name])
    connection.execute(AuditEvent.__table__.insert().values(
        id=new_id("aud"), tenant_id=tenant_id, actor_type="system", action="admin.organization.import",
        resource_type="organization_import", resource_id=plan["import_id"], source_service="admin-service",
        correlation_id=correlation_id, idempotency_key=f"cont01:{plan['plan_hash']}",
        after_state={"source_hash": plan["source_hash"], "plan_hash": plan["plan_hash"], "counts": counts},
        metadata={"operator": operator, "mode": "shadow", "source_unchanged": True},
    ))
    return {"status": "applied", "counts": counts}
