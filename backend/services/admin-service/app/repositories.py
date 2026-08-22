import hashlib
import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine

from .seeds.catalog import MVP_MODULE_SEEDS, get_module_seed

from .schemas import (
    BackofficeTenantRead,
    BackofficeUsageDailyRead,
    BackofficeUsageSummaryRead,
    CatalogItemCreateRequest,
    CatalogItemRead,
    CatalogItemUpdateRequest,
    CodeSequenceAllocationRead,
    CodeSequenceNextRequest,
    CodeSequenceRead,
    CodeSequenceUpdateRequest,
    EntitlementRead,
    PermissionRead,
    PolicyDecision,
    RoleRead,
    SessionBranchRead,
    SessionContextRead,
    SessionScopeRead,
    SettingRead,
    TenantRead,
    UnitOfMeasureCreateRequest,
    UnitOfMeasureRead,
    UnitOfMeasureUpdateRequest,
    UserRead,
)


class RolePermissionConflictError(Exception):
    pass


class RolePermissionValidationError(Exception):
    pass


class RolePermissionForbiddenError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


OWNER_PERMISSION_FLOOR = {
    "admin.tenant.read",
    "admin.user.read",
    "admin.role.read",
    "admin.role.permissions.manage",
    "admin.entitlement.manage",
}


class AdminRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

    def _lock_module_entitlements(self, connection, tenant_id: str):
        return connection.execute(
            text("""select module_code,status,source,tenant_enabled,
                (status='active' and tenant_enabled) as effective_active,limits
                from admin.tenant_modules where tenant_id=:tenant_id order by module_code for update"""),
            {"tenant_id": tenant_id},
        ).mappings().all()

    def _validate_module_transition(self, rows, module_code: str, effective_active: bool) -> None:
        effective = {
            row["module_code"]: row["status"] == "active" and bool(row["tenant_enabled"])
            for row in rows
        }
        effective[module_code] = effective_active
        module = get_module_seed(module_code)
        if effective_active and module:
            missing = sorted(code for code in module.dependencies if not effective.get(code, False))
            if missing:
                raise ValueError(f"module_dependencies_required:{','.join(missing)}")
        if not effective_active:
            dependents = sorted(
                item.code
                for item in MVP_MODULE_SEEDS
                if module_code in item.dependencies and effective.get(item.code, False)
            )
            if dependents:
                raise ValueError(f"module_dependency_in_use:{','.join(dependents)}")

    def default_organization_profile(self, commercial_name: str, legal_name: str | None = None) -> dict:
        return {
            "corporate": {
                "commercial_name": commercial_name,
                "legal_name": legal_name or commercial_name,
                "tax_id": "",
                "phone": "",
                "contact_name": "",
                "contact_email": "",
                "contact_phone": "",
                "contact_position": "",
            },
            "legal_entities": [],
            "branches": [],
        }

    @staticmethod
    def _normalize_catalog_code(catalog_code: str, code: str) -> str:
        return code.strip().upper() if catalog_code == "currencies" else code.strip().lower()

    def list_catalog_items(self, tenant_id: str, catalog_code: str, *, include_inactive: bool = False, q: str | None = None) -> list[CatalogItemRead]:
        filters = ["tenant_id=:tenant_id", "catalog_code=:catalog_code"]
        params = {"tenant_id": tenant_id, "catalog_code": catalog_code, "q": f"%{(q or '').strip().lower()}%"}
        if not include_inactive:
            filters.append("status='active'")
        if (q or "").strip():
            filters.append("(lower(code) like :q or lower(name_es) like :q or lower(name_en) like :q)")
        with self.engine.connect() as connection:
            rows = connection.execute(text(f"select id,catalog_code,code,name_es,name_en,metadata,system_default,status from admin.catalog_items where {' and '.join(filters)} order by name_es,code"), params).mappings().all()
        return [CatalogItemRead.model_validate(dict(row)) for row in rows]

    def get_catalog_item(self, tenant_id: str, catalog_code: str, code: str, *, active_only: bool = False) -> CatalogItemRead | None:
        normalized = self._normalize_catalog_code(catalog_code, code)
        active = " and status='active'" if active_only else ""
        with self.engine.connect() as connection:
            row = connection.execute(text(f"select id,catalog_code,code,name_es,name_en,metadata,system_default,status from admin.catalog_items where tenant_id=:tenant_id and catalog_code=:catalog_code and code=:code{active}"), {"tenant_id": tenant_id, "catalog_code": catalog_code, "code": normalized}).mappings().first()
        return CatalogItemRead.model_validate(dict(row)) if row else None

    def create_catalog_item(self, tenant_id: str, catalog_code: str, payload: CatalogItemCreateRequest, idempotency_key: str, correlation_id: str, actor_email: str | None = None) -> CatalogItemRead:
        operation = f"admin.catalog.create:{catalog_code}"
        normalized = self._normalize_catalog_code(catalog_code, payload.code)
        request_hash = self._command_request_hash({"catalog_code": catalog_code, "payload": payload.model_dump(mode="json") | {"code": normalized}})
        item_id = f"cat_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return CatalogItemRead.model_validate(replay)
            row = connection.execute(text("""insert into admin.catalog_items(id,tenant_id,catalog_code,code,name_es,name_en,metadata,system_default,status)
                values(:id,:tenant,:catalog,:code,:name_es,:name_en,cast(:metadata as jsonb),false,'active')
                on conflict(tenant_id,catalog_code,code) do nothing
                returning id,catalog_code,code,name_es,name_en,metadata,system_default,status"""), {"id": item_id, "tenant": tenant_id, "catalog": catalog_code, "code": normalized, "name_es": payload.name_es.strip(), "name_en": payload.name_en.strip(), "metadata": json.dumps(payload.metadata)}).mappings().first()
            if not row:
                raise ValueError("catalog_item_code_exists")
            result = dict(row)
            self._record_audit_event(connection, tenant_id=tenant_id, action=operation, resource_type="catalog_item", resource_id=item_id, before_state=None, after_state=result, idempotency_key=idempotency_key, correlation_id=correlation_id, metadata={"catalog_code": catalog_code}, actor_user_id=self._actor_user_id(connection, actor_email))
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 201)
        return CatalogItemRead.model_validate(result)

    def update_catalog_item(self, tenant_id: str, catalog_code: str, item_id: str, payload: CatalogItemUpdateRequest, idempotency_key: str, correlation_id: str, actor_email: str | None = None) -> CatalogItemRead | None:
        values = payload.model_dump(exclude_none=True)
        operation = f"admin.catalog.update:{catalog_code}:{item_id}"
        request_hash = self._command_request_hash({"item_id": item_id, "payload": values})
        with self.engine.begin() as connection:
            before = connection.execute(text("select id,catalog_code,code,name_es,name_en,metadata,system_default,status from admin.catalog_items where tenant_id=:tenant and catalog_code=:catalog and id=:id for update"), {"tenant": tenant_id, "catalog": catalog_code, "id": item_id}).mappings().first()
            if not before:
                return None
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return CatalogItemRead.model_validate(replay)
            if "metadata" in values:
                values["metadata"] = json.dumps(values["metadata"])
            if values:
                assignments = ",".join(f"{name}=cast(:{name} as jsonb)" if name == "metadata" else f"{name}=:{name}" for name in values)
                row = connection.execute(text(f"update admin.catalog_items set {assignments},updated_at=now() where tenant_id=:tenant and catalog_code=:catalog and id=:id returning id,catalog_code,code,name_es,name_en,metadata,system_default,status"), {"tenant": tenant_id, "catalog": catalog_code, "id": item_id, **values}).mappings().one()
            else:
                row = before
            result = dict(row)
            self._record_audit_event(connection, tenant_id=tenant_id, action="admin.catalog.update", resource_type="catalog_item", resource_id=item_id, before_state=dict(before), after_state=result, idempotency_key=idempotency_key, correlation_id=correlation_id, metadata={"catalog_code": catalog_code}, actor_user_id=self._actor_user_id(connection, actor_email))
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)
        return CatalogItemRead.model_validate(result)

    def list_code_sequences(self, tenant_id: str) -> list[CodeSequenceRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(text("""select id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status
                from admin.code_sequences where tenant_id=:tenant_id order by module_code,document_type"""), {"tenant_id": tenant_id}).mappings().all()
        return [CodeSequenceRead.model_validate(dict(row)) for row in rows]

    def update_code_sequence(self, tenant_id: str, sequence_id: str, payload: CodeSequenceUpdateRequest, idempotency_key: str, correlation_id: str, actor_email: str | None = None) -> CodeSequenceRead | None:
        values = payload.model_dump(exclude_none=True)
        if "prefix" in values:
            values["prefix"] = values["prefix"].strip().upper()
        operation = f"admin.code_sequence.update:{sequence_id}"
        request_hash = self._command_request_hash({"sequence_id": sequence_id, "payload": values})
        projection = "id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status"
        with self.engine.begin() as connection:
            before = connection.execute(text(f"select {projection} from admin.code_sequences where tenant_id=:tenant_id and id=:id for update"), {"tenant_id": tenant_id, "id": sequence_id}).mappings().first()
            if not before:
                return None
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return CodeSequenceRead.model_validate(replay)
            if "next_number" in values and values["next_number"] < before["next_number"]:
                raise ValueError("code_sequence_cannot_rewind")
            if values:
                assignments = ",".join(f"{key}=:{key}" for key in values)
                row = connection.execute(text(f"update admin.code_sequences set {assignments},updated_at=now() where tenant_id=:tenant_id and id=:id returning {projection}"), {"tenant_id": tenant_id, "id": sequence_id, **values}).mappings().one()
            else:
                row = before
            result = dict(row)
            self._record_audit_event(connection, tenant_id=tenant_id, action="admin.code_sequence.update", resource_type="code_sequence", resource_id=sequence_id, before_state=dict(before), after_state=result, idempotency_key=idempotency_key, correlation_id=correlation_id, metadata={"document_type": result["document_type"]}, actor_user_id=self._actor_user_id(connection, actor_email))
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)
        return CodeSequenceRead.model_validate(result)

    def allocate_business_code(self, tenant_id: str, document_type: str, payload: CodeSequenceNextRequest, idempotency_key: str, correlation_id: str, actor_email: str | None = None) -> CodeSequenceAllocationRead | None:
        normalized_document_type = document_type.strip().lower()
        normalized_manual_code = payload.manual_code.strip().upper() if payload.manual_code else None
        operation = f"admin.code_sequence.next:{normalized_document_type}"
        request_hash = self._command_request_hash({"document_type": normalized_document_type, "manual_code": normalized_manual_code})
        with self.engine.begin() as connection:
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return CodeSequenceAllocationRead.model_validate(replay)
            sequence = connection.execute(text("""select id,document_type,prefix,separator,next_number,padding,mode,status
                from admin.code_sequences where tenant_id=:tenant_id and document_type=:document_type for update"""), {"tenant_id": tenant_id, "document_type": normalized_document_type}).mappings().first()
            if not sequence or sequence["status"] != "active":
                raise ValueError("code_sequence_not_found")
            if sequence["mode"] == "manual":
                if not normalized_manual_code:
                    raise ValueError("manual_business_code_required")
                code = normalized_manual_code
                sequence_number = None
            else:
                sequence_number = int(sequence["next_number"])
                code = f"{sequence['prefix']}{sequence['separator']}{sequence_number:0{sequence['padding']}d}"
                connection.execute(text("update admin.code_sequences set next_number=next_number+1,updated_at=now() where tenant_id=:tenant_id and id=:id"), {"tenant_id": tenant_id, "id": sequence["id"]})
            result = {"document_type": normalized_document_type, "mode": sequence["mode"], "code": code, "sequence_number": sequence_number}
            self._record_audit_event(connection, tenant_id=tenant_id, action="admin.code_sequence.allocate", resource_type="code_sequence", resource_id=sequence["id"], before_state=None, after_state=result, idempotency_key=idempotency_key, correlation_id=correlation_id, metadata={"document_type": normalized_document_type}, actor_user_id=self._actor_user_id(connection, actor_email))
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)
        return CodeSequenceAllocationRead.model_validate(result)

    def list_units_of_measure(self, tenant_id: str, *, include_inactive: bool = False, q: str | None = None) -> list[UnitOfMeasureRead]:
        filters = ["tenant_id=:tenant_id"]
        params = {"tenant_id": tenant_id, "q": f"%{(q or '').strip().lower()}%"}
        if not include_inactive:
            filters.append("status='active'")
        if (q or "").strip():
            filters.append("(lower(code) like :q or lower(name_es) like :q or lower(name_en) like :q or lower(symbol) like :q)")
        with self.engine.connect() as connection:
            rows = connection.execute(text(f"select id,code,name_es,name_en,symbol,category,decimal_places,system_default,status from admin.units_of_measure where {' and '.join(filters)} order by category,name_es,code"), params).mappings().all()
        return [UnitOfMeasureRead.model_validate(dict(row)) for row in rows]

    def get_unit_of_measure(self, tenant_id: str, code: str, *, active_only: bool = False) -> UnitOfMeasureRead | None:
        active = " and status='active'" if active_only else ""
        with self.engine.connect() as connection:
            row = connection.execute(text(f"select id,code,name_es,name_en,symbol,category,decimal_places,system_default,status from admin.units_of_measure where tenant_id=:tenant_id and upper(code)=upper(:code){active}"), {"tenant_id": tenant_id, "code": code.strip()}).mappings().first()
        return UnitOfMeasureRead.model_validate(dict(row)) if row else None

    def create_unit_of_measure(
        self,
        tenant_id: str,
        payload: UnitOfMeasureCreateRequest,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ) -> UnitOfMeasureRead:
        unit_id = f"uom_{uuid4().hex[:26]}"
        values = payload.model_dump()
        values.update({"id": unit_id, "tenant_id": tenant_id, "code": payload.code.strip().upper()})
        operation = "admin.unit.create"
        request_hash = self._command_request_hash({"payload": values | {"id": None, "tenant_id": None}})
        with self.engine.begin() as connection:
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return UnitOfMeasureRead.model_validate(replay)
            row = connection.execute(text("""insert into admin.units_of_measure(id,tenant_id,code,name_es,name_en,symbol,category,decimal_places,system_default,status) values(:id,:tenant_id,:code,:name_es,:name_en,:symbol,:category,:decimal_places,false,'active') on conflict(tenant_id,code) do nothing returning id,code,name_es,name_en,symbol,category,decimal_places,system_default,status"""), values).mappings().first()
            if not row:
                raise ValueError("unit_code_exists")
            result = dict(row)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action=operation,
                resource_type="unit_of_measure",
                resource_id=unit_id,
                before_state=None,
                after_state=result,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"code": result["code"], "system_default": False},
                actor_user_id=self._actor_user_id(connection, actor_email),
            )
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 201)
        return UnitOfMeasureRead.model_validate(result)

    def update_unit_of_measure(
        self,
        tenant_id: str,
        unit_id: str,
        payload: UnitOfMeasureUpdateRequest,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ) -> UnitOfMeasureRead | None:
        values = payload.model_dump(exclude_none=True)
        operation = f"admin.unit.update:{unit_id}"
        request_hash = self._command_request_hash({"unit_id": unit_id, "payload": values})
        with self.engine.begin() as connection:
            before = connection.execute(text("select id,code,name_es,name_en,symbol,category,decimal_places,system_default,status from admin.units_of_measure where tenant_id=:tenant_id and id=:id for update"), {"tenant_id": tenant_id, "id": unit_id}).mappings().first()
            if not before:
                return None
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return UnitOfMeasureRead.model_validate(replay)
            if values:
                assignments = ",".join(f"{key}=:{key}" for key in values)
                values.update({"tenant_id": tenant_id, "id": unit_id})
                row = connection.execute(text(f"update admin.units_of_measure set {assignments},updated_at=now() where tenant_id=:tenant_id and id=:id returning id,code,name_es,name_en,symbol,category,decimal_places,system_default,status"), values).mappings().first()
            else:
                row = before
            result = dict(row)
            if result != dict(before):
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action="admin.unit.update",
                    resource_type="unit_of_measure",
                    resource_id=unit_id,
                    before_state=dict(before),
                    after_state=result,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"code": result["code"]},
                    actor_user_id=self._actor_user_id(connection, actor_email),
                )
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)
        return UnitOfMeasureRead.model_validate(result)

    @staticmethod
    def _command_request_hash(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

    def _begin_idempotent_command(self, connection, tenant_id: str, operation: str, idempotency_key: str, request_hash: str) -> dict | None:
        connection.execute(text("select pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"), {"lock_key": f"{tenant_id}:{operation}:{idempotency_key}"})
        existing = connection.execute(text("""select request_hash,response_payload from admin.command_idempotency where tenant_id=:tenant_id and operation=:operation and idempotency_key=:idempotency_key"""), {"tenant_id": tenant_id, "operation": operation, "idempotency_key": idempotency_key}).mappings().first()
        if existing:
            if existing["request_hash"] != request_hash:
                raise IdempotencyConflictError("idempotency_key_reused")
            if existing["response_payload"] is not None:
                return dict(existing["response_payload"])
            raise IdempotencyConflictError("command_in_progress")
        connection.execute(text("""insert into admin.command_idempotency(id,tenant_id,operation,idempotency_key,request_hash) values(:id,:tenant_id,:operation,:idempotency_key,:request_hash)"""), {"id": f"cmd_{uuid4().hex[:26]}", "tenant_id": tenant_id, "operation": operation, "idempotency_key": idempotency_key, "request_hash": request_hash})
        return None

    @staticmethod
    def _complete_idempotent_command(connection, tenant_id: str, operation: str, idempotency_key: str, response_payload: dict, status_code: int) -> None:
        connection.execute(text("""update admin.command_idempotency set response_payload=cast(:response_payload as jsonb),status_code=:status_code,completed_at=now() where tenant_id=:tenant_id and operation=:operation and idempotency_key=:idempotency_key"""), {"response_payload": json.dumps(response_payload, default=str), "status_code": status_code, "tenant_id": tenant_id, "operation": operation, "idempotency_key": idempotency_key})

    @staticmethod
    def _actor_user_id(connection, actor_email: str | None) -> str | None:
        if not actor_email:
            return None
        return connection.execute(text("select id from admin.users where email=lower(:email)"), {"email": actor_email}).scalar_one_or_none()

    def get_tenant(self, tenant_id: str) -> TenantRead | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    select id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    from admin.tenants
                    where id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().first()

        return TenantRead.model_validate(dict(row)) if row else None

    def list_backoffice_tenants(self, search: str | None = None, limit: int = 50) -> list[BackofficeTenantRead]:
        normalized_search = (search or "").strip()
        params = {
            "search": f"%{normalized_search.lower()}%",
            "limit": max(1, min(limit, 100)),
        }
        search_clause = ""
        if normalized_search:
            search_clause = """
                and (
                    lower(tenants.id) like :search
                    or
                    lower(tenants.commercial_name) like :search
                    or lower(tenants.slug) like :search
                    or lower(coalesce(tenants.legal_name, '')) like :search
                    or lower(coalesce(settings.value::text, '')) like :search
                )
            """
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    f"""
                    select
                        tenants.id,
                        tenants.slug,
                        tenants.legal_name,
                        tenants.commercial_name,
                        tenants.status,
                        tenants.plan_id,
                        tenants.timezone,
                        tenants.locale,
                        owner_users.email as owner_email,
                        count(distinct memberships.id) filter (where memberships.status = 'active') as active_memberships,
                        count(distinct memberships.id) as total_memberships,
                        coalesce(
                            array_remove(array_agg(distinct tenant_modules.module_code) filter (where tenant_modules.status = 'active'), null),
                            array[]::varchar[]
                        ) as modules,
                        coalesce(
                            (
                                select jsonb_agg(
                                    jsonb_build_object(
                                        'module_code', entitlement.module_code,
                                        'status', entitlement.status,
                                        'source', entitlement.source,
                                        'tenant_enabled', entitlement.tenant_enabled,
                                        'effective_active', entitlement.status = 'active' and entitlement.tenant_enabled,
                                        'limits', entitlement.limits
                                    ) order by entitlement.module_code
                                )
                                from admin.tenant_modules entitlement
                                where entitlement.tenant_id = tenants.id
                            ),
                            '[]'::jsonb
                        ) as entitlements,
                        coalesce(jsonb_array_length(settings.value -> 'legal_entities'), 0) as legal_entities_count,
                        coalesce(jsonb_array_length(settings.value -> 'branches'), 0) as branches_count
                    from admin.tenants tenants
                    left join admin.tenant_settings settings
                        on settings.tenant_id = tenants.id
                        and settings.key = 'organization.profile'
                    left join admin.tenant_modules tenant_modules
                        on tenant_modules.tenant_id = tenants.id
                    left join admin.memberships memberships
                        on memberships.tenant_id = tenants.id
                    left join admin.membership_roles owner_membership_roles
                        on owner_membership_roles.tenant_id = tenants.id
                    left join admin.roles owner_roles
                        on owner_roles.tenant_id = tenants.id
                        and owner_roles.id = owner_membership_roles.role_id
                        and owner_roles.code = 'owner'
                    left join admin.memberships owner_memberships
                        on owner_memberships.tenant_id = tenants.id
                        and owner_memberships.id = owner_membership_roles.membership_id
                    left join admin.users owner_users
                        on owner_users.id = owner_memberships.user_id
                    where tenants.status <> 'cancelled'
                    {search_clause}
                    group by
                        tenants.id,
                        tenants.slug,
                        tenants.legal_name,
                        tenants.commercial_name,
                        tenants.status,
                        tenants.plan_id,
                        tenants.timezone,
                        tenants.locale,
                        owner_users.email,
                        settings.value
                    order by tenants.created_at desc, tenants.commercial_name
                    limit :limit
                    """
                ),
                params,
            ).mappings().all()

        return [BackofficeTenantRead.model_validate(dict(row)) for row in rows]

    def list_backoffice_usage(
        self,
        from_date,
        to_date,
        tenant_id: str | None = None,
        limit: int = 200,
    ) -> tuple[list[BackofficeUsageDailyRead], BackofficeUsageSummaryRead]:
        params = {
            "from_date": from_date,
            "to_date": to_date,
            "tenant_id": tenant_id,
            "limit": max(1, min(limit, 500)),
        }
        tenant_clause = "and usage.tenant_id = :tenant_id" if tenant_id else ""
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    f"""
                    select
                        usage.tenant_id,
                        tenants.slug as tenant_slug,
                        tenants.commercial_name as tenant_name,
                        usage.usage_date,
                        usage.active_users,
                        usage.api_requests,
                        usage.storage_mb,
                        usage.estimated_cost_mxn,
                        usage.source
                    from admin.tenant_usage_daily usage
                    join admin.tenants tenants on tenants.id = usage.tenant_id
                    where usage.usage_date between :from_date and :to_date
                    {tenant_clause}
                    order by usage.usage_date desc, tenants.commercial_name
                    limit :limit
                    """
                ),
                params,
            ).mappings().all()
            summary_row = connection.execute(
                text(
                    f"""
                    select
                        count(distinct usage.tenant_id) as tenants,
                        count(distinct usage.usage_date) as days,
                        coalesce(sum(usage.active_users), 0) as active_users,
                        coalesce(sum(usage.api_requests), 0) as api_requests,
                        coalesce(sum(usage.storage_mb), 0) as storage_mb,
                        coalesce(sum(usage.estimated_cost_mxn), 0) as estimated_cost_mxn
                    from admin.tenant_usage_daily usage
                    where usage.usage_date between :from_date and :to_date
                    {tenant_clause}
                    """
                ),
                params,
            ).mappings().one()

        return (
            [BackofficeUsageDailyRead.model_validate(dict(row)) for row in rows],
            BackofficeUsageSummaryRead.model_validate(dict(summary_row)),
        )

    def set_backoffice_tenant_status(
        self,
        tenant_id: str,
        new_status: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> TenantRead | None:
        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    from admin.tenants
                    where id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().first()
            if before is None:
                return None
            row = connection.execute(
                text(
                    """
                    update admin.tenants
                    set status = :status, updated_at = now()
                    where id = :tenant_id
                    returning id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    """
                ),
                {"tenant_id": tenant_id, "status": new_status},
            ).mappings().one()
            membership_status = "disabled" if new_status == "suspended" else "active"
            connection.execute(
                text(
                    """
                    update admin.memberships
                    set
                        status = :membership_status,
                        disabled_at = case when :membership_status = 'disabled' then now() else disabled_at end,
                        activated_at = case when :membership_status = 'active' then coalesce(activated_at, now()) else activated_at end,
                        updated_at = now()
                    where tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id, "membership_status": membership_status},
            )
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="backoffice.tenant.status",
                resource_type="tenant",
                resource_id=tenant_id,
                before_state=dict(before),
                after_state=dict(row),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"status": new_status},
            )

        tenants = self.list_backoffice_tenants(search=tenant_id, limit=1)
        return tenants[0] if tenants else BackofficeTenantRead.model_validate({**dict(row), "modules": []})

    def update_backoffice_tenant(
        self,
        tenant_id: str,
        changes: dict,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ) -> BackofficeTenantRead | None:
        operation = "backoffice.tenant.update"
        request_hash = self._command_request_hash({"tenant_id": tenant_id, "changes": changes})
        with self.engine.begin() as connection:
            before = connection.execute(
                text("""select id,slug,legal_name,commercial_name,status,plan_id,timezone,locale from admin.tenants where id=:tenant_id for update"""),
                {"tenant_id": tenant_id},
            ).mappings().first()
            if before is None:
                return None
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return TenantRead.model_validate(replay)
            if changes:
                assignments = ",".join(f"{field}=:{field}" for field in changes)
                params = {"tenant_id": tenant_id, **changes}
                row = connection.execute(
                    text(f"""update admin.tenants set {assignments},updated_at=now() where id=:tenant_id returning id,slug,legal_name,commercial_name,status,plan_id,timezone,locale"""),
                    params,
                ).mappings().one()
            else:
                row = before
            result = dict(row)
            if result != dict(before):
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action=operation,
                    resource_type="tenant",
                    resource_id=tenant_id,
                    before_state=dict(before),
                    after_state=result,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"fields": sorted(changes)},
                    actor_user_id=self._actor_user_id(connection, actor_email),
                )
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)
        return TenantRead.model_validate(result)

    def set_backoffice_entitlement(
        self,
        tenant_id: str,
        module_code: str,
        status: str,
        limits: dict,
        source: str,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ) -> EntitlementRead | None:
        operation = f"backoffice.tenant.entitlement.update:{module_code}"
        request_hash = self._command_request_hash(
            {"tenant_id": tenant_id, "module_code": module_code, "status": status, "limits": limits, "source": source}
        )
        with self.engine.begin() as connection:
            if connection.execute(text("select 1 from admin.tenants where id=:tenant_id"), {"tenant_id": tenant_id}).scalar_one_or_none() is None:
                return None
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return EntitlementRead.model_validate(replay)
            entitlement_rows = self._lock_module_entitlements(connection, tenant_id)
            before = next((row for row in entitlement_rows if row["module_code"] == module_code), None)
            tenant_enabled = bool(before["tenant_enabled"]) if before is not None else True
            self._validate_module_transition(entitlement_rows, module_code, status == "active" and tenant_enabled)
            row = connection.execute(
                text(
                    """
                    insert into admin.tenant_modules(id,tenant_id,module_code,status,source,tenant_enabled,limits)
                    values(:id,:tenant_id,:module_code,:status,:source,true,cast(:limits as jsonb))
                    on conflict(tenant_id,module_code) do update set
                        status=excluded.status,
                        source=excluded.source,
                        limits=excluded.limits,
                        updated_at=now()
                    returning module_code,status,source,tenant_enabled,(status='active' and tenant_enabled) as effective_active,limits
                    """
                ),
                {"id": f"tmo_{uuid4().hex[:26]}", "tenant_id": tenant_id, "module_code": module_code, "status": status, "source": source, "limits": json.dumps(limits)},
            ).mappings().one()
            result = dict(row)
            if status == "active":
                connection.execute(
                    text(
                        """
                        insert into admin.role_permissions(id,tenant_id,role_id,permission_id,scope)
                        select 'rpe_'||substr(md5(roles.tenant_id||':'||roles.id||':'||permissions.id),1,26),roles.tenant_id,roles.id,permissions.id,'{}'::jsonb
                        from admin.roles roles
                        join admin.permissions permissions on permissions.module_code=:module_code
                            and permissions.status='active'
                            and permissions.classification='tenant'
                            and permissions.assignable_to_tenant_role=true
                        where roles.tenant_id=:tenant_id and roles.code='owner' and roles.system_role=true and roles.status='active'
                        on conflict(tenant_id,role_id,permission_id) do nothing
                        """
                    ),
                    {"tenant_id": tenant_id, "module_code": module_code},
                )
            if before is None or result != dict(before):
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action=operation,
                    resource_type="tenant_module",
                    resource_id=module_code,
                    before_state=dict(before) if before else None,
                    after_state=result,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"source": source},
                    actor_user_id=self._actor_user_id(connection, actor_email),
                )
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)
        return EntitlementRead.model_validate(result)

    def delete_backoffice_tenant(
        self,
        tenant_id: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    from admin.tenants
                    where id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().first()
            if before is None:
                return None
            users = connection.execute(
                text(
                    """
                    select distinct users.id, users.email
                    from admin.memberships memberships
                    join admin.users users on users.id = memberships.user_id
                    where memberships.tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().all()
            user_ids = [row["id"] for row in users]
            orphan_emails = []

            connection.execute(
                text("delete from admin.audit_events where tenant_id = :tenant_id"),
                {"tenant_id": tenant_id},
            )
            for user_id in user_ids:
                connection.execute(
                    text("update admin.audit_events set actor_user_id = null where actor_user_id = :user_id"),
                    {"user_id": user_id},
                )
            connection.execute(text("delete from admin.role_permissions where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.membership_roles where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.memberships where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.tenant_modules where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.tenant_settings where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.tenant_usage_daily where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.roles where tenant_id = :tenant_id"), {"tenant_id": tenant_id})
            connection.execute(text("delete from admin.tenants where id = :tenant_id"), {"tenant_id": tenant_id})

            removed_global_users = 0
            for user_id in user_ids:
                remaining = connection.execute(
                    text("select count(*) from admin.memberships where user_id = :user_id"),
                    {"user_id": user_id},
                ).scalar_one()
                if remaining == 0:
                    connection.execute(text("delete from admin.users where id = :user_id"), {"user_id": user_id})
                    removed_global_users += 1
                    orphan_emails.extend(row["email"] for row in users if row["id"] == user_id)

        return {
            "tenant": dict(before),
            "deleted": True,
            "removed_memberships": len(user_ids),
            "removed_global_users": removed_global_users,
            "firebase_emails": orphan_emails,
        }

    def create_tenant(
        self,
        slug: str,
        commercial_name: str,
        legal_name: str | None,
        plan_id: str | None,
        timezone: str,
        locale: str,
        source: dict,
        organization_profile: dict | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> TenantRead:
        tenant_id = f"ten_{uuid4().hex[:26]}"
        profile = organization_profile or self.default_organization_profile(commercial_name, legal_name)
        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    from admin.tenants
                    where slug = lower(:slug)
                    """
                ),
                {"slug": slug},
            ).mappings().first()
            row = connection.execute(
                text(
                    """
                    insert into admin.tenants (
                        id,
                        slug,
                        legal_name,
                        commercial_name,
                        status,
                        plan_id,
                        timezone,
                        locale,
                        source_type,
                        source_id,
                        metadata
                    )
                    values (
                        :id,
                        lower(:slug),
                        :legal_name,
                        :commercial_name,
                        'provisioning',
                        :plan_id,
                        :timezone,
                        :locale,
                        :source_type,
                        :source_id,
                        cast(:metadata as jsonb)
                    )
                    on conflict (slug)
                    do update set
                        legal_name = excluded.legal_name,
                        commercial_name = excluded.commercial_name,
                        plan_id = excluded.plan_id,
                        timezone = excluded.timezone,
                        locale = excluded.locale,
                        source_type = excluded.source_type,
                        source_id = excluded.source_id,
                        metadata = excluded.metadata,
                        updated_at = now()
                    returning id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    """
                ),
                {
                    "id": tenant_id,
                    "slug": slug,
                    "legal_name": legal_name,
                    "commercial_name": commercial_name,
                    "plan_id": plan_id,
                    "timezone": timezone,
                    "locale": locale,
                    "source_type": source["type"],
                    "source_id": source["id"],
                    "metadata": json.dumps({"source": source}),
                },
            ).mappings().one()
            connection.execute(
                text(
                    """
                    insert into admin.tenant_settings (id, tenant_id, key, module_code, value)
                    values (:id, :tenant_id, 'organization.profile', 'admin', cast(:value as jsonb))
                    on conflict (tenant_id, key)
                    do update set
                        module_code = excluded.module_code,
                        value = case
                            when admin.tenant_settings.value = '{}'::jsonb then excluded.value
                            else admin.tenant_settings.value
                        end,
                        updated_at = now()
                    """
                ),
                {
                    "id": f"set_{uuid4().hex[:26]}",
                    "tenant_id": row["id"],
                    "value": json.dumps(profile),
                },
            )
            self._record_audit_event(
                connection,
                tenant_id=row["id"],
                action="admin.tenant.create",
                resource_type="tenant",
                resource_id=row["id"],
                before_state=dict(before) if before else None,
                after_state=dict(row),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"source": source, "initialized_settings": ["organization.profile"]},
            )

        return TenantRead.model_validate(dict(row))

    def onboard_tenant(
        self,
        slug: str,
        commercial_name: str,
        legal_name: str | None,
        plan_id: str | None,
        timezone: str,
        locale: str,
        source: dict,
        owner: dict,
        organization_profile: dict | None,
        modules: list[dict],
        idempotency_key: str,
        correlation_id: str,
    ) -> dict:
        tenant_id = f"ten_{uuid4().hex[:26]}"
        owner_user_id = f"usr_{uuid4().hex[:26]}"
        owner_role_id = f"rol_{uuid4().hex[:26]}"
        owner_membership_id = f"mem_{uuid4().hex[:26]}"
        profile = organization_profile or self.default_organization_profile(commercial_name, legal_name)
        owner_status = owner.get("status", "invited")
        branch_ids = owner.get("branch_ids") if isinstance(owner.get("branch_ids"), list) else ["*"]
        normalized_modules = modules or [{"module_code": "admin", "status": "active", "limits": {}, "source": "provisioning"}]

        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    from admin.tenants
                    where slug = lower(:slug)
                    """
                ),
                {"slug": slug},
            ).mappings().first()
            tenant_row = connection.execute(
                text(
                    """
                    insert into admin.tenants (
                        id,
                        slug,
                        legal_name,
                        commercial_name,
                        status,
                        plan_id,
                        timezone,
                        locale,
                        source_type,
                        source_id,
                        metadata
                    )
                    values (
                        :id,
                        lower(:slug),
                        :legal_name,
                        :commercial_name,
                        'active',
                        :plan_id,
                        :timezone,
                        :locale,
                        :source_type,
                        :source_id,
                        cast(:metadata as jsonb)
                    )
                    on conflict (slug)
                    do update set
                        legal_name = excluded.legal_name,
                        commercial_name = excluded.commercial_name,
                        status = 'active',
                        plan_id = excluded.plan_id,
                        timezone = excluded.timezone,
                        locale = excluded.locale,
                        source_type = excluded.source_type,
                        source_id = excluded.source_id,
                        metadata = excluded.metadata,
                        updated_at = now()
                    returning id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    """
                ),
                {
                    "id": tenant_id,
                    "slug": slug,
                    "legal_name": legal_name,
                    "commercial_name": commercial_name,
                    "plan_id": plan_id,
                    "timezone": timezone,
                    "locale": locale,
                    "source_type": source["type"],
                    "source_id": source["id"],
                    "metadata": json.dumps({"source": source}),
                },
            ).mappings().one()
            tenant_id = tenant_row["id"]

            setting_row = connection.execute(
                text(
                    """
                    insert into admin.tenant_settings (id, tenant_id, key, module_code, value)
                    values (:id, :tenant_id, 'organization.profile', 'admin', cast(:value as jsonb))
                    on conflict (tenant_id, key)
                    do update set
                        module_code = excluded.module_code,
                        value = case
                            when admin.tenant_settings.value = '{}'::jsonb then excluded.value
                            else admin.tenant_settings.value
                        end,
                        updated_at = now()
                    returning key, module_code, value
                    """
                ),
                {
                    "id": f"set_{uuid4().hex[:26]}",
                    "tenant_id": tenant_id,
                    "value": json.dumps(profile),
                },
            ).mappings().one()

            user_row = connection.execute(
                text(
                    """
                    insert into admin.users (id, email, display_name, status)
                    values (:id, lower(:email), :display_name, :status)
                    on conflict (email)
                    do update set
                        display_name = excluded.display_name,
                        status = case
                            when admin.users.status = 'disabled' then excluded.status
                            else admin.users.status
                        end,
                        updated_at = now()
                    returning id, email, display_name, status
                    """
                ),
                {
                    "id": owner_user_id,
                    "email": owner["email"],
                    "display_name": owner["display_name"],
                    "status": owner_status,
                },
            ).mappings().one()
            owner_user_id = user_row["id"]

            role_row = connection.execute(
                text(
                    """
                    insert into admin.roles (id, tenant_id, code, name, description, status, system_role)
                    values (:id, :tenant_id, 'owner', 'Owner', 'Owner inicial del tenant creado por provisioning.', 'active', true)
                    on conflict (tenant_id, code)
                    do update set
                        name = excluded.name,
                        description = excluded.description,
                        status = 'active',
                        system_role = true,
                        updated_at = now()
                    returning id, code, name, status
                    """
                ),
                {"id": owner_role_id, "tenant_id": tenant_id},
            ).mappings().one()
            owner_role_id = role_row["id"]

            membership_row = connection.execute(
                text(
                    """
                    insert into admin.memberships (
                        id,
                        tenant_id,
                        user_id,
                        status,
                        invited_at,
                        activated_at,
                        metadata
                    )
                    values (
                        :id,
                        :tenant_id,
                        :user_id,
                        cast(:status as varchar),
                        now(),
                        case when cast(:status as varchar) = 'active' then now() else null end,
                        cast(:metadata as jsonb)
                    )
                    on conflict (tenant_id, user_id)
                    do update set
                        status = excluded.status,
                        invited_at = coalesce(admin.memberships.invited_at, excluded.invited_at),
                        activated_at = case
                            when excluded.status = 'active' then coalesce(admin.memberships.activated_at, now())
                            else admin.memberships.activated_at
                        end,
                        disabled_at = null,
                        metadata = excluded.metadata,
                        updated_at = now()
                    returning id, status
                    """
                ),
                {
                    "id": owner_membership_id,
                    "tenant_id": tenant_id,
                    "user_id": owner_user_id,
                    "status": owner_status,
                    "metadata": json.dumps({"scope": {"branch_ids": branch_ids}, "source": source}),
                },
            ).mappings().one()

            self._replace_membership_roles(connection, tenant_id, membership_row["id"], [owner_role_id])

            entitlement_rows = []
            for module in normalized_modules:
                module_row = connection.execute(
                    text(
                        """
                        insert into admin.tenant_modules (id, tenant_id, module_code, status, source, limits, starts_at)
                        values (:id, :tenant_id, :module_code, :status, :source, cast(:limits as jsonb), now())
                        on conflict (tenant_id, module_code)
                        do update set
                            status = excluded.status,
                            source = excluded.source,
                            limits = excluded.limits,
                            starts_at = coalesce(admin.tenant_modules.starts_at, excluded.starts_at),
                            updated_at = now()
                        returning module_code,status,source,tenant_enabled,(status='active' and tenant_enabled) as effective_active,limits
                        """
                    ),
                    {
                        "id": f"tmo_{uuid4().hex[:26]}",
                        "tenant_id": tenant_id,
                        "module_code": module["module_code"],
                        "status": module.get("status", "active"),
                        "source": module.get("source", "provisioning"),
                        "limits": json.dumps(module.get("limits", {})),
                    },
                ).mappings().one()
                entitlement_rows.append(dict(module_row))

            connection.execute(
                text(
                    """
                    insert into admin.role_permissions (id, tenant_id, role_id, permission_id, scope)
                    select
                        'rpe_' || substr(md5(:tenant_id || ':' || :role_id || ':' || permissions.id), 1, 26),
                        :tenant_id,
                        :role_id,
                        permissions.id,
                        '{}'::jsonb
                    from admin.permissions permissions
                    where permissions.status = 'active'
                        and permissions.classification = 'tenant'
                        and permissions.assignable_to_tenant_role = true
                        and (
                            permissions.module_code = 'admin'
                            or exists (
                                select 1 from admin.tenant_modules tenant_modules
                                where tenant_modules.tenant_id = :tenant_id
                                    and tenant_modules.module_code = permissions.module_code
                                    and tenant_modules.status = 'active'
                                    and tenant_modules.tenant_enabled = true
                            )
                        )
                    on conflict (tenant_id, role_id, permission_id) do nothing
                    """
                ),
                {"tenant_id": tenant_id, "role_id": owner_role_id},
            )

            owner_read = self._get_user_for_tenant(connection, tenant_id, owner_user_id)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.tenant.onboard",
                resource_type="tenant",
                resource_id=tenant_id,
                before_state=dict(before) if before else None,
                after_state={
                    "tenant": dict(tenant_row),
                    "owner": dict(owner_read),
                    "modules": entitlement_rows,
                    "organization_setting": dict(setting_row),
                },
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"source": source, "owner_status": owner_status},
            )

        session_context = self.get_session_context(tenant_id, owner_user_id) if owner_status == "active" else None
        return {
            "tenant": TenantRead.model_validate(dict(tenant_row)),
            "owner": UserRead.model_validate(dict(owner_read)),
            "entitlements": [EntitlementRead.model_validate(item) for item in entitlement_rows],
            "organization": SettingRead.model_validate(dict(setting_row)),
            "session_context": session_context,
        }

    def list_entitlements(self, tenant_id: str) -> list[EntitlementRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select module_code,status,source,tenant_enabled,(status='active' and tenant_enabled) as effective_active,limits
                    from admin.tenant_modules
                    where tenant_id = :tenant_id
                    order by module_code
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().all()

        return [EntitlementRead.model_validate(dict(row)) for row in rows]

    def list_settings(self, tenant_id: str, module_code: str | None = None) -> list[SettingRead]:
        query = """
            select key, module_code, value
            from admin.tenant_settings
            where tenant_id = :tenant_id
            order by module_code nulls last, key
        """
        params = {"tenant_id": tenant_id}
        if module_code is not None:
            query = """
                select key, module_code, value
                from admin.tenant_settings
                where tenant_id = :tenant_id
                    and module_code = :module_code
                order by module_code nulls last, key
            """
            params["module_code"] = module_code

        with self.engine.connect() as connection:
            rows = connection.execute(
                text(query),
                params,
            ).mappings().all()

        return [SettingRead.model_validate(dict(row)) for row in rows]

    def upsert_setting(
        self,
        tenant_id: str,
        key: str,
        module_code: str | None,
        value: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> SettingRead | None:
        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select key, module_code, value
                    from admin.tenant_settings
                    where tenant_id = :tenant_id and key = :key
                    """
                ),
                {"tenant_id": tenant_id, "key": key},
            ).mappings().first()
            row = connection.execute(
                text(
                    """
                    insert into admin.tenant_settings (id, tenant_id, key, module_code, value)
                    values (:id, :tenant_id, :key, :module_code, cast(:value as jsonb))
                    on conflict (tenant_id, key)
                    do update set
                        module_code = excluded.module_code,
                        value = excluded.value,
                        updated_at = now()
                    returning key, module_code, value
                    """
                ),
                {
                    "id": f"set_{uuid4().hex[:26]}",
                    "tenant_id": tenant_id,
                    "key": key,
                    "module_code": module_code,
                    "value": json.dumps(value),
                },
            ).mappings().first()
            if row:
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action="admin.setting.upsert",
                    resource_type="tenant_setting",
                    resource_id=key,
                    before_state=dict(before) if before else None,
                    after_state=dict(row),
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"module_code": module_code},
                )

        return SettingRead.model_validate(dict(row)) if row else None

    def create_legal_entity(
        self,
        tenant_id: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        item = {key: value for key, value in payload.items() if value is not None}
        item["id"] = f"rso_{uuid4().hex[:18]}"
        item["status"] = "active"
        return self._append_organization_item(
            tenant_id=tenant_id,
            collection_key="legal_entities",
            item=item,
            action="admin.organization.legal_entity.create",
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def update_legal_entity(
        self,
        tenant_id: str,
        legal_entity_id: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        return self._update_organization_item(
            tenant_id=tenant_id,
            collection_key="legal_entities",
            item_id=legal_entity_id,
            patch={key: value for key, value in payload.items() if value is not None},
            action="admin.organization.legal_entity.update",
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def set_legal_entity_status(
        self,
        tenant_id: str,
        legal_entity_id: str,
        status: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        return self._update_organization_item(
            tenant_id=tenant_id,
            collection_key="legal_entities",
            item_id=legal_entity_id,
            patch={"status": status},
            action=f"admin.organization.legal_entity.{status}",
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def create_branch(
        self,
        tenant_id: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        item = {key: value for key, value in payload.items() if value is not None}
        item["id"] = f"suc_{uuid4().hex[:18]}"
        item["status"] = "active"
        return self._append_organization_item(
            tenant_id=tenant_id,
            collection_key="branches",
            item=item,
            action="admin.organization.branch.create",
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def update_branch(
        self,
        tenant_id: str,
        branch_id: str,
        payload: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        return self._update_organization_item(
            tenant_id=tenant_id,
            collection_key="branches",
            item_id=branch_id,
            patch={key: value for key, value in payload.items() if value is not None},
            action="admin.organization.branch.update",
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def set_branch_status(
        self,
        tenant_id: str,
        branch_id: str,
        status: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        return self._update_organization_item(
            tenant_id=tenant_id,
            collection_key="branches",
            item_id=branch_id,
            patch={"status": status},
            action=f"admin.organization.branch.{status}",
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
        )

    def get_session_context(self, tenant_id: str, actor_id: str) -> SessionContextRead | None:
        with self.engine.connect() as connection:
            tenant = connection.execute(
                text(
                    """
                    select id, slug, legal_name, commercial_name, status, plan_id, timezone, locale
                    from admin.tenants
                    where id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().first()
            if tenant is None:
                return None

            user = self._get_user_for_tenant(connection, tenant_id, actor_id)
            if user is None:
                return None

            membership = connection.execute(
                text(
                    """
                    select id, metadata
                    from admin.memberships
                    where tenant_id = :tenant_id
                        and user_id = :actor_id
                        and status = 'active'
                    """
                ),
                {"tenant_id": tenant_id, "actor_id": actor_id},
            ).mappings().first()
            if membership is None:
                return None

            roles = connection.execute(
                text(
                    """
                    select
                        roles.id,
                        roles.code,
                        roles.name,
                        roles.status,
                        roles.system_role,
                        roles.permission_revision,
                        coalesce(array_agg(permissions.code order by permissions.code) filter (where permissions.code is not null), '{}') as permissions,
                        coalesce(
                            jsonb_agg(
                                jsonb_build_object(
                                    'permission_id', permissions.id,
                                    'code', permissions.code,
                                    'scope', role_permissions.scope
                                ) order by permissions.code
                            ) filter (where permissions.id is not null),
                            '[]'::jsonb
                        ) as permission_assignments
                    from admin.membership_roles membership_roles
                    join admin.roles roles
                        on roles.tenant_id = membership_roles.tenant_id
                        and roles.id = membership_roles.role_id
                    left join admin.role_permissions role_permissions
                        on role_permissions.tenant_id = roles.tenant_id
                        and role_permissions.role_id = roles.id
                    left join admin.permissions permissions
                        on permissions.id = role_permissions.permission_id
                        and permissions.status = 'active'
                    where membership_roles.tenant_id = :tenant_id
                        and membership_roles.membership_id = :membership_id
                        and roles.status = 'active'
                    group by roles.id, roles.code, roles.name, roles.status, roles.system_role, roles.permission_revision
                    order by roles.code
                    """
                ),
                {"tenant_id": tenant_id, "membership_id": membership["id"]},
            ).mappings().all()

            entitlements = connection.execute(
                text(
                    """
                    select module_code,status,source,tenant_enabled,(status='active' and tenant_enabled) as effective_active,limits
                    from admin.tenant_modules
                    where tenant_id = :tenant_id
                    order by module_code
                    """
                ),
                {"tenant_id": tenant_id},
            ).mappings().all()

            permissions = connection.execute(
                text(
                    """
                    select distinct permissions.code
                    from admin.memberships memberships
                    join admin.membership_roles membership_roles
                        on membership_roles.tenant_id = memberships.tenant_id
                        and membership_roles.membership_id = memberships.id
                    join admin.roles roles
                        on roles.tenant_id = memberships.tenant_id
                        and roles.id = membership_roles.role_id
                    join admin.role_permissions role_permissions
                        on role_permissions.tenant_id = memberships.tenant_id
                        and role_permissions.role_id = roles.id
                    join admin.permissions permissions
                        on permissions.id = role_permissions.permission_id
                    where memberships.tenant_id = :tenant_id
                        and memberships.user_id = :actor_id
                        and memberships.status = 'active'
                        and roles.status = 'active'
                        and permissions.status = 'active'
                        and permissions.classification = 'tenant'
                        and permissions.assignable_to_tenant_role = true
                        and (
                            permissions.module_code = 'admin'
                            or exists (
                                select 1
                                from admin.tenant_modules permitted_modules
                                where permitted_modules.tenant_id = :tenant_id
                                    and permitted_modules.module_code = permissions.module_code
                                    and permitted_modules.status = 'active'
                                    and permitted_modules.tenant_enabled = true
                            )
                        )
                    order by permissions.code
                    """
                ),
                {"tenant_id": tenant_id, "actor_id": actor_id},
            ).scalars().all()

            organization_profile = self._get_or_create_organization_profile(connection, tenant_id)

        entitlement_reads = [EntitlementRead.model_validate(dict(row)) for row in entitlements]
        role_reads = [RoleRead.model_validate(dict(row)) for row in roles]
        scope = self._build_session_scope(membership["metadata"], organization_profile)
        return SessionContextRead(
            tenant=TenantRead.model_validate(dict(tenant)),
            user=UserRead.model_validate(dict(user)),
            roles=role_reads,
            entitlements=entitlement_reads,
            entitlement_limits={item.module_code: item.limits for item in entitlement_reads},
            permissions=list(permissions),
            active_modules=[item.module_code for item in entitlement_reads if item.effective_active],
            scope=scope,
        )

    def get_session_context_by_email(self, tenant_id: str, email: str) -> SessionContextRead | None:
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    select users.id, users.status as user_status, memberships.status as membership_status
                    from admin.memberships memberships
                    join admin.users users on users.id = memberships.user_id
                    where memberships.tenant_id = :tenant_id
                        and users.email = lower(:email)
                        and users.status in ('active', 'invited')
                        and memberships.status in ('active', 'invited')
                    """
                ),
                {"tenant_id": tenant_id, "email": email},
            ).mappings().first()
            if row and (row["user_status"] == "invited" or row["membership_status"] == "invited"):
                connection.execute(
                    text(
                        """
                        update admin.users
                        set status = 'active', updated_at = now()
                        where id = :user_id and status = 'invited'
                        """
                    ),
                    {"user_id": row["id"]},
                )
                connection.execute(
                    text(
                        """
                        update admin.memberships
                        set status = 'active', activated_at = now(), disabled_at = null, updated_at = now()
                        where tenant_id = :tenant_id and user_id = :user_id and status = 'invited'
                        """
                    ),
                    {"tenant_id": tenant_id, "user_id": row["id"]},
                )

        return self.get_session_context(tenant_id, row["id"]) if row else None

    def list_session_tenants_by_email(self, email: str) -> list[dict]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                text(
                    """
                    select
                        tenants.id,
                        tenants.slug,
                        tenants.legal_name,
                        tenants.commercial_name,
                        tenants.status,
                        tenants.plan_id,
                        tenants.timezone,
                        tenants.locale,
                        users.status as user_status,
                        memberships.status as membership_status,
                        coalesce(
                            jsonb_agg(distinct roles.code) filter (where roles.code is not null),
                            '[]'::jsonb
                        ) as role_codes
                    from admin.memberships memberships
                    join admin.users users on users.id = memberships.user_id
                    join admin.tenants tenants on tenants.id = memberships.tenant_id
                    left join admin.membership_roles membership_roles
                        on membership_roles.tenant_id = memberships.tenant_id
                        and membership_roles.membership_id = memberships.id
                    left join admin.roles roles
                        on roles.tenant_id = memberships.tenant_id
                        and roles.id = membership_roles.role_id
                        and roles.status = 'active'
                    where users.email = lower(:email)
                        and users.status in ('active', 'invited')
                        and memberships.status in ('active', 'invited')
                        and tenants.status in ('active', 'provisioning')
                    group by
                        tenants.id,
                        tenants.slug,
                        tenants.legal_name,
                        tenants.commercial_name,
                        tenants.status,
                        tenants.plan_id,
                        tenants.timezone,
                        tenants.locale,
                        users.status,
                        memberships.status
                    order by tenants.created_at desc, tenants.commercial_name
                    """
                ),
                {"email": email},
            ).mappings().all()

        tenants = []
        for row in rows:
            tenant = TenantRead.model_validate(
                {
                    "id": row["id"],
                    "slug": row["slug"],
                    "legal_name": row["legal_name"],
                    "commercial_name": row["commercial_name"],
                    "status": row["status"],
                    "plan_id": row["plan_id"],
                    "timezone": row["timezone"],
                    "locale": row["locale"],
                }
            )
            tenants.append(
                {
                    "tenant": tenant,
                    "user_status": row["user_status"],
                    "membership_status": row["membership_status"],
                    "roles": list(row["role_codes"] or []),
                }
            )
        return tenants

    def update_entitlement_preference(
        self,
        tenant_id: str,
        module_code: str,
        enabled: bool,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ) -> EntitlementRead | None:
        operation = f"admin.entitlement.preference.update:{module_code}"
        request_hash = self._command_request_hash({"tenant_id": tenant_id, "module_code": module_code, "enabled": enabled})
        with self.engine.begin() as connection:
            entitlement_rows = self._lock_module_entitlements(connection, tenant_id)
            before = next((row for row in entitlement_rows if row["module_code"] == module_code), None)
            if before is None:
                return None
            replay = self._begin_idempotent_command(connection, tenant_id, operation, idempotency_key, request_hash)
            if replay is not None:
                return EntitlementRead.model_validate(replay)
            if before["status"] != "active":
                raise ValueError("module_not_contracted")
            self._validate_module_transition(entitlement_rows, module_code, enabled)
            row = connection.execute(
                text(
                    """
                    update admin.tenant_modules
                    set tenant_enabled=:enabled,updated_at=now()
                    where tenant_id=:tenant_id and module_code=:module_code
                    returning module_code,status,source,tenant_enabled,(status='active' and tenant_enabled) as effective_active,limits
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "module_code": module_code,
                    "enabled": enabled,
                },
            ).mappings().one()
            result = dict(row)
            if result != dict(before):
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action=operation,
                    resource_type="tenant_module",
                    resource_id=module_code,
                    before_state=dict(before),
                    after_state=result,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"tenant_enabled": enabled},
                    actor_user_id=self._actor_user_id(connection, actor_email),
                )
            self._complete_idempotent_command(connection, tenant_id, operation, idempotency_key, result, 200)

        return EntitlementRead.model_validate(result)

    def list_users(self, tenant_id: str, limit: int = 50) -> list[UserRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select
                        users.id,
                        users.email,
                        users.display_name,
                        memberships.status,
                        coalesce(array_agg(roles.code order by roles.code) filter (where roles.code is not null), '{}') as roles
                    from admin.memberships memberships
                    join admin.users users on users.id = memberships.user_id
                    left join admin.membership_roles membership_roles
                        on membership_roles.tenant_id = memberships.tenant_id
                        and membership_roles.membership_id = memberships.id
                    left join admin.roles roles on roles.id = membership_roles.role_id
                    where memberships.tenant_id = :tenant_id
                    group by users.id, users.email, users.display_name, memberships.status
                    order by users.email
                    limit :limit
                    """
                ),
                {"tenant_id": tenant_id, "limit": limit},
            ).mappings().all()

        return [UserRead.model_validate(dict(row)) for row in rows]

    def get_user_for_tenant(self, tenant_id: str, user_id: str) -> UserRead | None:
        with self.engine.connect() as connection:
            row = self._get_user_for_tenant(connection, tenant_id, user_id)

        return UserRead.model_validate(dict(row)) if row else None

    def invite_user(
        self,
        tenant_id: str,
        email: str,
        display_name: str,
        role_ids: list[str],
        idempotency_key: str,
        correlation_id: str,
    ) -> UserRead:
        user_id = f"usr_{uuid4().hex[:26]}"
        membership_id = f"mem_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select users.id, users.email, users.display_name, memberships.status
                    from admin.users users
                    left join admin.memberships memberships
                        on memberships.user_id = users.id and memberships.tenant_id = :tenant_id
                    where users.email = lower(:email)
                    """
                ),
                {"tenant_id": tenant_id, "email": email},
            ).mappings().first()
            user_row = connection.execute(
                text(
                    """
                    insert into admin.users (id, email, display_name, status)
                    values (:user_id, lower(:email), :display_name, 'invited')
                    on conflict (email)
                    do update set
                        display_name = excluded.display_name,
                        status = case
                            when admin.users.status = 'disabled' then 'invited'
                            else admin.users.status
                        end,
                        updated_at = now()
                    returning id
                    """
                ),
                {"user_id": user_id, "email": email, "display_name": display_name},
            ).mappings().one()
            user_id = user_row["id"]

            membership_row = connection.execute(
                text(
                    """
                    insert into admin.memberships (id, tenant_id, user_id, status, invited_at)
                    values (:membership_id, :tenant_id, :user_id, 'invited', now())
                    on conflict (tenant_id, user_id)
                    do update set
                        status = 'invited',
                        invited_at = coalesce(admin.memberships.invited_at, now()),
                        disabled_at = null,
                        updated_at = now()
                    returning id
                    """
                ),
                {"membership_id": membership_id, "tenant_id": tenant_id, "user_id": user_id},
            ).mappings().one()

            self._replace_membership_roles(connection, tenant_id, membership_row["id"], role_ids)
            row = self._get_user_for_tenant(connection, tenant_id, user_id)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.user.invite",
                resource_type="user",
                resource_id=user_id,
                before_state=dict(before) if before else None,
                after_state=dict(row),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"role_ids": role_ids},
            )

        return UserRead.model_validate(dict(row))

    def update_user(
        self,
        tenant_id: str,
        user_id: str,
        display_name: str | None,
        role_ids: list[str] | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> UserRead | None:
        with self.engine.begin() as connection:
            before = self._get_user_for_tenant(connection, tenant_id, user_id)
            membership_id = connection.execute(
                text(
                    """
                    select id
                    from admin.memberships
                    where tenant_id = :tenant_id and user_id = :user_id
                    """
                ),
                {"tenant_id": tenant_id, "user_id": user_id},
            ).scalar_one_or_none()
            if membership_id is None:
                return None

            if display_name is not None:
                connection.execute(
                    text(
                        """
                        update admin.users
                        set display_name = :display_name, updated_at = now()
                        where id = :user_id
                        """
                    ),
                    {"display_name": display_name, "user_id": user_id},
                )
            if role_ids is not None:
                self._replace_membership_roles(connection, tenant_id, membership_id, role_ids)

            row = self._get_user_for_tenant(connection, tenant_id, user_id)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.user.update",
                resource_type="user",
                resource_id=user_id,
                before_state=dict(before) if before else None,
                after_state=dict(row),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"role_ids_changed": role_ids is not None},
            )

        return UserRead.model_validate(dict(row)) if row else None

    def disable_user(
        self,
        tenant_id: str,
        user_id: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> UserRead | None:
        with self.engine.begin() as connection:
            before = self._get_user_for_tenant(connection, tenant_id, user_id)
            result = connection.execute(
                text(
                    """
                    update admin.memberships
                    set status = 'disabled',
                        disabled_at = now(),
                        updated_at = now()
                    where tenant_id = :tenant_id and user_id = :user_id
                    """
                ),
                {"tenant_id": tenant_id, "user_id": user_id},
            )
            if result.rowcount == 0:
                return None
            row = self._get_user_for_tenant(connection, tenant_id, user_id)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.user.disable",
                resource_type="user",
                resource_id=user_id,
                before_state=dict(before) if before else None,
                after_state=dict(row),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={},
            )

        return UserRead.model_validate(dict(row)) if row else None

    def delete_user(
        self,
        tenant_id: str,
        user_id: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> UserRead | None:
        with self.engine.begin() as connection:
            before = self._get_user_for_tenant(connection, tenant_id, user_id)
            if before is None:
                return None

            membership_id = connection.execute(
                text(
                    """
                    select id
                    from admin.memberships
                    where tenant_id = :tenant_id and user_id = :user_id
                    """
                ),
                {"tenant_id": tenant_id, "user_id": user_id},
            ).scalar_one_or_none()
            if membership_id is None:
                return None

            connection.execute(
                text(
                    """
                    delete from admin.membership_roles
                    where tenant_id = :tenant_id and membership_id = :membership_id
                    """
                ),
                {"tenant_id": tenant_id, "membership_id": membership_id},
            )
            connection.execute(
                text(
                    """
                    delete from admin.memberships
                    where tenant_id = :tenant_id and id = :membership_id
                    """
                ),
                {"tenant_id": tenant_id, "membership_id": membership_id},
            )

            remaining_memberships = connection.execute(
                text("select count(*) from admin.memberships where user_id = :user_id"),
                {"user_id": user_id},
            ).scalar_one()

            after_state = dict(before)
            after_state["status"] = "deleted"
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.user.delete",
                resource_type="user",
                resource_id=user_id,
                before_state=dict(before),
                after_state=after_state,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"removed_global_user": remaining_memberships == 0},
            )
            if remaining_memberships == 0:
                connection.execute(text("delete from admin.users where id = :user_id"), {"user_id": user_id})

        deleted = dict(before)
        deleted["status"] = "deleted"
        return UserRead.model_validate(deleted)

    def _record_audit_event(
        self,
        connection,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        before_state: dict | None,
        after_state: dict | None,
        idempotency_key: str,
        correlation_id: str,
        metadata: dict,
        actor_user_id: str | None = None,
    ) -> None:
        connection.execute(
            text(
                """
                insert into admin.audit_events (
                    id,
                    tenant_id,
                    actor_user_id,
                    actor_type,
                    action,
                    resource_type,
                    resource_id,
                    source_service,
                    correlation_id,
                    idempotency_key,
                    before_state,
                    after_state,
                    metadata
                )
                values (
                    :id,
                    :tenant_id,
                    cast(:actor_user_id as varchar),
                    case when cast(:actor_user_id as varchar) is null then 'system' else 'user' end,
                    :action,
                    :resource_type,
                    :resource_id,
                    'admin-service',
                    :correlation_id,
                    :idempotency_key,
                    cast(:before_state as jsonb),
                    cast(:after_state as jsonb),
                    cast(:metadata as jsonb)
                )
                """
            ),
            {
                "id": f"aud_{uuid4().hex[:26]}",
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "correlation_id": correlation_id,
                "idempotency_key": idempotency_key,
                "before_state": json.dumps(before_state, default=str) if before_state is not None else None,
                "after_state": json.dumps(after_state, default=str) if after_state is not None else None,
                "metadata": json.dumps(metadata, default=str),
            },
        )

    def _append_organization_item(
        self,
        tenant_id: str,
        collection_key: str,
        item: dict,
        action: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        with self.engine.begin() as connection:
            profile = self._get_or_create_organization_profile(connection, tenant_id)
            if profile is None:
                return None
            before_state = json.loads(json.dumps(profile))
            profile[collection_key] = [item, *profile.get(collection_key, [])]
            self._write_organization_profile(connection, tenant_id, profile)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action=action,
                resource_type=self._organization_resource_type(collection_key),
                resource_id=item["id"],
                before_state=None,
                after_state=item,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={"setting": "organization.profile", "collection": collection_key, "before_count": len(before_state.get(collection_key, []))},
            )
        return item

    def _update_organization_item(
        self,
        tenant_id: str,
        collection_key: str,
        item_id: str,
        patch: dict,
        action: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> dict | None:
        with self.engine.begin() as connection:
            profile = self._get_or_create_organization_profile(connection, tenant_id)
            if profile is None:
                return None
            items = profile.get(collection_key, [])
            for index, current in enumerate(items):
                if current.get("id") != item_id:
                    continue
                before = dict(current)
                updated = {**current, **patch}
                items[index] = updated
                profile[collection_key] = items
                self._write_organization_profile(connection, tenant_id, profile)
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action=action,
                    resource_type=self._organization_resource_type(collection_key),
                    resource_id=item_id,
                    before_state=before,
                    after_state=updated,
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"setting": "organization.profile", "collection": collection_key},
                )
                return updated
        return None

    def _organization_resource_type(self, collection_key: str) -> str:
        if collection_key == "legal_entities":
            return "legal_entity"
        if collection_key == "branches":
            return "branch"
        return "organization_item"

    def _get_or_create_organization_profile(self, connection, tenant_id: str) -> dict | None:
        row = connection.execute(
            text(
                """
                select key, module_code, value
                from admin.tenant_settings
                where tenant_id = :tenant_id and key = 'organization.profile'
                for update
                """
            ),
            {"tenant_id": tenant_id},
        ).mappings().first()
        if row:
            return self._normalize_organization_profile(row["value"])

        tenant = connection.execute(
            text(
                """
                select commercial_name, legal_name
                from admin.tenants
                where id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id},
        ).mappings().first()
        if tenant is None:
            return None

        profile = self.default_organization_profile(tenant["commercial_name"], tenant["legal_name"])
        connection.execute(
            text(
                """
                insert into admin.tenant_settings (id, tenant_id, key, module_code, value)
                values (:id, :tenant_id, 'organization.profile', 'admin', cast(:value as jsonb))
                on conflict (tenant_id, key) do nothing
                """
            ),
            {
                "id": f"set_{uuid4().hex[:26]}",
                "tenant_id": tenant_id,
                "value": json.dumps(profile),
            },
        )
        return profile

    def _write_organization_profile(self, connection, tenant_id: str, profile: dict) -> None:
        connection.execute(
            text(
                """
                update admin.tenant_settings
                set value = cast(:value as jsonb), module_code = 'admin', updated_at = now()
                where tenant_id = :tenant_id and key = 'organization.profile'
                """
            ),
            {"tenant_id": tenant_id, "value": json.dumps(profile)},
        )

    def _normalize_organization_profile(self, profile: dict | None) -> dict:
        profile = profile if isinstance(profile, dict) else {}
        corporate = profile.get("corporate") if isinstance(profile.get("corporate"), dict) else {}
        legal_entities = profile.get("legal_entities") if isinstance(profile.get("legal_entities"), list) else []
        branches = profile.get("branches") if isinstance(profile.get("branches"), list) else []
        return {
            "corporate": corporate,
            "legal_entities": [item for item in legal_entities if isinstance(item, dict)],
            "branches": [item for item in branches if isinstance(item, dict)],
        }

    def _build_session_scope(self, membership_metadata: dict | None, organization_profile: dict | None) -> SessionScopeRead:
        metadata = membership_metadata if isinstance(membership_metadata, dict) else {}
        scope_metadata = metadata.get("scope") if isinstance(metadata.get("scope"), dict) else metadata
        configured_branch_ids = scope_metadata.get("branch_ids")
        if not isinstance(configured_branch_ids, list):
            configured_branch_ids = scope_metadata.get("branches")
        branch_ids = [str(item) for item in configured_branch_ids if item] if isinstance(configured_branch_ids, list) else []

        profile = self._normalize_organization_profile(organization_profile)
        active_branches = [
            branch
            for branch in profile["branches"]
            if branch.get("status", "active") == "active" and branch.get("id") and branch.get("name")
        ]
        all_branches = not branch_ids or "*" in branch_ids
        allowed_branch_ids = {item for item in branch_ids if item != "*"}
        visible_branches = active_branches if all_branches else [branch for branch in active_branches if branch.get("id") in allowed_branch_ids]

        if not visible_branches:
            corporate = profile.get("corporate", {})
            visible_branches = [
                {
                    "id": "default",
                    "name": "Matriz",
                    "code": corporate.get("commercial_name", ""),
                    "status": "active",
                    "legal_entity_id": None,
                }
            ]

        branches = [
            SessionBranchRead(
                id=str(branch["id"]),
                name=str(branch["name"]),
                code=branch.get("code") or "",
                status=branch.get("status", "active"),
                legal_entity_id=branch.get("legal_entity_id"),
            )
            for branch in visible_branches
        ]
        return SessionScopeRead(
            branch_ids=[branch.id for branch in branches],
            branches=branches,
            all_branches=all_branches,
        )

    def _replace_membership_roles(self, connection, tenant_id: str, membership_id: str, role_ids: list[str]) -> None:
        connection.execute(
            text(
                """
                delete from admin.membership_roles
                where tenant_id = :tenant_id and membership_id = :membership_id
                """
            ),
            {"tenant_id": tenant_id, "membership_id": membership_id},
        )
        for role_id in role_ids:
            connection.execute(
                text(
                    """
                    insert into admin.membership_roles (id, tenant_id, membership_id, role_id)
                    select
                        cast(:id as varchar),
                        cast(:tenant_id as varchar),
                        cast(:membership_id as varchar),
                        roles.id
                    from admin.roles roles
                    where roles.tenant_id = :tenant_id and roles.id = :role_id
                    on conflict (tenant_id, membership_id, role_id) do nothing
                    """
                ),
                {
                    "id": f"mro_{uuid4().hex[:26]}",
                    "tenant_id": tenant_id,
                    "membership_id": membership_id,
                    "role_id": role_id,
                },
            )

    def _get_user_for_tenant(self, connection, tenant_id: str, user_id: str):
        return connection.execute(
            text(
                """
                select
                    users.id,
                    users.email,
                    users.display_name,
                    memberships.status,
                    coalesce(array_agg(roles.code order by roles.code) filter (where roles.code is not null), '{}') as roles
                from admin.memberships memberships
                join admin.users users on users.id = memberships.user_id
                left join admin.membership_roles membership_roles
                    on membership_roles.tenant_id = memberships.tenant_id
                    and membership_roles.membership_id = memberships.id
                left join admin.roles roles on roles.id = membership_roles.role_id
                where memberships.tenant_id = :tenant_id and users.id = :user_id
                group by users.id, users.email, users.display_name, memberships.status
                """
            ),
            {"tenant_id": tenant_id, "user_id": user_id},
        ).mappings().first()

    def list_roles(self, tenant_id: str, limit: int = 50) -> list[RoleRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select
                        roles.id,
                        roles.code,
                        roles.name,
                        roles.status,
                        roles.system_role,
                        roles.permission_revision,
                        coalesce(array_agg(permissions.code order by permissions.code) filter (where permissions.code is not null), '{}') as permissions,
                        coalesce(
                            jsonb_agg(
                                jsonb_build_object(
                                    'permission_id', permissions.id,
                                    'code', permissions.code,
                                    'scope', role_permissions.scope
                                ) order by permissions.code
                            ) filter (where permissions.id is not null),
                            '[]'::jsonb
                        ) as permission_assignments
                    from admin.roles roles
                    left join admin.role_permissions role_permissions
                        on role_permissions.tenant_id = roles.tenant_id
                        and role_permissions.role_id = roles.id
                    left join admin.permissions permissions
                        on permissions.id = role_permissions.permission_id
                    where roles.tenant_id = :tenant_id
                    group by roles.id, roles.code, roles.name, roles.status, roles.system_role, roles.permission_revision
                    order by roles.code
                    limit :limit
                    """
                ),
                {"tenant_id": tenant_id, "limit": limit},
            ).mappings().all()

        return [RoleRead.model_validate(dict(row)) for row in rows]

    def list_permissions(self, tenant_id: str, limit: int = 200) -> list[PermissionRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select
                        permissions.id,
                        permissions.code,
                        permissions.module_code,
                        permissions.resource,
                        permissions.action,
                        permissions.status,
                        permissions.display_name_es,
                        permissions.display_name_en,
                        permissions.description_es,
                        permissions.description_en,
                        permissions.classification,
                        permissions.assignable_to_tenant_role,
                        permissions.risk_level,
                        permissions.sort_order,
                        tenant_modules.status as entitlement_status,
                        case
                            when permissions.module_code = 'admin' then true
                            when tenant_modules.status = 'active' and tenant_modules.tenant_enabled = true then true
                            else false
                        end as available
                    from admin.permissions permissions
                    left join admin.tenant_modules tenant_modules
                        on tenant_modules.tenant_id = :tenant_id
                        and tenant_modules.module_code = permissions.module_code
                    where permissions.status = 'active'
                        and permissions.classification = 'tenant'
                        and permissions.assignable_to_tenant_role = true
                    order by permissions.sort_order, permissions.module_code, permissions.resource, permissions.action, permissions.code
                    limit :limit
                    """
                ),
                {"tenant_id": tenant_id, "limit": limit},
            ).mappings().all()

        return [PermissionRead.model_validate(dict(row)) for row in rows]

    def get_role(self, tenant_id: str, role_id: str) -> RoleRead | None:
        with self.engine.connect() as connection:
            row = self._get_role(connection, tenant_id, role_id)
        return RoleRead.model_validate(dict(row)) if row else None

    def create_role(
        self,
        tenant_id: str,
        code: str,
        name: str,
        description: str | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> RoleRead | None:
        role_id = f"rol_{uuid4().hex[:26]}"
        with self.engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    insert into admin.roles (id, tenant_id, code, name, description, status, system_role)
                    values (:id, :tenant_id, lower(:code), :name, :description, 'active', false)
                    on conflict (tenant_id, code) do nothing
                    returning id
                    """
                ),
                {
                    "id": role_id,
                    "tenant_id": tenant_id,
                    "code": code,
                    "name": name,
                    "description": description,
                },
            ).mappings().first()
            if row is None:
                return None
            role = self._get_role(connection, tenant_id, row["id"])
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.role.create",
                resource_type="role",
                resource_id=row["id"],
                before_state=None,
                after_state=dict(role),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={},
            )

        return RoleRead.model_validate(dict(role))

    def update_role(
        self,
        tenant_id: str,
        role_id: str,
        name: str | None,
        description: str | None,
        status: str | None,
        idempotency_key: str,
        correlation_id: str,
    ) -> RoleRead | None:
        with self.engine.begin() as connection:
            before = self._get_role(connection, tenant_id, role_id)
            if before is None:
                return None
            if before["system_role"] and status == "inactive":
                raise RolePermissionForbiddenError("system_role_cannot_be_inactivated")
            row = connection.execute(
                text(
                    """
                    update admin.roles
                    set
                        name = coalesce(:name, name),
                        description = coalesce(:description, description),
                        status = coalesce(:status, status),
                        updated_at = now()
                    where tenant_id = :tenant_id and id = :role_id
                    returning id
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "role_id": role_id,
                    "name": name,
                    "description": description,
                    "status": status,
                },
            ).mappings().first()
            if row is None:
                return None
            role = self._get_role(connection, tenant_id, role_id)
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.role.update",
                resource_type="role",
                resource_id=role_id,
                before_state=dict(before),
                after_state=dict(role),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={},
            )

        return RoleRead.model_validate(dict(role))

    def replace_role_permissions(
        self,
        tenant_id: str,
        role_id: str,
        assignments: list[dict],
        expected_revision: int,
        idempotency_key: str,
        correlation_id: str,
        actor_email: str | None = None,
    ) -> RoleRead | None:
        normalized = sorted(
            [
                {"permission_id": assignment["permission_id"], "scope": assignment.get("scope") or {}}
                for assignment in assignments
            ],
            key=lambda item: item["permission_id"],
        )
        permission_ids = [item["permission_id"] for item in normalized]
        if len(permission_ids) != len(set(permission_ids)):
            raise RolePermissionValidationError("duplicate_permission")
        operation = f"admin.role.permissions.replace:{role_id}"
        request_hash = hashlib.sha256(
            json.dumps(
                {"role_id": role_id, "assignments": normalized, "expected_revision": expected_revision},
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

        with self.engine.begin() as connection:
            connection.execute(
                text("select pg_advisory_xact_lock(hashtextextended(:lock_key, 0))"),
                {"lock_key": f"{tenant_id}:{operation}:{idempotency_key}"},
            )
            existing_command = connection.execute(
                text(
                    """
                    select request_hash, response_payload
                    from admin.command_idempotency
                    where tenant_id = :tenant_id
                        and operation = :operation
                        and idempotency_key = :idempotency_key
                    """
                ),
                {"tenant_id": tenant_id, "operation": operation, "idempotency_key": idempotency_key},
            ).mappings().first()
            if existing_command:
                if existing_command["request_hash"] != request_hash:
                    raise IdempotencyConflictError("idempotency_key_reused")
                if existing_command["response_payload"] is not None:
                    return RoleRead.model_validate(existing_command["response_payload"])
                raise RolePermissionConflictError("command_in_progress")

            before = self._get_role(connection, tenant_id, role_id, for_update=True)
            if before is None:
                return None
            if before["permission_revision"] != expected_revision:
                raise RolePermissionConflictError("permission_revision_conflict")

            connection.execute(
                text(
                    """
                    insert into admin.command_idempotency (
                        id, tenant_id, operation, idempotency_key, request_hash
                    ) values (:id, :tenant_id, :operation, :idempotency_key, :request_hash)
                    """
                ),
                {
                    "id": f"cmd_{uuid4().hex[:26]}",
                    "tenant_id": tenant_id,
                    "operation": operation,
                    "idempotency_key": idempotency_key,
                    "request_hash": request_hash,
                },
            )

            current_rows = connection.execute(
                text(
                    """
                    select
                        role_permissions.permission_id,
                        role_permissions.scope,
                        permissions.code,
                        permissions.module_code,
                        permissions.status,
                        permissions.classification,
                        permissions.assignable_to_tenant_role,
                        tenant_modules.status as entitlement_status
                    from admin.role_permissions role_permissions
                    join admin.permissions permissions on permissions.id = role_permissions.permission_id
                    left join admin.tenant_modules tenant_modules
                        on tenant_modules.tenant_id = role_permissions.tenant_id
                        and tenant_modules.module_code = permissions.module_code
                    where role_permissions.tenant_id = :tenant_id and role_permissions.role_id = :role_id
                    """
                ),
                {"tenant_id": tenant_id, "role_id": role_id},
            ).mappings().all()
            current = {row["permission_id"]: dict(row) for row in current_rows}

            permission_rows = []
            if permission_ids:
                permission_rows = connection.execute(
                    text(
                        """
                        select id, code, module_code, status, classification, assignable_to_tenant_role
                        from admin.permissions
                        where id = any(:permission_ids)
                        """
                    ),
                    {"permission_ids": permission_ids},
                ).mappings().all()
            requested_permissions = {row["id"]: dict(row) for row in permission_rows}
            if len(requested_permissions) != len(permission_ids):
                raise RolePermissionValidationError("permission_not_found")

            requested = {item["permission_id"]: item for item in normalized}
            added_ids = set(requested) - set(current)
            removal_candidates = set(current) - set(requested)
            protected_removal_ids = {
                permission_id
                for permission_id in removal_candidates
                if (
                    current[permission_id]["status"] != "active"
                    or current[permission_id]["classification"] != "tenant"
                    or not current[permission_id]["assignable_to_tenant_role"]
                    or (
                        current[permission_id]["module_code"] != "admin"
                        and current[permission_id]["entitlement_status"] != "active"
                    )
                )
            }
            removed_ids = removal_candidates - protected_removal_ids
            scope_changed_ids = {
                permission_id
                for permission_id in set(requested) & set(current)
                if requested[permission_id]["scope"] != (current[permission_id]["scope"] or {})
            }
            for permission_id in added_ids:
                permission = requested_permissions[permission_id]
                if (
                    permission["status"] != "active"
                    or permission["classification"] != "tenant"
                    or not permission["assignable_to_tenant_role"]
                ):
                    raise RolePermissionForbiddenError("permission_not_assignable")
            if scope_changed_ids or any(requested[permission_id]["scope"] for permission_id in added_ids):
                raise RolePermissionValidationError("scope_change_not_supported")

            added_modules = {
                requested_permissions[permission_id]["module_code"]
                for permission_id in added_ids
                if requested_permissions[permission_id]["module_code"] != "admin"
            }
            active_modules: set[str] = set()
            if added_modules:
                active_modules = set(
                    connection.execute(
                        text(
                            """
                            select module_code
                            from admin.tenant_modules
                            where tenant_id = :tenant_id
                                and module_code = any(:module_codes)
                                and status = 'active'
                                and tenant_enabled = true
                            """
                        ),
                        {"tenant_id": tenant_id, "module_codes": list(added_modules)},
                    ).scalars().all()
                )
            if added_modules - active_modules:
                raise RolePermissionForbiddenError("module_not_active")

            requested_codes = {permission["code"] for permission in requested_permissions.values()}
            if before["system_role"] and before["code"] == "owner":
                missing_floor = OWNER_PERMISSION_FLOOR - requested_codes
                if missing_floor:
                    raise RolePermissionForbiddenError("owner_permission_floor_required")

            if not added_ids and not removed_ids and not scope_changed_ids:
                connection.execute(
                    text(
                        """
                        update admin.command_idempotency
                        set response_payload = cast(:response_payload as jsonb), status_code = 200, completed_at = now()
                        where tenant_id = :tenant_id
                            and operation = :operation
                            and idempotency_key = :idempotency_key
                        """
                    ),
                    {
                        "response_payload": json.dumps(dict(before), default=str),
                        "tenant_id": tenant_id,
                        "operation": operation,
                        "idempotency_key": idempotency_key,
                    },
                )
                return RoleRead.model_validate(dict(before))

            if removed_ids:
                connection.execute(
                    text(
                        """
                        delete from admin.role_permissions
                        where tenant_id = :tenant_id and role_id = :role_id
                            and permission_id = any(:permission_ids)
                        """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "role_id": role_id,
                        "permission_ids": list(removed_ids),
                    },
                )
            for permission_id in added_ids:
                connection.execute(
                    text(
                        """
                        insert into admin.role_permissions (id, tenant_id, role_id, permission_id, scope)
                        values (:id, :tenant_id, :role_id, :permission_id, cast(:scope as jsonb))
                        """
                    ),
                    {
                        "id": f"rpe_{uuid4().hex[:26]}",
                        "tenant_id": tenant_id,
                        "role_id": role_id,
                        "permission_id": permission_id,
                        "scope": json.dumps(requested[permission_id]["scope"]),
                    },
                )

            connection.execute(
                text(
                    """
                    update admin.roles
                    set permission_revision = permission_revision + 1, updated_at = now()
                    where tenant_id = :tenant_id and id = :role_id
                    """
                ),
                {"tenant_id": tenant_id, "role_id": role_id},
            )

            role = self._get_role(connection, tenant_id, role_id)
            actor_user_id = None
            if actor_email:
                actor_user_id = connection.execute(
                    text("select id from admin.users where email = lower(:email)"),
                    {"email": actor_email},
                ).scalar_one_or_none()
            self._record_audit_event(
                connection,
                tenant_id=tenant_id,
                action="admin.role.permissions.replace",
                resource_type="role",
                resource_id=role_id,
                before_state=dict(before),
                after_state=dict(role),
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                metadata={
                    "added": sorted(requested_permissions[item]["code"] for item in added_ids),
                    "removed": sorted(current[item]["code"] for item in removed_ids),
                    "scope_changed": [],
                    "preserved_unavailable": sorted(current[item]["code"] for item in protected_removal_ids),
                    "previous_revision": expected_revision,
                    "new_revision": role["permission_revision"],
                },
                actor_user_id=actor_user_id,
            )
            connection.execute(
                text(
                    """
                    update admin.command_idempotency
                    set response_payload = cast(:response_payload as jsonb), status_code = 200, completed_at = now()
                    where tenant_id = :tenant_id
                        and operation = :operation
                        and idempotency_key = :idempotency_key
                    """
                ),
                {
                    "response_payload": json.dumps(dict(role), default=str),
                    "tenant_id": tenant_id,
                    "operation": operation,
                    "idempotency_key": idempotency_key,
                },
            )

        return RoleRead.model_validate(dict(role))

    def _get_role(self, connection, tenant_id: str, role_id: str, for_update: bool = False):
        if for_update:
            locked = connection.execute(
                text("select id from admin.roles where tenant_id = :tenant_id and id = :role_id for update"),
                {"tenant_id": tenant_id, "role_id": role_id},
            ).scalar_one_or_none()
            if locked is None:
                return None
        return connection.execute(
            text(
                """
                select
                    roles.id,
                    roles.code,
                    roles.name,
                    roles.status,
                    roles.system_role,
                    roles.permission_revision,
                    coalesce(array_agg(permissions.code order by permissions.code) filter (where permissions.code is not null), '{}') as permissions,
                    coalesce(
                        jsonb_agg(
                            jsonb_build_object(
                                'permission_id', permissions.id,
                                'code', permissions.code,
                                'scope', role_permissions.scope
                            ) order by permissions.code
                        ) filter (where permissions.id is not null),
                        '[]'::jsonb
                    ) as permission_assignments
                from admin.roles roles
                left join admin.role_permissions role_permissions
                    on role_permissions.tenant_id = roles.tenant_id
                    and role_permissions.role_id = roles.id
                left join admin.permissions permissions
                    on permissions.id = role_permissions.permission_id
                where roles.tenant_id = :tenant_id and roles.id = :role_id
                group by roles.id, roles.code, roles.name, roles.status, roles.system_role, roles.permission_revision
                """
            ),
            {"tenant_id": tenant_id, "role_id": role_id},
        ).mappings().first()

    def evaluate_policy(self, tenant_id: str, actor_id: str, module: str, resource: str, action: str) -> PolicyDecision:
        permission_code = f"{module}.{resource}.{action}"
        with self.engine.connect() as connection:
            tenant_status = connection.execute(
                text("select status from admin.tenants where id = :tenant_id"),
                {"tenant_id": tenant_id},
            ).scalar_one_or_none()
            if tenant_status is None:
                return PolicyDecision(allowed=False, reason="tenant_not_found")
            if tenant_status != "active":
                return PolicyDecision(allowed=False, reason="tenant_not_active")

            module_status = connection.execute(
                text(
                    """
                    select status,tenant_enabled
                    from admin.tenant_modules
                    where tenant_id = :tenant_id and module_code = :module
                    """
                ),
                {"tenant_id": tenant_id, "module": module},
            ).mappings().first()
            if module_status is None or module_status["status"] != "active" or not module_status["tenant_enabled"]:
                return PolicyDecision(allowed=False, reason="module_not_active")

            rows = connection.execute(
                text(
                    """
                    select permissions.code
                    from admin.memberships memberships
                    join admin.membership_roles membership_roles
                        on membership_roles.tenant_id = memberships.tenant_id
                        and membership_roles.membership_id = memberships.id
                    join admin.role_permissions role_permissions
                        on role_permissions.tenant_id = memberships.tenant_id
                        and role_permissions.role_id = membership_roles.role_id
                    join admin.permissions permissions
                        on permissions.id = role_permissions.permission_id
                    where memberships.tenant_id = :tenant_id
                        and memberships.user_id = :actor_id
                        and memberships.status = 'active'
                        and permissions.status = 'active'
                        and permissions.code = :permission_code
                    order by permissions.code
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "actor_id": actor_id,
                    "permission_code": permission_code,
                },
            ).scalars().all()

        matched_permissions = list(rows)
        return PolicyDecision(
            allowed=bool(matched_permissions),
            reason="allowed" if matched_permissions else "permission_not_granted",
            matched_permissions=matched_permissions,
        )


_repository: AdminRepository | None = None


def get_admin_repository() -> AdminRepository:
    global _repository
    if _repository is None:
        _repository = AdminRepository(create_database_engine())
    return _repository
