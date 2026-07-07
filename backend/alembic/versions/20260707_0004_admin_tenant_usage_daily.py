"""daily tenant usage metrics for admin-service.

Revision ID: 20260707_0004
Revises: 20260705_0003
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260707_0004"
down_revision: str | None = "20260705_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenant_usage_daily",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("active_users", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("api_requests", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("storage_mb", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("estimated_cost_mxn", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("active_users >= 0", name="ck_tenant_usage_daily_active_users_non_negative"),
        sa.CheckConstraint("api_requests >= 0", name="ck_tenant_usage_daily_api_requests_non_negative"),
        sa.CheckConstraint("storage_mb >= 0", name="ck_tenant_usage_daily_storage_non_negative"),
        sa.CheckConstraint("estimated_cost_mxn >= 0", name="ck_tenant_usage_daily_cost_non_negative"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "usage_date", name="uq_tenant_usage_daily_tenant_date"),
        schema="admin",
    )
    op.create_index(
        "ix_tenant_usage_daily_date_tenant",
        "tenant_usage_daily",
        ["usage_date", "tenant_id"],
        schema="admin",
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_usage_daily_date_tenant", table_name="tenant_usage_daily", schema="admin")
    op.drop_table("tenant_usage_daily", schema="admin")
