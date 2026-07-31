import os
from contextlib import nullcontext
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from app.repositories import (
    AdminRepository,
    IdempotencyConflictError,
    RolePermissionConflictError,
    RolePermissionForbiddenError,
)


class TransactionEngine:
    """Keep repository calls inside one rollback-only integration transaction."""

    def __init__(self, connection):
        self.connection = connection

    def begin(self):
        return nullcontext(self.connection)

    def connect(self):
        return nullcontext(self.connection)


@pytest.mark.skipif(not os.getenv("ERCLAVE_TEST_DATABASE_URL"), reason="local PostgreSQL integration URL not configured")
def test_role_permission_replace_is_tenant_safe_idempotent_and_revision_guarded():
    engine = create_engine(os.environ["ERCLAVE_TEST_DATABASE_URL"])
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            repository = AdminRepository(TransactionEngine(connection))
            suffix = uuid4().hex[:12]
            tenant = repository.create_tenant(
                slug=f"permission-editor-{suffix}",
                commercial_name="Permission editor integration",
                legal_name=None,
                plan_id=None,
                timezone="America/Mexico_City",
                locale="es-MX",
                source={"type": "test", "id": suffix},
                organization_profile=None,
                idempotency_key=f"tenant-{suffix}",
                correlation_id=f"test-{suffix}",
            )
            role = repository.create_role(
                tenant_id=tenant.id,
                code=f"tester-{suffix}",
                name="Tester",
                description=None,
                idempotency_key=f"role-{suffix}",
                correlation_id=f"test-{suffix}",
            )
            permission_rows = connection.execute(
                text(
                    """
                    select code, id
                    from admin.permissions
                    where code in (
                        'admin.role.permissions.manage',
                        'internal.policy.evaluate',
                        'production.order.read',
                        'sales.order.read'
                    )
                    """
                )
            ).mappings().all()
            permissions = {row["code"]: row["id"] for row in permission_rows}
            assert set(permissions) == {
                "admin.role.permissions.manage",
                "internal.policy.evaluate",
                "production.order.read",
                "sales.order.read",
            }

            connection.execute(
                text(
                    """
                    insert into admin.role_permissions (id, tenant_id, role_id, permission_id, scope)
                    values (:id, :tenant_id, :role_id, :permission_id, '{}'::jsonb)
                    """
                ),
                {
                    "id": f"rpe_{uuid4().hex[:26]}",
                    "tenant_id": tenant.id,
                    "role_id": role.id,
                    "permission_id": permissions["production.order.read"],
                },
            )

            assignments = [{"permission_id": permissions["admin.role.permissions.manage"], "scope": {}}]
            updated = repository.replace_role_permissions(
                tenant_id=tenant.id,
                role_id=role.id,
                assignments=assignments,
                expected_revision=1,
                idempotency_key=f"permissions-{suffix}",
                correlation_id=f"test-{suffix}",
            )
            assert updated is not None
            assert updated.permission_revision == 2
            assert updated.permissions == ["admin.role.permissions.manage", "production.order.read"]
            listed = {item.id: item for item in repository.list_roles(tenant.id)}[role.id]
            assert listed.permission_revision == 2
            assert {item.permission_id for item in listed.permission_assignments} == {
                permissions["admin.role.permissions.manage"],
                permissions["production.order.read"],
            }

            replay = repository.replace_role_permissions(
                tenant_id=tenant.id,
                role_id=role.id,
                assignments=assignments,
                expected_revision=1,
                idempotency_key=f"permissions-{suffix}",
                correlation_id=f"test-{suffix}",
            )
            assert replay == updated
            assert connection.execute(
                text(
                    """
                    select count(*)
                    from admin.command_idempotency
                    where tenant_id = :tenant_id and operation = :operation
                    """
                ),
                {"tenant_id": tenant.id, "operation": f"admin.role.permissions.replace:{role.id}"},
            ).scalar_one() == 1

            with pytest.raises(IdempotencyConflictError):
                repository.replace_role_permissions(
                    tenant_id=tenant.id,
                    role_id=role.id,
                    assignments=[],
                    expected_revision=1,
                    idempotency_key=f"permissions-{suffix}",
                    correlation_id=f"test-{suffix}",
                )

            with pytest.raises(RolePermissionConflictError):
                repository.replace_role_permissions(
                    tenant_id=tenant.id,
                    role_id=role.id,
                    assignments=assignments,
                    expected_revision=1,
                    idempotency_key=f"stale-{suffix}",
                    correlation_id=f"test-{suffix}",
                )

            for code in ("internal.policy.evaluate", "sales.order.read"):
                with pytest.raises(RolePermissionForbiddenError):
                    repository.replace_role_permissions(
                        tenant_id=tenant.id,
                        role_id=role.id,
                        assignments=assignments + [{"permission_id": permissions[code], "scope": {}}],
                        expected_revision=2,
                        idempotency_key=f"forbidden-{code}-{suffix}",
                        correlation_id=f"test-{suffix}",
                    )

            assert repository.replace_role_permissions(
                tenant_id=f"ten_other_{suffix}",
                role_id=role.id,
                assignments=assignments,
                expected_revision=2,
                idempotency_key=f"other-{suffix}",
                correlation_id=f"test-{suffix}",
            ) is None

            owner = repository.create_role(
                tenant_id=tenant.id,
                code="owner",
                name="Owner",
                description=None,
                idempotency_key=f"owner-{suffix}",
                correlation_id=f"test-{suffix}",
            )
            connection.execute(
                text("update admin.roles set system_role = true where tenant_id = :tenant_id and id = :role_id"),
                {"tenant_id": tenant.id, "role_id": owner.id},
            )
            with pytest.raises(RolePermissionForbiddenError, match="owner_permission_floor_required"):
                repository.replace_role_permissions(
                    tenant_id=tenant.id,
                    role_id=owner.id,
                    assignments=assignments,
                    expected_revision=1,
                    idempotency_key=f"owner-floor-{suffix}",
                    correlation_id=f"test-{suffix}",
                )
            with pytest.raises(RolePermissionForbiddenError, match="system_role_cannot_be_inactivated"):
                repository.update_role(
                    tenant_id=tenant.id,
                    role_id=owner.id,
                    name=None,
                    description=None,
                    status="inactive",
                    idempotency_key=f"owner-inactive-{suffix}",
                    correlation_id=f"test-{suffix}",
                )
        finally:
            transaction.rollback()
            engine.dispose()
