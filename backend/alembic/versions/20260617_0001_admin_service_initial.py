"""admin-service initial physical model.

Revision ID: 20260617_0001
Revises:
Create Date: 2026-06-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260617_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS admin")

    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("legal_name", sa.String(length=240), nullable=True),
        sa.Column("commercial_name", sa.String(length=240), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("plan_id", sa.String(length=40), nullable=True),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column("locale", sa.String(length=20), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=True),
        sa.Column("source_id", sa.String(length=120), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status in ('provisioning', 'active', 'suspended', 'cancelled')",
            name="ck_tenants_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        schema="admin",
    )
    op.create_index("ix_tenants_status", "tenants", ["status"], schema="admin")

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("identity_provider_id", sa.String(length=160), nullable=True),
        sa.Column("email", sa.String(length=240), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status in ('invited', 'active', 'disabled')", name="ck_users_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("identity_provider_id"),
        schema="admin",
    )
    op.create_index("ix_users_status", "users", ["status"], schema="admin")

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("code", sa.String(length=160), nullable=False),
        sa.Column("module_code", sa.String(length=80), nullable=False),
        sa.Column("resource", sa.String(length=80), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status in ('active', 'inactive')", name="ck_permissions_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema="admin",
    )
    op.create_index(
        "ix_permissions_module_resource_action",
        "permissions",
        ["module_code", "resource", "action"],
        schema="admin",
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("system_role", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status in ('active', 'inactive')", name="ck_roles_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),
        schema="admin",
    )
    op.create_index("ix_roles_tenant_status", "roles", ["tenant_id", "status"], schema="admin")

    op.create_table(
        "tenant_modules",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("module_code", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("limits", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status in ('active', 'inactive', 'suspended')", name="ck_tenant_modules_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "module_code", name="uq_tenant_modules_tenant_module"),
        schema="admin",
    )
    op.create_index("ix_tenant_modules_tenant_status", "tenant_modules", ["tenant_id", "status"], schema="admin")

    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status in ('invited', 'active', 'disabled')", name="ck_memberships_status"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["admin.users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),
        schema="admin",
    )
    op.create_index("ix_memberships_tenant_status", "memberships", ["tenant_id", "status"], schema="admin")

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("role_id", sa.String(length=40), nullable=False),
        sa.Column("permission_id", sa.String(length=40), nullable=False),
        sa.Column("scope", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["admin.permissions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["admin.roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "role_id", "permission_id", name="uq_role_permissions_role_permission"),
        schema="admin",
    )

    op.create_table(
        "membership_roles",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("membership_id", sa.String(length=40), nullable=False),
        sa.Column("role_id", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["membership_id"], ["admin.memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["admin.roles.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "membership_id", "role_id", name="uq_membership_roles_membership_role"),
        schema="admin",
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=True),
        sa.Column("actor_user_id", sa.String(length=40), nullable=True),
        sa.Column("actor_type", sa.String(length=40), nullable=False),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("source_service", sa.String(length=80), nullable=False),
        sa.Column("correlation_id", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["admin.users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        schema="admin",
    )
    op.create_index("ix_audit_events_tenant_occurred", "audit_events", ["tenant_id", "occurred_at"], schema="admin")
    op.create_index("ix_audit_events_resource", "audit_events", ["resource_type", "resource_id"], schema="admin")
    op.create_index("ix_audit_events_correlation", "audit_events", ["correlation_id"], schema="admin")


def downgrade() -> None:
    op.drop_index("ix_audit_events_correlation", table_name="audit_events", schema="admin")
    op.drop_index("ix_audit_events_resource", table_name="audit_events", schema="admin")
    op.drop_index("ix_audit_events_tenant_occurred", table_name="audit_events", schema="admin")
    op.drop_table("audit_events", schema="admin")
    op.drop_table("membership_roles", schema="admin")
    op.drop_table("role_permissions", schema="admin")
    op.drop_index("ix_memberships_tenant_status", table_name="memberships", schema="admin")
    op.drop_table("memberships", schema="admin")
    op.drop_index("ix_tenant_modules_tenant_status", table_name="tenant_modules", schema="admin")
    op.drop_table("tenant_modules", schema="admin")
    op.drop_index("ix_roles_tenant_status", table_name="roles", schema="admin")
    op.drop_table("roles", schema="admin")
    op.drop_index("ix_permissions_module_resource_action", table_name="permissions", schema="admin")
    op.drop_table("permissions", schema="admin")
    op.drop_index("ix_users_status", table_name="users", schema="admin")
    op.drop_table("users", schema="admin")
    op.drop_index("ix_tenants_status", table_name="tenants", schema="admin")
    op.drop_table("tenants", schema="admin")
