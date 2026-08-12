"""production machines, orders and executable stages.

Revision ID: 20260804_0012
Revises: 20260730_0011
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260804_0012"
down_revision: str | None = "20260730_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_services", sa.Column("cost_center", sa.String(160), nullable=True), schema="production")
    op.add_column("product_services", sa.Column("expected_margin", sa.Numeric(9, 4), nullable=True), schema="production")
    op.add_column("product_services", sa.Column("description", sa.Text(), nullable=True), schema="production")
    op.create_check_constraint("ck_product_services_expected_margin", "product_services", "expected_margin is null or (expected_margin >= 0 and expected_margin <= 100)", schema="production")
    op.create_table(
        "machines",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("machine_type", sa.String(120), nullable=False),
        sa.Column("area_name", sa.String(200), nullable=True),
        sa.Column("available_minutes_per_day", sa.Numeric(18, 6), nullable=False),
        sa.Column("cost_per_minute", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('active','inactive','maintenance')", name="ck_production_machines_status"),
        sa.CheckConstraint("available_minutes_per_day > 0", name="ck_production_machines_capacity"),
        sa.CheckConstraint("cost_per_minute >= 0", name="ck_production_machines_cost"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_production_machines_tenant_code"),
        schema="production",
    )
    op.create_index("ix_production_machines_tenant_status", "machines", ["tenant_id", "status"], schema="production")

    op.create_table(
        "production_orders",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("product_service_id", sa.String(40), nullable=False),
        sa.Column("recipe_id", sa.String(40), nullable=False),
        sa.Column("recipe_version_id", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("required_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responsible_name_snapshot", sa.String(200), nullable=False),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("source_id", sa.String(80), nullable=True),
        sa.Column("source_line_id", sa.String(80), nullable=True),
        sa.Column("planned_cost", sa.Numeric(18, 6), nullable=False),
        sa.Column("actual_cost", sa.Numeric(18, 6), nullable=True),
        sa.Column("recipe_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("resource_validation_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(80), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("quantity > 0", name="ck_production_orders_quantity"),
        sa.CheckConstraint("planned_cost >= 0", name="ck_production_orders_planned_cost"),
        sa.CheckConstraint("actual_cost is null or actual_cost >= 0", name="ck_production_orders_actual_cost"),
        sa.CheckConstraint("status in ('released','waiting_resources','in_progress','paused','in_validation','completed','cancelled')", name="ck_production_orders_status"),
        sa.CheckConstraint("source_type in ('manual','sales_order','integration')", name="ck_production_orders_source_type"),
        sa.CheckConstraint("priority in ('low','medium','high')", name="ck_production_orders_priority"),
        sa.ForeignKeyConstraint(["product_service_id"], ["production.product_services.id"], name="fk_production_orders_product"),
        sa.ForeignKeyConstraint(["recipe_id"], ["production.recipes.id"], name="fk_production_orders_recipe"),
        sa.ForeignKeyConstraint(["recipe_version_id"], ["production.recipe_versions.id"], name="fk_production_orders_recipe_version"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_production_orders_tenant_code"),
        schema="production",
    )
    op.create_index("ix_production_orders_tenant_status", "production_orders", ["tenant_id", "status"], schema="production")
    op.create_index("ix_production_orders_tenant_product", "production_orders", ["tenant_id", "product_service_id"], schema="production")
    op.create_index("ix_production_orders_tenant_source", "production_orders", ["tenant_id", "source_type", "source_id"], schema="production")

    op.create_table(
        "production_order_stages",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("production_order_id", sa.String(40), nullable=False),
        sa.Column("recipe_stage_id", sa.String(40), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description_snapshot", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("planned_minutes", sa.Numeric(18, 6), nullable=True),
        sa.Column("actual_minutes", sa.Numeric(18, 6), nullable=True),
        sa.Column("responsible_name_snapshot", sa.String(200), nullable=True),
        sa.Column("progress_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('pending','in_progress','completed','skipped','blocked')", name="ck_production_order_stages_status"),
        sa.CheckConstraint("planned_minutes is null or planned_minutes >= 0", name="ck_production_order_stages_planned_minutes"),
        sa.CheckConstraint("actual_minutes is null or actual_minutes >= 0", name="ck_production_order_stages_actual_minutes"),
        sa.CheckConstraint("progress_percent >= 0 and progress_percent <= 100", name="ck_production_order_stages_progress"),
        sa.ForeignKeyConstraint(["production_order_id"], ["production.production_orders.id"], name="fk_production_order_stages_order", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="production",
    )
    op.create_index("ix_production_order_stages_tenant_order", "production_order_stages", ["tenant_id", "production_order_id", "sort_order"], schema="production")
    op.create_index("ix_production_order_stages_tenant_status", "production_order_stages", ["tenant_id", "status"], schema="production")

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(40), nullable=False),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        schema="production",
    )
    op.create_index("ix_production_audit_tenant_resource", "audit_events", ["tenant_id", "resource_type", "resource_id", "occurred_at"], schema="production")


def downgrade() -> None:
    op.drop_index("ix_production_audit_tenant_resource", table_name="audit_events", schema="production")
    op.drop_table("audit_events", schema="production")
    op.drop_index("ix_production_order_stages_tenant_status", table_name="production_order_stages", schema="production")
    op.drop_index("ix_production_order_stages_tenant_order", table_name="production_order_stages", schema="production")
    op.drop_table("production_order_stages", schema="production")
    op.drop_index("ix_production_orders_tenant_source", table_name="production_orders", schema="production")
    op.drop_index("ix_production_orders_tenant_product", table_name="production_orders", schema="production")
    op.drop_index("ix_production_orders_tenant_status", table_name="production_orders", schema="production")
    op.drop_table("production_orders", schema="production")
    op.drop_index("ix_production_machines_tenant_status", table_name="machines", schema="production")
    op.drop_table("machines", schema="production")
    op.execute("alter table production.product_services drop constraint if exists ck_product_services_expected_margin")
    op.execute("alter table production.product_services drop column if exists description")
    op.execute("alter table production.product_services drop column if exists expected_margin")
    op.execute("alter table production.product_services drop column if exists cost_center")
