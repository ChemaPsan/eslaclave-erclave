from copy import deepcopy
from types import SimpleNamespace
import pytest
from pydantic import ValidationError
from erclave_common.errors import ErclaveError
from app.organization_scope import MembershipScope, configured_scope, effective_scope, select_active
from app.schemas import SessionScopeRead


def catalog():
    return {"issuers": [{"id": "emi", "legal_name": "Fiscal", "code": "EMI", "status": "active"}],
            "societies": [{"id": "soc", "issuer_id": "emi", "name": "Society", "code": "SOC", "base_currency": "MXN", "status": "active"}],
            "divisions": [{"id": id_, "society_id": "soc", "name": id_, "code": id_, "status": "active"} for id_ in ("div-a", "div-b")],
            "mappings": [{"collection": "branches", "legacy_id": "old-a", "division_id": "div-a"}]}


def test_restricted_legacy_maps_ids_without_granting_new_divisions():
    data = catalog()
    configured = configured_scope({"scope": {"branch_ids": ["old-a"]}}, data)
    result = effective_scope(configured, data)
    assert result["division_ids"] == ["div-a"]
    assert result["branch_ids"] == ["old-a"]
    assert not result["all_divisions"]
    assert result["society_ids"] == ["soc"]


@pytest.mark.parametrize("legacy", [{}, {"scope": {"branch_ids": []}}, {"scope": {"branch_ids": ["*"]}}])
def test_legacy_effective_all_becomes_explicit_wildcard(legacy):
    assert configured_scope(legacy, catalog()).division_ids == ["*"]


def test_versioned_empty_is_deny_all_without_default_branch():
    result = effective_scope(MembershipScope(), catalog())
    assert result["divisions"] == result["branches"] == result["issuers"] == []
    assert not result["all_branches"]


@pytest.mark.parametrize("kind", ["issuers", "societies", "divisions"])
def test_inactive_ancestry_cannot_be_selected(kind):
    data = catalog()
    for item in data[kind]:
        item["status"] = "inactive"
    result = effective_scope(MembershipScope(society_ids=["*"], division_ids=["*"]), data)
    assert result["divisions"] == []


@pytest.mark.parametrize("metadata", [{"scope": {"version": 3}}, {"scope": {"version": 2, "division_ids": ["*"], "society_ids": []}},
                                      {"scope": {"branch_ids": ["foreign"]}}, {"scope": {"branch_ids": "*"}}, {"scope": []}])
def test_malformed_or_unmapped_scope_never_becomes_wildcard(metadata):
    with pytest.raises(ErclaveError):
        configured_scope(metadata, catalog())


def test_parent_grant_alone_does_not_grant_divisions():
    assert effective_scope(MembershipScope(society_ids=["soc"]), catalog())["division_ids"] == []


def test_active_selection_is_derived_and_revalidated():
    value = effective_scope(MembershipScope(society_ids=["soc"], division_ids=["div-a"]), catalog())
    context = SimpleNamespace(scope=SessionScopeRead.model_validate(value), tenant=SimpleNamespace(status="active"), user=SimpleNamespace(status="active"))
    assert select_active(context, "div-a").scope.active_society_id == "soc"
    assert context.scope.active_issuer_id == "emi"
    for id_ in ("div-b", "foreign", "default"):
        with pytest.raises(ErclaveError):
            select_active(context, id_)


def test_moving_division_does_not_expand_versioned_society_grant():
    data = catalog()
    data["societies"].append({**data["societies"][0], "id": "soc-other"})
    configured = MembershipScope(society_ids=["soc"], division_ids=["div-a"])
    data["divisions"][0]["society_id"] = "soc-other"
    assert effective_scope(configured, data)["division_ids"] == []


@pytest.mark.parametrize("ids", [["*", "div-a"], ["div-a", "div-a"], [""], ["x" * 41]])
def test_invalid_membership_identifier_sets(ids):
    with pytest.raises(ValidationError):
        MembershipScope(society_ids=["*"], division_ids=ids)
