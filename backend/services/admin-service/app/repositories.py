import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine

from .schemas import EntitlementRead, PermissionRead, PolicyDecision, RoleRead, TenantRead, UserRead


class AdminRepository:
    def __init__(self, engine: Engine):
        self.engine = engine

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
