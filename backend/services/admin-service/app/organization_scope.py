"""Versioned membership scope, resolved only against tenant-owned organization rows."""
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from erclave_common.errors import ErclaveError
from .models import Division, FiscalIssuer, OrganizationLegacyMapping, Society
from .organization_store import authority, lock_organization, rows
from .organization_migration import digest


class MembershipScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[2] = 2
    society_ids: list[str] = Field(default_factory=list, max_length=1000)
    division_ids: list[str] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def explicit_scope(self):
        for values in (self.society_ids, self.division_ids):
            if any(not value or len(value) > 40 for value in values) or len(set(values)) != len(values):
                raise ValueError("Invalid scope identifiers")
            if "*" in values and values != ["*"]:
                raise ValueError("Wildcard must be exclusive")
        # A restricted grant is an explicit snapshot of division IDs. No future grants by parent.
        if self.division_ids == ["*"] and self.society_ids != ["*"]:
            raise ValueError("All divisions requires all societies")
        return self


class ScopeUpdate(MembershipScope):
    expected_revision: int = Field(ge=0)


class ScopeRead(MembershipScope):
    revision: int = 0
    divisions: list[dict] = Field(default_factory=list)


class ScopeResponse(BaseModel):
    data: ScopeRead


def denied(code="organization_scope_denied", status=403, field=None):
    raise ErclaveError(code, "Organization scope could not be resolved.", status,
                       {"field": field} if field else {})


def catalog(connection, tenant):
    return {"societies": rows(connection, Society, tenant), "divisions": rows(connection, Division, tenant),
            "issuers": rows(connection, FiscalIssuer, tenant), "mappings": rows(connection, OrganizationLegacyMapping, tenant)}


def configured_scope(metadata, data):
    """Legacy unrestricted semantics are explicit; malformed/versioned-empty scope never grants all."""
    metadata = metadata if isinstance(metadata, dict) else {}
    raw = metadata.get("scope", metadata)
    if not isinstance(raw, dict):
        denied("organization_scope_invalid", 409)
    if "version" in raw:
        if type(raw.get("revision", 0)) is not int or raw.get("revision", 0) < 0:
            denied("organization_scope_invalid", 409)
        try:
            return MembershipScope.model_validate({key: value for key, value in raw.items() if key != "revision"})
        except ValueError:
            denied("organization_scope_invalid", 409)
    legacy = raw.get("branch_ids", raw.get("branches"))
    if legacy is None or legacy == [] or legacy == ["*"]:
        # This preserves the pre-CONT-03 effective grant, including old unconfigured memberships.
        return MembershipScope(society_ids=["*"], division_ids=["*"])
    if not isinstance(legacy, list) or any(not isinstance(value, str) or not value or value == "*" for value in legacy):
        denied("organization_scope_invalid", 409)
    aliases = {item["legacy_id"]: item["division_id"] for item in data["mappings"] if item["collection"] == "branches"}
    known = {item["id"]: item for item in data["divisions"]}
    resolved = [aliases.get(value, value) for value in legacy]
    if any(value not in known for value in resolved):
        denied("organization_scope_review_required", 409)
    return MembershipScope(society_ids=sorted({known[value]["society_id"] for value in resolved}), division_ids=sorted(set(resolved)))


def effective_scope(configured, data, revision=0):
    issuers = {item["id"]: item for item in data["issuers"] if item["status"] == "active"}
    societies = {item["id"]: item for item in data["societies"] if item["status"] == "active"
                 and item["issuer_id"] in issuers and (configured.society_ids == ["*"] or item["id"] in configured.society_ids)}
    divisions = [item for item in data["divisions"] if item["status"] == "active" and item["society_id"] in societies
                 and (configured.division_ids == ["*"] or item["id"] in configured.division_ids)]
    # A parent grant alone does not widen visibility beyond the actual division grant.
    visible_societies = {item["society_id"] for item in divisions}
    public_societies = [{key: row[key] for key in ("id", "name", "code", "issuer_id", "base_currency")}
                        for id_, row in societies.items() if id_ in visible_societies]
    public_divisions = [{key: item[key] for key in ("id", "name", "code", "society_id")} for item in divisions]
    issuer_ids = {item["issuer_id"] for item in public_societies}
    public_issuers = [{key: row[key] for key in ("id", "code", "legal_name")} for id_, row in issuers.items() if id_ in issuer_ids]
    reverse = {item["division_id"]: item["legacy_id"] for item in data["mappings"] if item["collection"] == "branches"}
    society_reverse = {item["society_id"]: item["legacy_id"] for item in data["mappings"] if item["collection"] == "legal_entities"}
    return {"version": 2, "revision": revision, "society_ids": [item["id"] for item in public_societies],
            "division_ids": [item["id"] for item in divisions], "societies": public_societies,
            "divisions": public_divisions, "issuers": public_issuers,
            "all_divisions": configured.division_ids == ["*"], "all_branches": configured.division_ids == ["*"],
            "branch_ids": [reverse.get(item["id"], item["id"]) for item in divisions],
            "branches": [{"id": reverse.get(item["id"], item["id"]), "name": item["name"], "code": item["code"],
                          "status": "active", "legal_entity_id": society_reverse.get(item["society_id"], item["society_id"])} for item in divisions]}


def resolve_scope(connection, tenant, metadata):
    if not authority(connection, tenant):
        if isinstance(metadata, dict) and isinstance(metadata.get("scope"), dict) and "version" in metadata["scope"]:
            return effective_scope(MembershipScope(), {"issuers": [], "societies": [], "divisions": [], "mappings": []})
        return None  # Pre-switch tenants keep their existing contract until the reviewed activation.
    data = catalog(connection, tenant)
    configured = configured_scope(metadata, data)
    revision = (metadata or {}).get("scope", {}).get("revision", 0)
    return effective_scope(configured, data, revision)


def scope_migration_plan(connection, tenant, lock=False):
    if not authority(connection, tenant):
        denied("organization_scope_review_required", 409)
    data = catalog(connection, tenant)
    members = connection.execute(text("select id, metadata from admin.memberships where tenant_id=:tenant order by id"
                                      + (" for update" if lock else "")), {"tenant": tenant}).mappings().all()
    changes = []
    for row in members:
        metadata = row["metadata"] or {}
        configured = configured_scope(metadata, data).model_dump()
        raw = metadata.get("scope", metadata)
        if "version" not in raw:
            changes.append({"id": row["id"], "before": metadata, "after": {**metadata,
                "scope_legacy": raw, "scope": {**configured, "revision": 1}}})
    return {"hash": digest({"tenant": tenant, "changes": changes, "mappings": data["mappings"],
                           "parents": [{"id": item["id"], "society_id": item["society_id"]} for item in data["divisions"]]}), "changes": changes}


def migrate_scopes(connection, repository, tenant, expected_hash, operator):
    lock_organization(connection, tenant)
    plan = scope_migration_plan(connection, tenant, lock=True)
    if plan["hash"] != expected_hash:
        denied("organization_scope_conflict", 409)
    for item in plan["changes"]:
        connection.execute(text("update admin.memberships set metadata=cast(:metadata as jsonb), updated_at=now() where tenant_id=:tenant and id=:id"),
                           {"metadata": json.dumps(item["after"]), "tenant": tenant, "id": item["id"]})
        repository._record_audit_event(connection, tenant_id=tenant, action="admin.membership.scope.migrate", resource_type="membership",
            resource_id=item["id"], before_state={"scope": item["after"]["scope_legacy"]}, after_state={"scope": item["after"]["scope"]},
            idempotency_key=f"scope-migrate:{expected_hash}:{item['id']}", correlation_id=f"scope-migrate:{expected_hash}",
            metadata={"operator": operator})
    return len(plan["changes"])


def select_active(context, division_id):
    if division_id is None:
        return context
    if context.tenant.status != "active" or context.user.status != "active":
        denied()
    divisions = context.scope.divisions
    division = next((item for item in divisions if item["id"] == division_id), None)
    if not division:
        denied()
    society = next(item for item in context.scope.societies if item["id"] == division["society_id"])
    context.scope.active_division_id = division["id"]
    context.scope.active_society_id = society["id"]
    context.scope.active_issuer_id = society["issuer_id"]
    return context


class ScopeStore:
    def __init__(self, repository):
        self.repository = repository

    def membership(self, connection, tenant, user_id, lock=False):
        row = connection.execute(text("select id, metadata from admin.memberships where tenant_id=:tenant and user_id=:user"
                                      + (" for update" if lock else "")), {"tenant": tenant, "user": user_id}).mappings().first()
        if not row:
            denied("user_not_found", 404)
        if not authority(connection, tenant):
            denied("organization_scope_review_required", 409)
        return row

    def read(self, tenant, user_id):
        with self.repository.engine.connect() as connection:
            row = self.membership(connection, tenant, user_id)
            data = catalog(connection, tenant)
            result = configured_scope(row["metadata"], data).model_dump()
            result["revision"] = (row["metadata"] or {}).get("scope", {}).get("revision", 0)
            result["divisions"] = [{key: item[key] for key in ("id", "code", "name", "society_id", "status")}
                                   for item in data["divisions"] if item["id"] in result["division_ids"]]
            return result

    def update(self, tenant, user_id, payload, key, correlation, actor_email):
        operation = "admin.user.scope.update"
        with self.repository.engine.begin() as connection:
            lock_organization(connection, tenant)
            row = self.membership(connection, tenant, user_id, lock=True)
            cached = self.repository._begin_idempotent_command(connection, tenant, operation, key,
                self.repository._command_request_hash({"user_id": user_id, **payload}))
            if cached is not None:
                return cached
            metadata = row["metadata"] or {}
            before = configured_scope(metadata, catalog(connection, tenant)).model_dump()
            revision = metadata.get("scope", {}).get("revision", 0)
            if payload["expected_revision"] != revision:
                denied("organization_scope_conflict", 409)
            configured = MembershipScope.model_validate({key_: value for key_, value in payload.items() if key_ != "expected_revision"})
            data = catalog(connection, tenant)
            eligible = effective_scope(configured, data)
            eligible["society_ids"] = [item["id"] for item in data["societies"] if item["status"] == "active"
                and any(parent["id"] == item["issuer_id"] and parent["status"] == "active" for parent in data["issuers"])]
            for field in ("society_ids", "division_ids"):
                if getattr(configured, field) != ["*"] and not set(getattr(configured, field)).issubset(set(eligible[field])):
                    denied("organization_scope_reference_invalid", 422, field)
            result = {**configured.model_dump(), "revision": revision + 1}
            connection.execute(text("update admin.memberships set metadata=cast(:metadata as jsonb), updated_at=now() where tenant_id=:tenant and id=:id"),
                               {"metadata": json.dumps({**metadata, "scope": result}), "tenant": tenant, "id": row["id"]})
            self.repository._record_audit_event(connection, tenant_id=tenant, action=operation, resource_type="membership",
                resource_id=row["id"], before_state={**before, "revision": revision}, after_state=result,
                idempotency_key=key, correlation_id=correlation, metadata={}, actor_user_id=self.repository._actor_user_id(connection, actor_email))
            self.repository._complete_idempotent_command(connection, tenant, operation, key, result, 200)
            return result
