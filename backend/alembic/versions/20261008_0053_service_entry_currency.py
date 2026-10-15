"""Preserve original Society cost and explicit document conversion on service entries."""
from alembic import op
import sqlalchemy as sa
revision: str = "20261008_0053"
down_revision: str | None = "20261008_0052"
branch_labels = None
depends_on = None
TABLES = ("service_time_entries","service_cost_entries")
CHECK = "(cost_currency is null and document_currency is null and cost_exchange_rate is null and original_total_cost is null) or (cost_currency is not null and document_currency is not null and cost_exchange_rate is not null and original_total_cost is not null and cost_currency ~ '^[A-Z]{3}$' and document_currency ~ '^[A-Z]{3}$' and cost_exchange_rate > 0 and cost_exchange_rate != 'NaN'::numeric and original_total_cost >= 0 and original_total_cost != 'NaN'::numeric and (cost_currency <> document_currency or cost_exchange_rate = 1))"

def upgrade():
    for table in TABLES:
        op.add_column(table,sa.Column('cost_currency',sa.String(3)),schema='sales')
        op.add_column(table,sa.Column('document_currency',sa.String(3)),schema='sales')
        op.add_column(table,sa.Column('cost_exchange_rate',sa.Numeric(24,12)),schema='sales')
        op.add_column(table,sa.Column('original_total_cost',sa.Numeric(18,6)),schema='sales')
        op.create_check_constraint('ck_'+table+'_money',table,CHECK,schema='sales')

def downgrade():
    op.execute('LOCK TABLE sales.service_time_entries, sales.service_cost_entries, sales.audit_events IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM sales.service_time_entries WHERE cost_currency IS NOT NULL) OR EXISTS (SELECT 1 FROM sales.service_cost_entries WHERE cost_currency IS NOT NULL) OR EXISTS (SELECT 1 FROM sales.audit_events WHERE action LIKE 'service_order.%.create:%' AND payload->>'cost_currency' IS NOT NULL) THEN RAISE EXCEPTION 'Service cost currency history exists; use forward-fix'; END IF; END $$""")
    for table in reversed(TABLES):
        op.drop_constraint('ck_'+table+'_money',table,type_='check',schema='sales')
        for column in ('original_total_cost','cost_exchange_rate','document_currency','cost_currency'):
            op.drop_column(table,column,schema='sales')
