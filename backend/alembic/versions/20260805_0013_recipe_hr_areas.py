"""link recipe stages to HR area references.

Revision ID: 20260805_0013
Revises: 20260804_0012
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa


revision: str = "20260805_0013"
down_revision: str | None = "20260804_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recipe_stages", sa.Column("labor_area_ref_id", sa.String(40), nullable=True), schema="production")
    op.add_column("recipe_stages", sa.Column("labor_area_name", sa.String(200), nullable=True), schema="production")
    op.execute("update production.recipe_stages set labor_area_name = name where labor_area_name is null")
    op.create_index(
        "ix_production_recipe_stages_tenant_labor_area",
        "recipe_stages",
        ["tenant_id", "labor_area_ref_id"],
        schema="production",
    )


def downgrade() -> None:
    op.drop_index("ix_production_recipe_stages_tenant_labor_area", table_name="recipe_stages", schema="production")
    op.drop_column("recipe_stages", "labor_area_name", schema="production")
    op.drop_column("recipe_stages", "labor_area_ref_id", schema="production")
