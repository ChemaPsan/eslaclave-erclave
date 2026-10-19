"""Freeze stock cost currency and explicit conversion on sales fulfillment."""
from alembic import op
import sqlalchemy as sa
revision: str = "20261005_0049"
down_revision: str | None = "20261005_0048"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('orders',sa.Column('cost_currency',sa.String(3)),schema='sales')
    op.add_column('orders',sa.Column('cost_exchange_rate',sa.Numeric(24,12)),schema='sales')
    op.create_check_constraint('ck_sales_order_cost_currency','orders',"(cost_currency is null and cost_exchange_rate is null) or (division_ref_id is not null and cost_currency is not null and cost_exchange_rate is not null and cost_currency ~ '^[A-Z]{3}$' and cost_exchange_rate>0)",schema='sales')
    op.add_column('delivery_lines',sa.Column('original_actual_cost',sa.Numeric(18,2)),schema='sales')
    op.create_check_constraint('ck_sales_delivery_original_cost','delivery_lines','original_actual_cost is null or original_actual_cost>=0',schema='sales')

def downgrade():
    op.execute('LOCK TABLE sales.orders, sales.delivery_lines IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM sales.orders WHERE cost_currency IS NOT NULL) OR EXISTS (SELECT 1 FROM sales.delivery_lines WHERE original_actual_cost IS NOT NULL) THEN RAISE EXCEPTION 'Cost currency history exists; use forward-fix'; END IF; END $$""")
    op.drop_constraint('ck_sales_delivery_original_cost','delivery_lines',type_='check',schema='sales')
    op.drop_column('delivery_lines','original_actual_cost',schema='sales')
    op.drop_constraint('ck_sales_order_cost_currency','orders',type_='check',schema='sales')
    op.drop_column('orders','cost_exchange_rate',schema='sales')
    op.drop_column('orders','cost_currency',schema='sales')
