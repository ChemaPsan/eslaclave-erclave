"""Offline preflight regressions: no engines, tenant fixtures or DB writes."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[4] / "tools" / "preflight_organization.py"
SPEC = importlib.util.spec_from_file_location("organization_preflight", SCRIPT)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)
TENANT = "ten_739ee59d765d5e14818674800d"


def export():
    return {"tenant_id": TENANT, "organization_profile": {
        "corporate": {"commercial_name": "Synthetic corporate"},
        "legal_entities": [{"id": "rso_a", "code": "SOC-A", "legal_name": "Synthetic legal entity",
                            "status": "active", "tax_id": "SYNTHETIC-ID", "fiscal_regime": "example",
                            "fiscal_address": "Synthetic address", "contact_email": "private@example.invalid"}],
        "branches": [{"id": "suc_a", "code": "DIV-A", "name": "Synthetic branch",
                      "status": "inactive", "legal_entity_id": "rso_a"}],
    }}


def codes(report):
    return {issue["code"] for issue in report["issues"]}


def test_complete_export_is_unchanged_repeatable_and_not_migration_authority():
    document = export()
    original = deepcopy(document)
    result = preflight.inspect_export(document, TENANT)
    assert result["data_status"] == "clean"
    assert result["database_checked"] is False
    assert result["migration_authorized"] is False
    assert result == preflight.inspect_export(document, TENANT)
    assert document == original


def test_rejects_wrong_tenant_before_inspecting_contents():
    document = export()
    document["tenant_id"] = "other_synthetic_tenant"
    document["organization_profile"]["branches"] = [None]
    result = preflight.inspect_export(document, TENANT)
    assert codes(result) == {"tenant_mismatch"}
    assert result["counts"] == {"legal_entities": 0, "branches": 0}


@pytest.mark.parametrize("value", [None, "", 7, {}])
def test_does_not_normalize_malformed_collection_to_empty(value):
    document = export()
    document["organization_profile"]["branches"] = value
    assert "collection_array_required" in codes(preflight.inspect_export(document, TENANT))


def test_malformed_and_duplicate_rows_remain_in_counts_and_block_ambiguous_reference():
    document = export()
    profile = document["organization_profile"]
    profile["legal_entities"].extend([None, deepcopy(profile["legal_entities"][0])])
    result = preflight.inspect_export(document, TENANT)
    assert result["counts"]["legal_entities"] == 3
    assert {"record_object_required", "duplicate_id", "ambiguous_legal_entity_reference"} <= codes(result)


@pytest.mark.parametrize("reference,expected", [
    (None, "society_assignment_required"), ("", "society_assignment_required"),
    ("missing", "orphan_legal_entity_reference"), ({}, "invalid_legal_entity_reference"),
])
def test_unresolved_branch_parent_is_never_inferred(reference, expected):
    document = export()
    document["organization_profile"]["branches"][0]["legal_entity_id"] = reference
    assert expected in codes(preflight.inspect_export(document, TENANT))


def test_shared_fiscal_identity_missing_code_and_extensions_require_review():
    document = export()
    profile = document["organization_profile"]
    profile["legal_entities"].append({**profile["legal_entities"][0], "id": "rso_b", "code": None})
    profile["branches"][0]["custom_secret_field"] = "do-not-echo"
    result = preflight.inspect_export(document, TENANT)
    assert result["data_status"] == "review_required"
    assert {"shared_tax_identity_review", "code_allocation_required", "unmapped_record_fields"} <= codes(result)
    serialized = json.dumps(result)
    for private in ("SYNTHETIC-ID", "private@example.invalid", "do-not-echo", "custom_secret_field"):
        assert private not in serialized


def test_nested_tenant_mismatch_and_unknown_status_are_blocking():
    document = export()
    branch = document["organization_profile"]["branches"][0]
    branch.update(tenant_id="other_synthetic_tenant", status="deleted")
    result = preflight.inspect_export(document, TENANT)
    assert result["data_status"] == "blocked"
    assert {"tenant_mismatch", "status_unresolved"} <= codes(result)


def test_missing_fiscal_fields_and_codes_remain_explicit_review_items():
    document = export()
    legal = document["organization_profile"]["legal_entities"][0]
    for field in ("code", "tax_id", "fiscal_regime", "fiscal_address"):
        del legal[field]
    result = preflight.inspect_export(document, TENANT)
    assert result["data_status"] == "review_required"
    assert {"code_allocation_required", "fiscal_identity_incomplete", "fiscal_profile_incomplete"} <= codes(result)


def test_case_insensitive_code_collision_requires_review_without_renumbering():
    document = export()
    branches = document["organization_profile"]["branches"]
    branches.append({**branches[0], "id": "suc_b", "code": "div-a"})
    before = deepcopy(document)
    assert "code_collision_review" in codes(preflight.inspect_export(document, TENANT))
    assert document == before


@pytest.mark.parametrize("content", ['{"tenant_id":"a","tenant_id":"b"}', '{"secret":NaN}', 'not JSON'])
def test_cli_rejects_ambiguous_json_without_echoing_input(tmp_path, capsys, content):
    source = tmp_path / "export.json"
    source.write_text(content, encoding="utf-8")
    assert preflight.main(["--input", str(source), "--tenant-id", TENANT]) == 2
    assert json.loads(capsys.readouterr().out) == {"error": {"code": "invalid_local_export"}}


@pytest.mark.parametrize("status,code,expected", [("active", "DIV-A", 0), ("active", None, 1), ("unexpected", "DIV-A", 2)])
def test_cli_hashes_source_and_returns_exit_status(tmp_path, capsys, status, code, expected):
    document = export()
    document["organization_profile"]["branches"][0]["status"] = status
    document["organization_profile"]["branches"][0]["code"] = code
    source = tmp_path / "export.json"
    source.write_text(json.dumps(document), encoding="utf-8-sig")
    before = source.read_bytes()
    assert preflight.main(["--input", str(source), "--tenant-id", TENANT]) == expected
    report = json.loads(capsys.readouterr().out)
    assert len(report["source_sha256"]) == 64
    assert source.read_bytes() == before
