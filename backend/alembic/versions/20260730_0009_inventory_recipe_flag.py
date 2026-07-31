"""add inventory recipe eligibility flag.

Revision ID: 20260730_0009
Revises: 20260727_0008
"""
from alembic import op
import sqlalchemy as sa


revision: str = "20260730_0009"
down_revision: str | None = "20260727_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "items",
        sa.Column("use_in_recipe", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        schema="inventory",
    )
    op.create_index(
        "ix_inventory_items_tenant_recipe_status",
        "items",
        ["tenant_id", "use_in_recipe", "status"],
        schema="inventory",
    )


def downgrade() -> None:
    op.drop_index("ix_inventory_items_tenant_recipe_status", table_name="items", schema="inventory")
    op.drop_column("items", "use_in_recipe", schema="inventory")
