"""Inspect a raw organization.profile export without connecting or writing to a DB.

This is a data-quality report, not a migration plan or permission to migrate.
Input: {"tenant_id": "...", "organization_profile": { ... raw JSONB ... }}.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


LEGAL_FIELDS = {
    "id", "status", "code", "legal_name", "tax_id", "fiscal_regime", "cfdi_usage",
    "fiscal_address", "contact_name", "contact_email", "contact_phone", "contact_position",
    "tenant_id",
}
BRANCH_FIELDS = {"id", "status", "name", "code", "legal_entity_id", "address", "phone", "tenant_id"}


def inspect_export(document: object, tenant_id: str) -> dict:
    """Preserve the source; report paths and codes, never names, contacts or RFCs."""
    issues: list[dict] = []
    counts = {"legal_entities": 0, "branches": 0}

    def issue(code: str, path: list, severity: str = "blocking", **details) -> None:
        issues.append({"code": code, "path": path, "severity": severity, **details})

    def finish() -> dict:
        totals = Counter(item["severity"] for item in issues)
        status = "blocked" if totals["blocking"] else "review_required" if totals["review"] else "clean"
        return {
            "report_version": 1,
            "scope": "offline_export_only",
            "database_checked": False,
            "migration_authorized": False,
            "data_status": status,
            "counts": counts,
            "issue_counts": {key: totals[key] for key in ("blocking", "review")},
            "issues": issues,
        }

    def identity(value: object) -> bool:
        return isinstance(value, str) and bool(value) and value == value.strip()

    if not identity(tenant_id):
        issue("tenant_required", ["tenant_id"])
        return finish()
    if not isinstance(document, dict):
        issue("export_object_required", [])
        return finish()
    if document.get("tenant_id") != tenant_id:
        issue("tenant_mismatch", ["tenant_id"])
        return finish()  # Do not inspect another tenant's export.
    profile = document.get("organization_profile")
    if not isinstance(profile, dict):
        issue("profile_object_required", ["organization_profile"])
        return finish()
    root = ["organization_profile"]
    if "corporate" not in profile or not isinstance(profile["corporate"], dict):
        issue("corporate_object_required", root + ["corporate"])
    if "tenant_id" in profile and profile["tenant_id"] != tenant_id:
        issue("tenant_mismatch", root + ["tenant_id"])
    unknown_profile = set(profile) - {"corporate", "legal_entities", "branches", "tenant_id"}
    if unknown_profile:
        issue("unmapped_profile_fields", root, "review", field_count=len(unknown_profile))

    collections: dict[str, list[tuple[int, dict]]] = {}
    for name, allowed, label in (
        ("legal_entities", LEGAL_FIELDS, "legal_name"),
        ("branches", BRANCH_FIELDS, "name"),
    ):
        raw = profile.get(name)
        collections[name] = []
        if not isinstance(raw, list):
            issue("collection_array_required", root + [name])
            continue
        counts[name] = len(raw)  # Includes malformed rows; never silently drops them.
        seen_ids: set[str] = set()
        seen_codes: set[str] = set()
        for index, item in enumerate(raw):
            path = root + [name, index]
            if not isinstance(item, dict):
                issue("record_object_required", path)
                continue
            collections[name].append((index, item))
            if "tenant_id" in item and item["tenant_id"] != tenant_id:
                issue("tenant_mismatch", path + ["tenant_id"])
            record_id = item.get("id")
            if not identity(record_id):
                issue("stable_id_required", path + ["id"])
            elif record_id in seen_ids:
                issue("duplicate_id", path + ["id"])
            else:
                seen_ids.add(record_id)
            if not isinstance(item.get(label), str) or not item[label].strip():
                issue("name_required", path + [label])
            if item.get("status") not in ("active", "inactive"):
                issue("status_unresolved", path + ["status"])
            code = item.get("code")
            if code is None or code == "":
                issue("code_allocation_required", path + ["code"], "review")
            elif not identity(code):
                issue("invalid_code", path + ["code"])
            elif code.casefold() in seen_codes:
                issue("code_collision_review", path + ["code"], "review")
            else:
                seen_codes.add(code.casefold())
            extra = set(item) - allowed
            if extra:
                issue("unmapped_record_fields", path, "review", field_count=len(extra))
            for field in allowed - {"id", "status", "code", label, "tenant_id"}:
                if item.get(field) is not None and not isinstance(item[field], str):
                    issue("text_field_invalid", path + [field])

    legal_ids = Counter(
        item["id"] for _, item in collections["legal_entities"] if identity(item.get("id"))
    )
    seen_tax_ids: set[str] = set()
    for index, item in collections["legal_entities"]:
        path = root + ["legal_entities", index]
        tax_id = item.get("tax_id")
        if tax_id is None or isinstance(tax_id, str) and not tax_id.strip():
            issue("fiscal_identity_incomplete", path + ["tax_id"], "review")
        elif isinstance(tax_id, str):
            normalized = tax_id.strip().upper()
            if normalized in seen_tax_ids:
                issue("shared_tax_identity_review", path + ["tax_id"], "review")
            seen_tax_ids.add(normalized)
        for field in ("fiscal_regime", "fiscal_address"):
            if not item.get(field) or isinstance(item[field], str) and not item[field].strip():
                issue("fiscal_profile_incomplete", path + [field], "review")

    for index, item in collections["branches"]:
        path = root + ["branches", index, "legal_entity_id"]
        reference = item.get("legal_entity_id")
        if reference is None or reference == "":
            issue("society_assignment_required", path, "review")
        elif not identity(reference):
            issue("invalid_legal_entity_reference", path)
        elif legal_ids[reference] == 0:
            issue("orphan_legal_entity_reference", path)
        elif legal_ids[reference] > 1:
            issue("ambiguous_legal_entity_reference", path)

    # Stable ordering for repeatable review, including checks over sets above.
    issues.sort(key=lambda item: (json.dumps(item["path"]), item["code"]))
    return finish()


def unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def reject_constant(_value: str) -> None:
    raise ValueError("non_standard_json_number")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Raw local JSON export; never a URL")
    parser.add_argument("--tenant-id", required=True, help="Must match the export envelope")
    args = parser.parse_args(argv)
    try:
        # Refuse UNC/network paths; this command never fetches a remote resource.
        if str(args.input).startswith(("\\\\", "//")):
            raise ValueError("network_path")
        raw = args.input.read_bytes()
        document = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (OSError, ValueError, RecursionError):
        # Do not echo source contents, PII, credentials or exception diagnostics.
        print(json.dumps({"error": {"code": "invalid_local_export"}}))
        return 2
    report = inspect_export(document, args.tenant_id)
    report["source_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return {"clean": 0, "review_required": 1, "blocked": 2}[report["data_status"]]


if __name__ == "__main__":
    raise SystemExit(main())
