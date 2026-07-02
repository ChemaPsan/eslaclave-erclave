"""production-service initial physical model.

Revision ID: 20260701_0002
Revises: 20260617_0001
Create Date: 2026-07-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260701_0002"
down_revision: str | None = "20260617_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS production")

    op.create_table(
        "product_services",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("tenant_id", sa.String(length=40), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=240), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("base_unit", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("target_price", sa.Numeric(14, 4), nullable=True),
        sa.Column("standard_cost", sa.Numeric(14, 4), nullable=True),
        sa.Column("responsible_area", sa.String(length=160), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("type in ('product', 'service')", name="ck_product_services_type"),
        sa.CheckConstraint("status in ('active', 'inactive', 'pending_approval')", name="ck_product_services_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_product_services_tenant_code"),
        schema="production",
    )
    op.create_index(
        "ix_product_services_tenant_status",
        "product_services",
        ["tenant_id", "status"],
        schema="production",
    )
    op.create_index(
        "ix_product_services_tenant_type",
        "product_services",
        ["tenant_id", "type"],
        schema="production",
    )


def downgrade() -> None:
    op.drop_index("ix_product_services_tenant_type", table_name="product_services", schema="production")
    op.drop_index("ix_product_services_tenant_status", table_name="product_services", schema="production")
    op.drop_table("product_services", schema="production")
    op.execute("DROP SCHEMA IF EXISTS production")
