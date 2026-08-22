"""Separate contracted entitlement from tenant module preference.

Revision ID: 20260818_0016
Revises: 20260817_0015
"""

from alembic import op
import sqlalchemy as sa


revision: str = "20260818_0016"
down_revision: str | None = "20260817_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant_modules",
        sa.Column("tenant_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        schema="admin",
    )
    op.create_index(
        "ix_tenant_modules_tenant_effective",
        "tenant_modules",
        ["tenant_id", "status", "tenant_enabled"],
        schema="admin",
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_modules_tenant_effective", table_name="tenant_modules", schema="admin")
    op.drop_column("tenant_modules", "tenant_enabled", schema="admin")
