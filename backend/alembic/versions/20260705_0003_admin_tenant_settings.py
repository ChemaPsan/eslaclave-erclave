"""tenant settings for admin-service.

Revision ID: 20260705_0003
Revises: 20260701_0002
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260705_0003"
down_revision: str | None = "20260701_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_settings",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("key", sa.String(length=160), nullable=False),
        sa.Column("module_code", sa.String(length=80), nullable=True),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key", name="uq_tenant_settings_tenant_key"),
        schema="admin",
    )
    op.create_index("ix_tenant_settings_tenant_module", "tenant_settings", ["tenant_id", "module_code"], schema="admin")


def downgrade() -> None:
    op.drop_index("ix_tenant_settings_tenant_module", table_name="tenant_settings", schema="admin")
    op.drop_table("tenant_settings", schema="admin")
