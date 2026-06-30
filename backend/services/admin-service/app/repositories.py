from sqlalchemy import text
from sqlalchemy.engine import Engine

from erclave_common.db import create_database_engine

from .schemas import EntitlementRead, PolicyDecision, RoleRead, TenantRead, UserRead


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

    def list_roles(self, tenant_id: str, limit: int = 50) -> list[RoleRead]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    select id, code, name, status
                    from admin.roles
                    where tenant_id = :tenant_id
                    order by code
                    limit :limit
                    """
                ),
                {"tenant_id": tenant_id, "limit": limit},
            ).mappings().all()

        return [RoleRead.model_validate(dict(row)) for row in rows]

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
