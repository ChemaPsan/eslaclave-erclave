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
from app.schemas import UnitOfMeasureCreateRequest, UnitOfMeasureUpdateRequest


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


@pytest.mark.skipif(not os.getenv("ERCLAVE_TEST_DATABASE_URL"), reason="local PostgreSQL integration URL not configured")
def test_unit_commands_are_tenant_safe_idempotent_and_audited():
    engine = create_engine(os.environ["ERCLAVE_TEST_DATABASE_URL"])
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            repository = AdminRepository(TransactionEngine(connection))
            suffix = uuid4().hex[:12]
            tenant = repository.create_tenant(
                slug=f"unit-catalog-{suffix}", commercial_name="Unit catalog integration", legal_name=None,
                plan_id=None, timezone="America/Mexico_City", locale="es-MX",
                source={"type": "test", "id": suffix}, organization_profile=None,
                idempotency_key=f"tenant-unit-{suffix}", correlation_id=f"test-{suffix}",
            )
            payload = UnitOfMeasureCreateRequest(code="svc.test", name_es="Servicio prueba", name_en="Test service", symbol="svc", category="other", decimal_places=2)
            created = repository.create_unit_of_measure(tenant.id, payload, f"unit-create-{suffix}", f"test-{suffix}")
            replay = repository.create_unit_of_measure(tenant.id, payload, f"unit-create-{suffix}", f"test-{suffix}")
            assert replay == created
            with pytest.raises(IdempotencyConflictError):
                repository.create_unit_of_measure(tenant.id, payload.model_copy(update={"symbol": "otro"}), f"unit-create-{suffix}", f"test-{suffix}")

            updated = repository.update_unit_of_measure(tenant.id, created.id, UnitOfMeasureUpdateRequest(status="inactive"), f"unit-update-{suffix}", f"test-{suffix}")
            assert updated is not None and updated.status == "inactive"
            assert repository.update_unit_of_measure(tenant.id, created.id, UnitOfMeasureUpdateRequest(status="inactive"), f"unit-update-{suffix}", f"test-{suffix}") == updated
            assert repository.get_unit_of_measure(tenant.id, created.code, active_only=True) is None
            assert repository.get_unit_of_measure(f"ten_other_{suffix}", created.code) is None
            assert connection.execute(text("select count(*) from admin.audit_events where tenant_id=:tenant_id and resource_type='unit_of_measure'"), {"tenant_id": tenant.id}).scalar_one() == 2
            assert connection.execute(text("select count(*) from admin.command_idempotency where tenant_id=:tenant_id and operation like 'admin.unit.%'"), {"tenant_id": tenant.id}).scalar_one() == 2
        finally:
            transaction.rollback()
            engine.dispose()


@pytest.mark.skipif(not os.getenv("ERCLAVE_TEST_DATABASE_URL"), reason="local PostgreSQL integration URL not configured")
def test_backoffice_entitlement_and_tenant_preference_are_separate_tenant_safe_commands():
    engine = create_engine(os.environ["ERCLAVE_TEST_DATABASE_URL"])
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            repository = AdminRepository(TransactionEngine(connection))
            suffix = uuid4().hex[:12]
            tenants = [
                repository.create_tenant(
                    slug=f"module-control-{index}-{suffix}",
                    commercial_name=f"Module control {index}",
                    legal_name=None,
                    plan_id="manual",
                    timezone="America/Mexico_City",
                    locale="es-MX",
                    source={"type": "test", "id": f"{suffix}-{index}"},
                    organization_profile=None,
                    idempotency_key=f"tenant-module-{index}-{suffix}",
                    correlation_id=f"test-{suffix}",
                )
                for index in (1, 2)
            ]
            tenant, other_tenant = tenants
            connection.execute(
                text("update admin.tenants set status='active' where id = any(:tenant_ids)"),
                {"tenant_ids": [tenant.id, other_tenant.id]},
            )

            granted = repository.set_backoffice_entitlement(
                tenant.id, "production", "active", {"orders": 25}, "manual",
                f"grant-{suffix}", f"test-{suffix}",
            )
            assert granted is not None
            assert granted.status == "active"
            assert granted.tenant_enabled is True
            assert granted.effective_active is True
            assert repository.list_entitlements(other_tenant.id) == []

            with pytest.raises(ValueError, match="module_dependencies_required:hr"):
                repository.set_backoffice_entitlement(
                    tenant.id, "sales", "active", {}, "manual",
                    f"sales-missing-dependency-{suffix}", f"test-{suffix}",
                )
            repository.set_backoffice_entitlement(
                tenant.id, "hr", "active", {}, "manual",
                f"grant-hr-{suffix}", f"test-{suffix}",
            )
            sales = repository.set_backoffice_entitlement(
                tenant.id, "sales", "active", {}, "manual",
                f"grant-sales-{suffix}", f"test-{suffix}",
            )
            assert sales is not None and sales.effective_active is True
            with pytest.raises(ValueError, match="module_dependency_in_use:sales"):
                repository.update_entitlement_preference(
                    tenant.id, "production", False, f"production-blocked-{suffix}", f"test-{suffix}",
                )
            repository.update_entitlement_preference(
                tenant.id, "sales", False, f"disable-sales-{suffix}", f"test-{suffix}",
            )

            disabled = repository.update_entitlement_preference(
                tenant.id, "production", False, f"preference-{suffix}", f"test-{suffix}",
            )
            replay = repository.update_entitlement_preference(
                tenant.id, "production", False, f"preference-{suffix}", f"test-{suffix}",
            )
            assert disabled == replay
            assert disabled is not None and disabled.status == "active"
            assert disabled.tenant_enabled is False
            assert disabled.effective_active is False
            assert repository.evaluate_policy(tenant.id, "usr_missing", "production", "order", "read").reason == "module_not_active"

            with pytest.raises(IdempotencyConflictError):
                repository.update_entitlement_preference(
                    tenant.id, "production", True, f"preference-{suffix}", f"test-{suffix}",
                )
            assert repository.update_entitlement_preference(
                other_tenant.id, "production", False, f"other-{suffix}", f"test-{suffix}",
            ) is None

            withdrawn = repository.set_backoffice_entitlement(
                tenant.id, "production", "inactive", {}, "manual",
                f"withdraw-{suffix}", f"test-{suffix}",
            )
            assert withdrawn is not None and withdrawn.status == "inactive"
            assert withdrawn.effective_active is False
            with pytest.raises(ValueError, match="module_not_contracted"):
                repository.update_entitlement_preference(
                    tenant.id, "production", True, f"blocked-{suffix}", f"test-{suffix}",
                )

            updated_tenant = repository.update_backoffice_tenant(
                tenant.id,
                {"commercial_name": "Module control edited", "plan_id": "premium"},
                f"update-tenant-{suffix}",
                f"test-{suffix}",
            )
            assert updated_tenant is not None and updated_tenant.commercial_name == "Module control edited"
            assert repository.get_tenant(other_tenant.id).commercial_name == "Module control 2"
            assert connection.execute(
                text("select count(*) from admin.audit_events where tenant_id=:tenant_id and action like '%entitlement%'") ,
                {"tenant_id": tenant.id},
            ).scalar_one() == 6
        finally:
            transaction.rollback()
            engine.dispose()


@pytest.mark.skipif(not os.getenv("ERCLAVE_TEST_DATABASE_URL"), reason="local PostgreSQL integration URL not configured")
def test_onboarding_assigns_owner_permissions_after_modules_are_created():
    engine = create_engine(os.environ["ERCLAVE_TEST_DATABASE_URL"])
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            repository = AdminRepository(TransactionEngine(connection))
            suffix = uuid4().hex[:12]
            result = repository.onboard_tenant(
                slug=f"sales-onboarding-{suffix}",
                commercial_name="Sales onboarding integration",
                legal_name=None,
                plan_id="manual",
                timezone="America/Mexico_City",
                locale="es-MX",
                source={"type": "test", "id": suffix},
                owner={"email": f"owner-{suffix}@example.com", "display_name": "Owner Sales", "status": "active", "branch_ids": ["*"]},
                organization_profile=None,
                modules=[
                    {"module_code": "admin", "status": "active", "limits": {}, "source": "manual"},
                    {"module_code": "hr", "status": "active", "limits": {}, "source": "manual"},
                    {"module_code": "production", "status": "active", "limits": {}, "source": "manual"},
                    {"module_code": "sales", "status": "active", "limits": {}, "source": "manual"},
                ],
                idempotency_key=f"onboard-sales-{suffix}",
                correlation_id=f"test-{suffix}",
            )
            tenant_id = result["tenant"].id
            sales_permission_count = connection.execute(
                text("""select count(*) from admin.role_permissions role_permissions
                    join admin.roles roles on roles.tenant_id=role_permissions.tenant_id and roles.id=role_permissions.role_id
                    join admin.permissions permissions on permissions.id=role_permissions.permission_id
                    where role_permissions.tenant_id=:tenant_id and roles.code='owner' and permissions.module_code='sales'"""),
                {"tenant_id": tenant_id},
            ).scalar_one()
            assert sales_permission_count > 0
        finally:
            transaction.rollback()
            engine.dispose()
