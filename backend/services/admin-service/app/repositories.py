import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine

from .schemas import (
    EntitlementRead,
    PermissionRead,
    PolicyDecision,
    RoleRead,
    SessionContextRead,
    SettingRead,
    TenantRead,
    UserRead,
)


class AdminRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

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

    def list_entitlements(self, tenant_id: str) -> list[EntitlementRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select module_code, status, limits as limits
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

            entitlements = connection.execute(
                text(
                    """
                    select module_code, status, limits as limits
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
                    order by permissions.code
                    """
                ),
                {"tenant_id": tenant_id, "actor_id": actor_id},
            ).scalars().all()

        entitlement_reads = [EntitlementRead.model_validate(dict(row)) for row in entitlements]
        return SessionContextRead(
            tenant=TenantRead.model_validate(dict(tenant)),
            user=UserRead.model_validate(dict(user)),
            entitlements=entitlement_reads,
            permissions=list(permissions),
            active_modules=[item.module_code for item in entitlement_reads if item.status == "active"],
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

    def upsert_entitlement(
        self,
        tenant_id: str,
        module_code: str,
        status: str,
        limits: dict,
        source: str,
        idempotency_key: str,
        correlation_id: str,
    ) -> EntitlementRead | None:
        with self.engine.begin() as connection:
            before = connection.execute(
                text(
                    """
                    select module_code, status, limits
                    from admin.tenant_modules
                    where tenant_id = :tenant_id and module_code = :module_code
                    """
                ),
                {"tenant_id": tenant_id, "module_code": module_code},
            ).mappings().first()
            row = connection.execute(
                text(
                    """
                    insert into admin.tenant_modules (id, tenant_id, module_code, status, source, limits)
                    values (:id, :tenant_id, :module_code, :status, :source, cast(:limits as jsonb))
                    on conflict (tenant_id, module_code)
                    do update set
                        status = excluded.status,
                        source = excluded.source,
                        limits = excluded.limits,
                        updated_at = now()
                    returning module_code, status, limits
                    """
                ),
                {
                    "id": f"tmo_{uuid4().hex[:26]}",
                    "tenant_id": tenant_id,
                    "module_code": module_code,
                    "status": status,
                    "source": source,
                    "limits": json.dumps(limits),
                },
            ).mappings().first()
            if row:
                self._record_audit_event(
                    connection,
                    tenant_id=tenant_id,
                    action="admin.entitlement.upsert",
                    resource_type="tenant_module",
                    resource_id=module_code,
                    before_state=dict(before) if before else None,
                    after_state=dict(row),
                    idempotency_key=idempotency_key,
                    correlation_id=correlation_id,
                    metadata={"source": source},
                )

        return EntitlementRead.model_validate(dict(row)) if row else None

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
    ) -> None:
        connection.execute(
            text(
                """
                insert into admin.audit_events (
                    id,
                    tenant_id,
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
                    'system',
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
                        coalesce(array_agg(permissions.code order by permissions.code) filter (where permissions.code is not null), '{}') as permissions
                    from admin.roles roles
                    left join admin.role_permissions role_permissions
                        on role_permissions.tenant_id = roles.tenant_id
                        and role_permissions.role_id = roles.id
                    left join admin.permissions permissions
                        on permissions.id = role_permissions.permission_id
                    where roles.tenant_id = :tenant_id
                    group by roles.id, roles.code, roles.name, roles.status
                    order by roles.code
                    limit :limit
                    """
                ),
                {"tenant_id": tenant_id, "limit": limit},
            ).mappings().all()

        return [RoleRead.model_validate(dict(row)) for row in rows]

    def list_permissions(self, limit: int = 200) -> list[PermissionRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select id, code, module_code, resource, action, status
                    from admin.permissions
                    where status = 'active'
                    order by module_code, resource, action, code
                    limit :limit
                    """
                ),
                {"limit": limit},
            ).mappings().all()

        return [PermissionRead.model_validate(dict(row)) for row in rows]

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
        permission_ids: list[str],
        scope: dict,
        idempotency_key: str,
        correlation_id: str,
    ) -> RoleRead | None:
        with self.engine.begin() as connection:
            before = self._get_role(connection, tenant_id, role_id)
            if before is None:
                return None
            valid_permission_ids = connection.execute(
                text(
                    """
                    select id
                    from admin.permissions
                    where id = any(:permission_ids) and status = 'active'
                    """
                ),
                {"permission_ids": permission_ids},
            ).scalars().all()
            if len(valid_permission_ids) != len(set(permission_ids)):
                return None

            connection.execute(
                text(
                    """
                    delete from admin.role_permissions
                    where tenant_id = :tenant_id and role_id = :role_id
                    """
                ),
                {"tenant_id": tenant_id, "role_id": role_id},
            )
            for permission_id in permission_ids:
                connection.execute(
                    text(
                        """
                        insert into admin.role_permissions (id, tenant_id, role_id, permission_id, scope)
                        values (:id, :tenant_id, :role_id, :permission_id, cast(:scope as jsonb))
                        on conflict (tenant_id, role_id, permission_id) do nothing
                        """
                    ),
                    {
                        "id": f"rpe_{uuid4().hex[:26]}",
                        "tenant_id": tenant_id,
                        "role_id": role_id,
                        "permission_id": permission_id,
                        "scope": json.dumps(scope),
                    },
                )

            role = self._get_role(connection, tenant_id, role_id)
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
                metadata={"permission_ids": permission_ids},
            )

        return RoleRead.model_validate(dict(role))

    def _get_role(self, connection, tenant_id: str, role_id: str):
        return connection.execute(
            text(
                """
                select
                    roles.id,
                    roles.code,
                    roles.name,
                    roles.status,
                    coalesce(array_agg(permissions.code order by permissions.code) filter (where permissions.code is not null), '{}') as permissions
                from admin.roles roles
                left join admin.role_permissions role_permissions
                    on role_permissions.tenant_id = roles.tenant_id
                    and role_permissions.role_id = roles.id
                left join admin.permissions permissions
                    on permissions.id = role_permissions.permission_id
                where roles.tenant_id = :tenant_id and roles.id = :role_id
                group by roles.id, roles.code, roles.name, roles.status
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
                    select status
                    from admin.tenant_modules
                    where tenant_id = :tenant_id and module_code = :module
                    """
                ),
                {"tenant_id": tenant_id, "module": module},
            ).scalar_one_or_none()
            if module_status != "active":
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
