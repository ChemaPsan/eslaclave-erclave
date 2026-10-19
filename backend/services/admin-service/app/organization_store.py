"""Tenant-serialized organization commands and the legacy read/write adapter."""
import json

from sqlalchemy import func, or_, select, text
from erclave_common.errors import ErclaveError

from .models import AuditEvent, Division, FiscalIssuer, OrganizationAuthority, OrganizationImport, OrganizationLegacyMapping, Society, new_id
from .organization_migration import TABLES, OrganizationMigrationError, apply_import, build_plan, digest, read_profile

MODELS = {"fiscal-issuers": FiscalIssuer, "societies": Society, "divisions": Division}
KINDS = {"fiscal-issuers": "fiscal_issuer", "societies": "society", "divisions": "division"}
PREFIXES = {"fiscal-issuers": "EMI", "societies": "SOC", "divisions": "DIV"}
CONTACT_FIELDS = ("contact_name", "contact_email", "contact_phone", "contact_position")
FISCAL_FIELDS = ("legal_name", "tax_id", "fiscal_regime", "cfdi_usage", "fiscal_address", "postal_code", "country_code")


def error(code, field=None, status=409):
    # Codes and field paths are public; SQL diagnostics and captured fiscal values are not.
    raise ErclaveError(code, "Organization operation could not be completed.", status,
                       {"field": field} if field else {})


def lock_organization(connection, tenant_id):
    connection.execute(text("select pg_advisory_xact_lock(hashtextextended(:key,0))"),
                       {"key": f"admin.organization.import:{tenant_id}"})


def authority(connection, tenant_id):
    table = OrganizationAuthority.__table__
    return connection.execute(select(table).where(table.c.tenant_id == tenant_id)).mappings().first()


def structure_hash(profile):
    return digest({key: profile.get(key, []) for key in ("legal_entities", "branches")})


def rows(connection, model, tenant_id):
    table = model.__table__
    return [dict(row) for row in connection.execute(select(table).where(table.c.tenant_id == tenant_id)).mappings()]


def activate_organization(connection, tenant_id, source_hash, plan_hash, operator, correlation_id, resolutions=None):
    """Explicit reviewed switch. Archive a changed shadow before rebuilding it atomically."""
    lock_organization(connection, tenant_id)
    active = authority(connection, tenant_id)
    if active:
        original_plan = build_plan(tenant_id, active["source_profile"], resolutions)
        if active["source_hash"] != source_hash or original_plan["plan_hash"] != plan_hash:
            error("organization_review_changed")
        if active["projection_hash"] != structure_hash(read_profile(connection, tenant_id, lock=True)):
            error("organization_projection_changed")
        return {"status": "already_active"}
    profile = read_profile(connection, tenant_id, lock=True)
    plan = build_plan(tenant_id, profile, resolutions)
    if source_hash != plan["source_hash"] or plan_hash != plan["plan_hash"]:
        error("organization_review_changed")
    previous = rows(connection, OrganizationImport, tenant_id)
    archive = {}
    if previous:
        batch = previous[0]
        old_plan = build_plan(tenant_id, batch["source_profile"], batch["resolutions"])
        if batch["source_hash"] != old_plan["source_hash"] or batch["plan_hash"] != old_plan["plan_hash"]:
            error("organization_shadow_changed")
        # No edits to a prepared destination may be lost during reconciliation.
        for name, table in TABLES.items():
            actual = connection.execute(select(table).where(table.c.tenant_id == tenant_id)).mappings().all()
            expected = old_plan["rows"][name]
            columns = {key for row in expected for key in row}
            if sorted(digest({key: row[key] for key in columns}) for row in actual) != sorted(map(digest, expected)):
                error("organization_shadow_changed")
        # CONT-02 columns must not have been edited outside the governed switch.
        if any(item.get("postal_code") or item.get("country_code") for item in rows(connection, FiscalIssuer, tenant_id)):
            error("organization_shadow_changed")
        if batch["source_hash"] != source_hash or batch["plan_hash"] != plan_hash:
            archive = {"batch": dict(batch), "tables": {name: [dict(row) for row in connection.execute(
                select(table).where(table.c.tenant_id == tenant_id)).mappings()] for name, table in TABLES.items()}}
            # Only an unactivated, byte-verified shadow is replaced, never live organization data.
            for model in (OrganizationLegacyMapping, Division, Society, FiscalIssuer, OrganizationImport):
                connection.execute(model.__table__.delete().where(model.__table__.c.tenant_id == tenant_id))
    apply_import(connection, tenant_id, expected_source_hash=source_hash, expected_plan_hash=plan_hash,
                 operator=operator, correlation_id=correlation_id, resolutions=resolutions)
    # CONT-01's reviewed plan stays byte-compatible. Promote the new optional fields
    # from preserved source items only at activation; conflicting aliases need review.
    optional_fields = {}
    for item in plan["rows"]["organization_legacy_mappings"]:
        if item["collection"] != "legal_entities":
            continue
        destination = optional_fields.setdefault(item["issuer_id"], {})
        for field, maximum in (("postal_code", 20), ("country_code", 2)):
            value = item["source_item"].get(field)
            if value in (None, ""):
                continue
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
                error("organization_value_invalid", field, 422)
            value = value.strip().upper() if field == "country_code" else value.strip()
            if field == "country_code" and (len(value) != 2 or not value.isascii() or not value.isalpha()):
                error("organization_value_invalid", field, 422)
            if field in destination and destination[field] != value:
                error("organization_review_changed", field)
            destination[field] = value
    for issuer_id, values in optional_fields.items():
        if values:
            connection.execute(FiscalIssuer.__table__.update().where(
                FiscalIssuer.tenant_id == tenant_id, FiscalIssuer.id == issuer_id).values(**values))
    connection.execute(OrganizationAuthority.__table__.insert().values(
        tenant_id=tenant_id, source_hash=source_hash, projection_hash=structure_hash(profile),
        source_profile=profile, prior_shadow=json.loads(json.dumps(archive, default=str)), operator=operator,
    ))
    connection.execute(AuditEvent.__table__.insert().values(
        id=new_id("aud"), tenant_id=tenant_id, actor_type="system", action="admin.organization.activate",
        resource_type="organization_authority", resource_id=tenant_id, source_service="admin-service",
        correlation_id=correlation_id, idempotency_key=f"cont02:{plan_hash}",
        after_state={"source_hash": source_hash, "plan_hash": plan_hash, "reconciled_shadow": bool(archive)},
        metadata={"operator": operator, "authority": "normalized"},
    ))
    return {"status": "activated", "reconciled_shadow": bool(archive)}


class OrganizationStore:
    def __init__(self, repository):
        self.repository = repository
        self.engine = repository.engine

    def ensure_active(self, connection, tenant_id, actor, correlation_id):
        lock_organization(connection, tenant_id)
        active = authority(connection, tenant_id)
        profile = read_profile(connection, tenant_id, lock=True)
        if not active:
            # An empty original has no identities to infer. Nonempty data requires the reviewed CLI.
            if profile.get("legal_entities") or profile.get("branches"):
                error("organization_review_required")
            plan = build_plan(tenant_id, profile)
            activate_organization(connection, tenant_id, plan["source_hash"], plan["plan_hash"], actor or "local-system", correlation_id)
        elif active["projection_hash"] != structure_hash(profile):
            error("organization_projection_changed")
        return profile

    @staticmethod
    def get_row(connection, tenant_id, kind, record_id):
        table = MODELS[kind].__table__
        row = connection.execute(select(table).where(table.c.tenant_id == tenant_id, table.c.id == record_id)).mappings().first()
        if not row:
            error("organization_record_not_found", status=404)
        return dict(row)

    def public_row(self, connection, tenant_id, kind, row):
        item = {key: value for key, value in row.items() if key not in ("tenant_id", "created_at", "updated_at", "contact")}
        if kind == "fiscal-issuers":
            item.update({key: row["contact"].get(key) for key in CONTACT_FIELDS})
        elif kind == "societies":
            item["issuer_name"] = self.get_row(connection, tenant_id, "fiscal-issuers", row["issuer_id"])["legal_name"]
        else:
            item["society_name"] = self.get_row(connection, tenant_id, "societies", row["society_id"])["name"]
        return item

    def list(self, tenant_id, kind, *, q="", status=None, parent_id=None, limit=25, offset=0):
        table = MODELS[kind].__table__
        filters = [table.c.tenant_id == tenant_id]
        if status:
            filters.append(table.c.status == status)
        if q.strip():
            label = table.c.legal_name if kind == "fiscal-issuers" else table.c.name
            filters.append(or_(table.c.code.ilike(f"%{q.strip()}%"), label.ilike(f"%{q.strip()}%")))
        if parent_id and kind != "fiscal-issuers":
            filters.append((table.c.issuer_id if kind == "societies" else table.c.society_id) == parent_id)
        with self.engine.connect() as connection:
            if not authority(connection, tenant_id):
                source = read_profile(connection, tenant_id)
                if source.get("legal_entities") or source.get("branches"):
                    error("organization_review_required")
                if connection.execute(select(table.c.id).where(table.c.tenant_id == tenant_id).limit(1)).first():
                    error("organization_review_required")
            total = connection.execute(select(func.count()).select_from(table).where(*filters)).scalar_one()
            items = connection.execute(select(table).where(*filters).order_by(table.c.code, table.c.id).limit(limit).offset(offset)).mappings()
            data = [self.public_row(connection, tenant_id, kind, row) for row in items]
            code_mode = connection.execute(text("select mode from admin.code_sequences where tenant_id=:tenant and document_type=:type"),
                {"tenant": tenant_id, "type": f"admin.{KINDS[kind]}"}).scalar() or "managed"
        return {"data": data, "meta": {"total": total, "limit": limit, "offset": offset, "code_mode": code_mode}}

    def get(self, tenant_id, kind, record_id):
        with self.engine.connect() as connection:
            if not authority(connection, tenant_id):
                error("organization_review_required")
            return self.public_row(connection, tenant_id, kind, self.get_row(connection, tenant_id, kind, record_id))

    def allocate_code(self, connection, tenant_id, kind, requested):
        prefix = PREFIXES[kind]
        document_type = f"admin.{KINDS[kind]}"
        connection.execute(text("""insert into admin.code_sequences
            (id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
            values(:id,:tenant,:type,'admin',:es,:en,:prefix,'-',1,6,'managed',true,'active')
            on conflict (tenant_id,document_type) do nothing"""),
            {"id": new_id("seq"), "tenant": tenant_id, "type": document_type, "prefix": prefix,
             "es": {"EMI": "Emisores", "SOC": "Sociedades", "DIV": "Divisiones"}[prefix], "en": kind})
        sequence = connection.execute(text("select * from admin.code_sequences where tenant_id=:tenant and document_type=:type for update"),
                                      {"tenant": tenant_id, "type": document_type}).mappings().one()
        if sequence["status"] != "active":
            error("code_sequence_not_found")
        if sequence["mode"] == "manual":
            if not requested:
                error("manual_business_code_required", "code", 422)
            return requested.strip().upper()
        if requested:
            error("organization_code_managed", "code", 422)
        table = MODELS[kind].__table__
        number = sequence["next_number"]
        while True:
            code = f"{sequence['prefix']}{sequence['separator']}{number:0{sequence['padding']}d}"
            number += 1
            if not connection.execute(select(table.c.id).where(table.c.tenant_id == tenant_id, func.lower(table.c.code) == code.lower())).first():
                break
        connection.execute(text("update admin.code_sequences set next_number=:number,updated_at=now() where tenant_id=:tenant and id=:id"),
                           {"number": number, "tenant": tenant_id, "id": sequence["id"]})
        return code

    def write(self, connection, tenant_id, kind, payload, record_id, action, key, correlation, actor, *, legacy=False):
        table = MODELS[kind].__table__
        before = self.get_row(connection, tenant_id, kind, record_id) if record_id else None
        values = dict(payload)
        if before and "code" in values:
            if values["code"] != before["code"]:
                error("organization_code_immutable", "code", 422)
            values.pop("code")
        if kind == "fiscal-issuers":
            contact = dict(before["contact"]) if before else {}
            contact.update({name: values.pop(name) for name in CONTACT_FIELDS if name in values})
            values["contact"] = contact
            if "tax_id" in values:
                values["tax_id"] = (values["tax_id"] or "").strip().upper() or None
            tax_id = values.get("tax_id", before.get("tax_id") if before else None)
            if tax_id and connection.execute(select(table.c.id).where(table.c.tenant_id == tenant_id,
                    func.upper(func.trim(table.c.tax_id)) == tax_id.upper(), table.c.id != (record_id or ""))).first():
                error("organization_tax_id_duplicate", "tax_id")
        if not before:
            values.update(id=new_id(PREFIXES[kind].lower()), tenant_id=tenant_id, status="active",
                          code=payload["code"].strip().upper() if legacy and payload.get("code") else self.allocate_code(connection, tenant_id, kind, payload.get("code")))
        after = {**(before or {}), **values}
        name_field = "legal_name" if kind == "fiscal-issuers" else "name"
        if not isinstance(after.get(name_field), str) or not after[name_field].strip():
            error("organization_required_value", name_field, 422)
        # Legacy adapters also cross this boundary; reject oversized values before SQL.
        for field, maximum in {name_field: 240, "code": 80, "tax_id": 80, "fiscal_regime": 80,
                               "cfdi_usage": 80, "postal_code": 20, "country_code": 2, "phone": 80,
                               "fiscal_address": 2000, "address": 2000}.items():
            if after.get(field) is not None and (not isinstance(after[field], str) or len(after[field]) > maximum):
                error("organization_value_invalid", field, 422)
        for field, value in after.get("contact", {}).items():
            if field in CONTACT_FIELDS and value is not None and (not isinstance(value, str) or len(value) > (80 if field == "contact_phone" else 240)):
                error("organization_value_invalid", field, 422)
        if "base_currency" in after:
            after["base_currency"] = str(after["base_currency"]).upper()
            if not before or "base_currency" in values:
                if not connection.execute(text("select id from admin.catalog_items where tenant_id=:tenant and catalog_code='currencies' and code=:code and status='active'"),
                                          {"tenant": tenant_id, "code": after["base_currency"]}).first():
                    error("organization_currency_invalid", "base_currency", 422)
                values["base_currency"] = after["base_currency"]
        if kind != "fiscal-issuers":
            parent_kind, field = ("fiscal-issuers", "issuer_id") if kind == "societies" else ("societies", "society_id")
            if not after.get(field):
                error("organization_required_value", field, 422)
            try:
                parent = self.get_row(connection, tenant_id, parent_kind, after[field])
            except ErclaveError as exc:
                if exc.code == "organization_record_not_found":
                    error("organization_parent_invalid", field, 422)
                raise
            if parent["status"] != "active" and (after["status"] == "active" or not before or field in values):
                error("organization_parent_inactive", field)
        if after["status"] == "inactive" and (not before or before["status"] == "active"):
            child_model = Society if kind == "fiscal-issuers" else Division if kind == "societies" else None
            if child_model:
                child = child_model.__table__
                parent_col = child.c.issuer_id if kind == "fiscal-issuers" else child.c.society_id
                if connection.execute(select(child.c.id).where(child.c.tenant_id == tenant_id, parent_col == record_id, child.c.status == "active").limit(1)).first():
                    error("organization_active_dependents")
        if not before and connection.execute(select(table.c.id).where(table.c.tenant_id == tenant_id, func.lower(table.c.code) == values["code"].lower())).first():
            error("organization_code_duplicate", "code")
        # Remove/reinsert affected equivalences within this transaction to respect immediate composite FKs.
        mapping = OrganizationLegacyMapping.__table__
        mappings = []
        if before and ((kind == "societies" and "issuer_id" in values) or (kind == "divisions" and "society_id" in values)):
            target_col = mapping.c.society_id if kind == "societies" else mapping.c.division_id
            extra = mapping.c.collection == "legal_entities" if kind == "societies" else mapping.c.collection == "branches"
            mappings = [dict(row) for row in connection.execute(select(mapping).where(mapping.c.tenant_id == tenant_id, target_col == record_id, extra)).mappings()]
            connection.execute(mapping.delete().where(mapping.c.tenant_id == tenant_id, target_col == record_id, extra))
        if before:
            connection.execute(table.update().where(table.c.tenant_id == tenant_id, table.c.id == record_id).values(**values, updated_at=func.now()))
        else:
            connection.execute(table.insert().values(**values))
            record_id = values["id"]
        for item in mappings:
            item["issuer_id" if kind == "societies" else "society_id"] = values["issuer_id" if kind == "societies" else "society_id"]
            connection.execute(mapping.insert().values(**item))
        result = self.public_row(connection, tenant_id, kind, self.get_row(connection, tenant_id, kind, record_id))
        self.repository._record_audit_event(connection, tenant_id, f"admin.{KINDS[kind]}.{action}", KINDS[kind], record_id,
            self.public_row(connection, tenant_id, kind, before) if before else None, result, key, correlation,
            {"authority": "normalized"}, self.repository._actor_user_id(connection, actor))
        return result

    def project(self, connection, tenant_id):
        source = read_profile(connection, tenant_id, lock=True)
        mappings = rows(connection, OrganizationLegacyMapping, tenant_id)
        societies = rows(connection, Society, tenant_id)
        issuers = {row["id"]: row for row in rows(connection, FiscalIssuer, tenant_id)}
        legal_map = {row["society_id"]: row for row in mappings if row["collection"] == "legal_entities"}
        division_map = {row["division_id"]: row for row in mappings if row["collection"] == "branches"}
        prior_entities = {row["id"]: row for row in source.get("legal_entities", [])}
        prior_branches = {row["id"]: row for row in source.get("branches", [])}
        legal_ids = {row["id"]: legal_map.get(row["id"], {}).get("legacy_id", row["id"]) for row in societies}
        entities, branches = [], []
        for row in societies:
            issuer = issuers[row["issuer_id"]]
            legacy_id = legal_ids[row["id"]]
            original = legal_map.get(row["id"], {}).get("source_item", {})
            entities.append({**original, **prior_entities.get(legacy_id, {}), **{key: issuer.get(key) for key in FISCAL_FIELDS},
                **issuer["contact"], "id": legacy_id, "code": row["code"], "name": row["name"], "status": row["status"],
                "society_id": row["id"], "issuer_id": row["issuer_id"], "base_currency": row["base_currency"]})
        for row in rows(connection, Division, tenant_id):
            legacy_id = division_map.get(row["id"], {}).get("legacy_id", row["id"])
            original = division_map.get(row["id"], {}).get("source_item", {})
            branches.append({**original, **prior_branches.get(legacy_id, {}), **{key: row[key] for key in ("code", "name", "status", "address", "phone")},
                             "id": legacy_id, "legal_entity_id": legal_ids[row["society_id"]], "division_id": row["id"], "society_id": row["society_id"]})
        profile = {**source, "legal_entities": sorted(entities, key=lambda row: row["id"]), "branches": sorted(branches, key=lambda row: row["id"])}
        self.repository._write_organization_profile(connection, tenant_id, profile)
        table = OrganizationAuthority.__table__
        connection.execute(table.update().where(table.c.tenant_id == tenant_id).values(projection_hash=structure_hash(profile)))
        return profile

    def command(self, tenant_id, kind, payload, record_id, action, key, correlation, actor):
        with self.engine.begin() as connection:
            self.ensure_active(connection, tenant_id, actor, correlation)
            operation = f"admin.{KINDS[kind]}.{action}:{record_id or 'new'}"
            replay = self.repository._begin_idempotent_command(connection, tenant_id, operation, key,
                        self.repository._command_request_hash(payload))
            if replay is not None:
                return replay
            result = self.write(connection, tenant_id, kind, payload, record_id, action, key, correlation, actor)
            self.project(connection, tenant_id)
            self.repository._complete_idempotent_command(connection, tenant_id, operation, key, result, 201 if not record_id else 200)
            return result

    def resolve_legacy(self, connection, tenant_id, collection, legacy_id):
        mapping = OrganizationLegacyMapping.__table__
        column = mapping.c.society_id if collection == "legal_entities" else mapping.c.division_id
        return connection.execute(select(column).where(mapping.c.tenant_id == tenant_id, mapping.c.collection == collection,
                                                      mapping.c.legacy_id == legacy_id)).scalar_one_or_none() or legacy_id

    def legacy_command(self, connection, tenant_id, collection, payload, legacy_id, key, correlation):
        self.ensure_active(connection, tenant_id, None, correlation)
        operation = f"admin.organization.legacy:{collection}:{legacy_id or 'new'}"
        from .repositories import IdempotencyConflictError
        try:
            replay = self.repository._begin_idempotent_command(connection, tenant_id, operation, key, self.repository._command_request_hash(payload))
        except IdempotencyConflictError:
            error("idempotency_key_reused")
        if replay is not None:
            return replay
        kind = "societies" if collection == "legal_entities" else "divisions"
        record_id = self.resolve_legacy(connection, tenant_id, collection, legacy_id) if legacy_id else None
        values = dict(payload)
        if collection == "legal_entities":
            if record_id:
                society = self.get_row(connection, tenant_id, kind, record_id)
                issuer_id = society["issuer_id"]
                if any(field in values for field in (*FISCAL_FIELDS, *CONTACT_FIELDS)):
                    table = Society.__table__
                    if connection.execute(select(func.count()).select_from(table).where(table.c.tenant_id == tenant_id, table.c.issuer_id == issuer_id)).scalar_one() > 1:
                        error("organization_shared_issuer")
                    self.write(connection, tenant_id, "fiscal-issuers", {k: v for k, v in values.items() if k in (*FISCAL_FIELDS, *CONTACT_FIELDS)}, issuer_id, "update", key, correlation, None)
            else:
                issuer_id = self.write(connection, tenant_id, "fiscal-issuers", {k: v for k, v in values.items() if k in (*FISCAL_FIELDS, *CONTACT_FIELDS)}, None, "create", key, correlation, None)["id"]
            values = {**({"issuer_id": issuer_id, "base_currency": "MXN"} if not record_id else {}),
                      **({"name": values["legal_name"]} if "legal_name" in values else {}),
                      **({"status": values["status"]} if record_id and "status" in values else {})}
        else:
            if "legal_entity_id" in values:
                values["society_id"] = self.resolve_legacy(connection, tenant_id, "legal_entities", values.pop("legal_entity_id"))
            if not record_id and not values.get("society_id"):
                error("organization_society_required", "legal_entity_id", 422)
        result = self.write(connection, tenant_id, kind, values, record_id, "update" if record_id else "create", key, correlation, None, legacy=True)
        profile = self.project(connection, tenant_id)
        normalized_key = "society_id" if kind == "societies" else "division_id"
        legacy = next(row for row in profile[collection] if row[normalized_key] == result["id"])
        self.repository._complete_idempotent_command(connection, tenant_id, operation, key, legacy, 200 if record_id else 201)
        return legacy
