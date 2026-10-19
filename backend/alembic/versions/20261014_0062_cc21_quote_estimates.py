"""CC-21: confirmed Division cost and quote estimate provenance."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "20261014_0062"
down_revision: str | None = "20261014_0061"
branch_labels = None
depends_on = None

SALES_TABLES = ("quotes", "quote_lines", "orders", "order_lines")
PRODUCTION_TABLE = "product_service_division_assignments"


def upgrade():
    op.add_column(PRODUCTION_TABLE, sa.Column("estimated_unit_cost", sa.Numeric(18, 6), nullable=True), schema="production")
    op.add_column(PRODUCTION_TABLE, sa.Column("cost_currency", sa.String(3), nullable=True), schema="production")
    op.add_column(PRODUCTION_TABLE, sa.Column("cost_society_ref_id", sa.String(40), nullable=True), schema="production")
    op.add_column(PRODUCTION_TABLE, sa.Column("cost_confirmed_at", sa.DateTime(timezone=True), nullable=True), schema="production")
    op.create_check_constraint(
        "ck_cc21_product_assignment_estimated_cost",
        PRODUCTION_TABLE,
        "(estimated_unit_cost is null and cost_currency is null and cost_society_ref_id is null and cost_confirmed_at is null) "
        "or (estimated_unit_cost is not null and estimated_unit_cost >= 0 and estimated_unit_cost != 'NaN'::numeric "
        "and cost_currency ~ '^[A-Z]{3}$' and length(cost_society_ref_id) > 0 and cost_confirmed_at is not null)",
        schema="production",
    )
    for table in SALES_TABLES:
        op.add_column(table, sa.Column("estimated_cost_snapshot", JSONB, nullable=True), schema="sales")
        op.create_check_constraint(
            f"ck_cc21_{table}_estimate_snapshot",
            table,
            "estimated_cost_snapshot is null or jsonb_typeof(estimated_cost_snapshot) = 'object'",
            schema="sales",
        )


def downgrade():
    op.execute(
        "LOCK TABLE production.product_service_division_assignments, sales.quotes, sales.quote_lines, "
        "sales.orders, sales.order_lines IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""DO $$ BEGIN IF
        EXISTS (SELECT 1 FROM production.product_service_division_assignments WHERE estimated_unit_cost IS NOT NULL)
        OR EXISTS (SELECT 1 FROM sales.quotes WHERE estimated_cost_snapshot IS NOT NULL)
        OR EXISTS (SELECT 1 FROM sales.quote_lines WHERE estimated_cost_snapshot IS NOT NULL)
        OR EXISTS (SELECT 1 FROM sales.orders WHERE estimated_cost_snapshot IS NOT NULL)
        OR EXISTS (SELECT 1 FROM sales.order_lines WHERE estimated_cost_snapshot IS NOT NULL)
        THEN RAISE EXCEPTION 'CC21 monetary estimate history exists; use forward-fix'; END IF; END $$""")
    for table in reversed(SALES_TABLES):
        op.drop_constraint(f"ck_cc21_{table}_estimate_snapshot", table, type_="check", schema="sales")
        op.drop_column(table, "estimated_cost_snapshot", schema="sales")
    op.drop_constraint("ck_cc21_product_assignment_estimated_cost", PRODUCTION_TABLE, type_="check", schema="production")
    for column in ("cost_confirmed_at", "cost_society_ref_id", "cost_currency", "estimated_unit_cost"):
        op.drop_column(PRODUCTION_TABLE, column, schema="production")
