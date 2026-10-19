"""Authentic Sales source and unique request/order conversion; no historical inference."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20261008_0054"
down_revision: str | None = "20261008_0053"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('sales_order_requests',sa.Column('production_order_ref_id',sa.String(40)),schema='production')
    op.add_column('sales_order_requests',sa.Column('creation_attempt_ref_id',sa.String(40)),schema='production')
    op.add_column('sales_order_requests',sa.Column('source_snapshot',JSONB),schema='production')
    op.create_unique_constraint('uq_sales_request_production_order','sales_order_requests',['tenant_id','production_order_ref_id'],schema='production')
    op.create_foreign_key('fk_sales_request_production_order','sales_order_requests','production_orders',['tenant_id','production_order_ref_id'],['tenant_id','id'],source_schema='production',referent_schema='production',ondelete='RESTRICT')
    op.create_check_constraint('ck_sales_request_source_snapshot','sales_order_requests',"source_snapshot is null or jsonb_typeof(source_snapshot)='object'",schema='production')

def downgrade():
    op.execute('LOCK TABLE production.sales_order_requests IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM production.sales_order_requests WHERE source_snapshot IS NOT NULL OR production_order_ref_id IS NOT NULL OR creation_attempt_ref_id IS NOT NULL) OR EXISTS(SELECT 1 FROM production.audit_events WHERE after_state->>'production_order_ref_id' IS NOT NULL OR action='sales_order_request.cancel') THEN RAISE EXCEPTION 'Sales conversion history exists; use forward-fix'; END IF; END $$""")
    op.drop_constraint('ck_sales_request_source_snapshot','sales_order_requests',schema='production')
    op.drop_constraint('fk_sales_request_production_order','sales_order_requests',schema='production')
    op.drop_constraint('uq_sales_request_production_order','sales_order_requests',schema='production')
    for name in ('source_snapshot','creation_attempt_ref_id','production_order_ref_id'):
        op.drop_column('sales_order_requests',name,schema='production')
