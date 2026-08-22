"""Add weighted progress snapshots to production stages.

Revision ID: 20260821_0021
Revises: 20260818_0020
"""

from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0021"
down_revision: str | None = "20260818_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recipe_stages", sa.Column("weight_percent", sa.Numeric(5, 2), nullable=True), schema="production")
    op.execute("""
        with ranked as (
          select id, row_number() over (partition by tenant_id, recipe_version_id order by sort_order, id) as position,
                 count(*) over (partition by tenant_id, recipe_version_id) as stage_count
          from production.recipe_stages where status = 'active'
        )
        update production.recipe_stages s set weight_percent = case
          when ranked.position = ranked.stage_count then 100 - round(100.0 / ranked.stage_count, 2) * (ranked.stage_count - 1)
          else round(100.0 / ranked.stage_count, 2) end
        from ranked where ranked.id = s.id
    """)
    op.execute("update production.recipe_stages set weight_percent = 0 where weight_percent is null")
    op.alter_column("recipe_stages", "weight_percent", nullable=False, schema="production")
    op.create_check_constraint("ck_recipe_stages_weight", "recipe_stages", "weight_percent >= 0 and weight_percent <= 100", schema="production")

    op.add_column("production_order_stages", sa.Column("weight_percent", sa.Numeric(5, 2), nullable=True), schema="production")
    op.add_column("production_order_stages", sa.Column("labor_area_ref_id", sa.String(40), nullable=True), schema="production")
    op.add_column("production_order_stages", sa.Column("labor_area_name_snapshot", sa.String(200), nullable=True), schema="production")
    op.execute("""
        with ranked as (
          select id, row_number() over (partition by tenant_id, production_order_id order by sort_order, id) as position,
                 count(*) over (partition by tenant_id, production_order_id) as stage_count
          from production.production_order_stages
        )
        update production.production_order_stages s set weight_percent = case
          when ranked.position = ranked.stage_count then 100 - round(100.0 / ranked.stage_count, 2) * (ranked.stage_count - 1)
          else round(100.0 / ranked.stage_count, 2) end
        from ranked where ranked.id = s.id
    """)
    op.alter_column("production_order_stages", "weight_percent", nullable=False, schema="production")
    op.create_check_constraint("ck_production_order_stages_weight", "production_order_stages", "weight_percent > 0 and weight_percent <= 100", schema="production")


def downgrade() -> None:
    op.drop_constraint("ck_production_order_stages_weight", "production_order_stages", schema="production", type_="check")
    op.drop_column("production_order_stages", "labor_area_name_snapshot", schema="production")
    op.drop_column("production_order_stages", "labor_area_ref_id", schema="production")
    op.drop_column("production_order_stages", "weight_percent", schema="production")
    op.drop_constraint("ck_recipe_stages_weight", "recipe_stages", schema="production", type_="check")
    op.drop_column("recipe_stages", "weight_percent", schema="production")
