"""Tenant-safe permission editor metadata and concurrency state.

Revision ID: 20260730_0011
Revises: 20260730_0010
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0011"
down_revision: str | None = "20260730_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("roles", sa.Column("permission_revision", sa.Integer(), nullable=False, server_default="1"), schema="admin")
    op.add_column("permissions", sa.Column("display_name_es", sa.String(200), nullable=True), schema="admin")
    op.add_column("permissions", sa.Column("display_name_en", sa.String(200), nullable=True), schema="admin")
    op.add_column("permissions", sa.Column("description_es", sa.Text(), nullable=True), schema="admin")
    op.add_column("permissions", sa.Column("description_en", sa.Text(), nullable=True), schema="admin")
    op.add_column("permissions", sa.Column("classification", sa.String(40), nullable=False, server_default="tenant"), schema="admin")
    op.add_column("permissions", sa.Column("assignable_to_tenant_role", sa.Boolean(), nullable=False, server_default=sa.true()), schema="admin")
    op.add_column("permissions", sa.Column("risk_level", sa.String(20), nullable=False, server_default="standard"), schema="admin")
    op.add_column("permissions", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="1000"), schema="admin")
    op.execute("UPDATE admin.permissions SET display_name_es = code, display_name_en = code, description_es = coalesce(description, code), description_en = coalesce(description, code)")
    op.execute("UPDATE admin.permissions SET classification = case when split_part(code, '.', 1) = 'external' then 'integration' else split_part(code, '.', 1) end, assignable_to_tenant_role = false WHERE split_part(code, '.', 1) IN ('internal','public','external')")
    op.execute("UPDATE admin.permissions SET classification = 'internal', assignable_to_tenant_role = false WHERE code LIKE 'billing.manual_activation.%'")
    op.alter_column("permissions", "display_name_es", nullable=False, schema="admin")
    op.alter_column("permissions", "display_name_en", nullable=False, schema="admin")
    op.alter_column("permissions", "description_es", nullable=False, schema="admin")
    op.alter_column("permissions", "description_en", nullable=False, schema="admin")
    op.create_check_constraint("ck_permissions_classification", "permissions", "classification in ('tenant','internal','public','integration')", schema="admin")
    op.create_check_constraint("ck_permissions_risk_level", "permissions", "risk_level in ('low','standard','high','critical')", schema="admin")
    op.create_check_constraint("ck_permissions_tenant_assignable", "permissions", "classification = 'tenant' or assignable_to_tenant_role = false", schema="admin")
    op.create_index("ix_permissions_classification_assignable", "permissions", ["classification", "assignable_to_tenant_role"], schema="admin")
    op.create_table(
        "command_idempotency",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("operation", sa.String(180), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_command_idempotency_scope"),
        schema="admin",
    )
    op.execute(
        """
        INSERT INTO admin.permissions (
            id, code, module_code, resource, action, description, status,
            display_name_es, display_name_en, description_es, description_en,
            classification, assignable_to_tenant_role, risk_level, sort_order
        ) VALUES (
            'per_f9ca12efcda6546fa0c25e2c51',
            'admin.role.permissions.manage',
            'admin',
            'role.permissions',
            'manage',
            'Manage role permission assignments.',
            'active',
            'Administrar permisos de roles',
            'Manage role permissions',
            'Permite administrar permisos de roles dentro de Administracion.',
            'Allows users to manage role permissions in Administration.',
            'tenant', true, 'high', 1060
        )
        ON CONFLICT (code) DO UPDATE SET
            classification = 'tenant',
            assignable_to_tenant_role = true,
            risk_level = 'high',
            status = 'active'
        """
    )
    op.execute(
        """
        INSERT INTO admin.role_permissions (id, tenant_id, role_id, permission_id, scope)
        SELECT
            'rpe_' || substr(md5(roles.tenant_id || ':' || roles.id || ':' || permissions.id), 1, 26),
            roles.tenant_id,
            roles.id,
            permissions.id,
            '{}'::jsonb
        FROM admin.roles roles
        JOIN admin.permissions permissions ON permissions.code = 'admin.role.permissions.manage'
        WHERE roles.code = 'owner' AND roles.system_role = true AND roles.status = 'active'
        ON CONFLICT (tenant_id, role_id, permission_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("command_idempotency", schema="admin")
    op.execute("DELETE FROM admin.role_permissions WHERE permission_id = 'per_f9ca12efcda6546fa0c25e2c51'")
    op.execute("DELETE FROM admin.permissions WHERE id = 'per_f9ca12efcda6546fa0c25e2c51' AND code = 'admin.role.permissions.manage'")
    op.drop_index("ix_permissions_classification_assignable", table_name="permissions", schema="admin")
    op.drop_constraint("ck_permissions_risk_level", "permissions", schema="admin", type_="check")
    op.drop_constraint("ck_permissions_classification", "permissions", schema="admin", type_="check")
    op.drop_constraint("ck_permissions_tenant_assignable", "permissions", schema="admin", type_="check")
    for column in ("sort_order", "risk_level", "assignable_to_tenant_role", "classification", "description_en", "description_es", "display_name_en", "display_name_es"):
        op.drop_column("permissions", column, schema="admin")
    op.drop_column("roles", "permission_revision", schema="admin")
