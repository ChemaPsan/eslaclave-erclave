"""production multi-day capacity planning.

Revision ID: 20260825_0029
Revises: 20260824_0028
"""
from alembic import op
import sqlalchemy as sa


revision: str = "20260825_0029"
down_revision: str | None = "20260824_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recipe_versions",
        sa.Column("suggested_duration_days", sa.Integer(), nullable=False, server_default="1"),
        schema="production",
    )
    op.create_check_constraint(
        "ck_recipe_versions_suggested_duration_days",
        "recipe_versions",
        "suggested_duration_days between 1 and 365",
        schema="production",
    )
    op.add_column(
        "production_orders",
        sa.Column("planned_duration_days", sa.Integer(), nullable=False, server_default="1"),
        schema="production",
    )
    op.add_column("production_orders", sa.Column("planned_end_date", sa.Date()), schema="production")
    op.create_check_constraint(
        "ck_production_orders_planned_duration_days",
        "production_orders",
        "planned_duration_days between 1 and 365",
        schema="production",
    )
    op.drop_constraint(
        "uq_production_capacity_order_resource",
        "capacity_commitments",
        schema="production",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_production_capacity_order_resource_date",
        "capacity_commitments",
        ["tenant_id", "production_order_id", "resource_type", "resource_ref_id", "planned_date"],
        schema="production",
    )


def downgrade() -> None:
    # Preserve the total number of committed minutes before restoring the former
    # one-row-per-order/resource representation.
    op.execute(sa.text("""
        update production.capacity_commitments target
        set quantity_minutes = totals.quantity_minutes,
            updated_at = now()
        from (
            select tenant_id, production_order_id, resource_type, resource_ref_id,
                   (array_agg(id order by planned_date, id))[1] keep_id,
                   sum(quantity_minutes) quantity_minutes
            from production.capacity_commitments
            group by tenant_id, production_order_id, resource_type, resource_ref_id
        ) totals
        where target.id = totals.keep_id
    """))
    op.execute(sa.text("""
        delete from production.capacity_commitments target
        using (
            select tenant_id, production_order_id, resource_type, resource_ref_id,
                   (array_agg(id order by planned_date, id))[1] keep_id
            from production.capacity_commitments
            group by tenant_id, production_order_id, resource_type, resource_ref_id
        ) totals
        where target.tenant_id = totals.tenant_id
          and target.production_order_id = totals.production_order_id
          and target.resource_type = totals.resource_type
          and target.resource_ref_id = totals.resource_ref_id
          and target.id <> totals.keep_id
    """))
    op.drop_constraint(
        "uq_production_capacity_order_resource_date",
        "capacity_commitments",
        schema="production",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_production_capacity_order_resource",
        "capacity_commitments",
        ["tenant_id", "production_order_id", "resource_type", "resource_ref_id"],
        schema="production",
    )
    op.drop_constraint(
        "ck_production_orders_planned_duration_days", "production_orders", schema="production", type_="check"
    )
    op.drop_column("production_orders", "planned_end_date", schema="production")
    op.drop_column("production_orders", "planned_duration_days", schema="production")
    op.drop_constraint(
        "ck_recipe_versions_suggested_duration_days", "recipe_versions", schema="production", type_="check"
    )
    op.drop_column("recipe_versions", "suggested_duration_days", schema="production")
