"""production recipes and versioning.

Revision ID: 20260721_0005
Revises: 20260707_0004
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260721_0005"
down_revision: str | None = "20260707_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("product_service_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="draft"),
        sa.Column("current_version_id", sa.String(40), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft', 'active', 'inactive')", name="ck_recipes_status"),
        sa.ForeignKeyConstraint(["product_service_id"], ["production.product_services.id"], name="fk_recipes_product_service"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_recipes_tenant_code"),
        schema="production",
    )
    op.create_index("ix_recipes_tenant_product", "recipes", ["tenant_id", "product_service_id"], schema="production")

    op.create_table(
        "recipe_versions",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("recipe_id", sa.String(40), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="draft"),
        sa.Column("base_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("base_unit", sa.String(40), nullable=False),
        sa.Column("standard_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(40), nullable=True),
        sa.Column("obsolete_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft', 'pending_approval', 'approved', 'obsolete')", name="ck_recipe_versions_status"),
        sa.CheckConstraint("base_quantity > 0", name="ck_recipe_versions_base_quantity"),
        sa.ForeignKeyConstraint(["recipe_id"], ["production.recipes.id"], name="fk_recipe_versions_recipe"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "recipe_id", "version_number", name="uq_recipe_versions_number"),
        schema="production",
    )
    op.create_index("ix_recipe_versions_tenant_recipe_status", "recipe_versions", ["tenant_id", "recipe_id", "status"], schema="production")

    op.create_table(
        "recipe_resources",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("recipe_version_id", sa.String(40), nullable=False),
        sa.Column("resource_type", sa.String(40), nullable=False),
        sa.Column("resource_ref_id", sa.String(40), nullable=True),
        sa.Column("resource_code", sa.String(80), nullable=False),
        sa.Column("resource_name", sa.String(240), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("resource_type in ('material', 'labor', 'machine', 'other')", name="ck_recipe_resources_type"),
        sa.CheckConstraint("quantity > 0", name="ck_recipe_resources_quantity"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_recipe_resources_unit_cost"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["production.recipe_versions.id"], name="fk_recipe_resources_version", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="production",
    )
    op.create_index("ix_recipe_resources_tenant_version", "recipe_resources", ["tenant_id", "recipe_version_id"], schema="production")
    op.create_index("ix_recipe_resources_tenant_reference", "recipe_resources", ["tenant_id", "resource_type", "resource_ref_id"], schema="production")

    op.create_table(
        "recipe_stages",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("recipe_version_id", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("expected_minutes", sa.Numeric(18, 6), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.CheckConstraint("status in ('active', 'inactive')", name="ck_recipe_stages_status"),
        sa.CheckConstraint("expected_minutes is null or expected_minutes >= 0", name="ck_recipe_stages_minutes"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["production.recipe_versions.id"], name="fk_recipe_stages_version", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="production",
    )
    op.create_index("ix_recipe_stages_tenant_version_order", "recipe_stages", ["tenant_id", "recipe_version_id", "sort_order"], schema="production")
    op.create_foreign_key("fk_recipes_current_version", "recipes", "recipe_versions", ["current_version_id"], ["id"], source_schema="production", referent_schema="production")
    op.add_column("product_services", sa.Column("current_recipe_version_id", sa.String(40), nullable=True), schema="production")
    op.create_foreign_key("fk_product_services_current_recipe", "product_services", "recipe_versions", ["current_recipe_version_id"], ["id"], source_schema="production", referent_schema="production")


def downgrade() -> None:
    op.drop_constraint("fk_product_services_current_recipe", "product_services", schema="production", type_="foreignkey")
    op.drop_column("product_services", "current_recipe_version_id", schema="production")
    op.drop_constraint("fk_recipes_current_version", "recipes", schema="production", type_="foreignkey")
    op.drop_index("ix_recipe_stages_tenant_version_order", table_name="recipe_stages", schema="production")
    op.drop_table("recipe_stages", schema="production")
    op.drop_index("ix_recipe_resources_tenant_reference", table_name="recipe_resources", schema="production")
    op.drop_index("ix_recipe_resources_tenant_version", table_name="recipe_resources", schema="production")
    op.drop_table("recipe_resources", schema="production")
    op.drop_index("ix_recipe_versions_tenant_recipe_status", table_name="recipe_versions", schema="production")
    op.drop_table("recipe_versions", schema="production")
    op.drop_index("ix_recipes_tenant_product", table_name="recipes", schema="production")
    op.drop_table("recipes", schema="production")
