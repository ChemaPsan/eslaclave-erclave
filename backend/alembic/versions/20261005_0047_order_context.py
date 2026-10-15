"""Order context copied from approved quotes; no historical mapping."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20261005_0047"
down_revision: str | None = "20261005_0046"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('orders',sa.Column('division_ref_id',sa.String(40)),schema='sales')
    op.add_column('orders',sa.Column('society_ref_id',sa.String(40)),schema='sales')
    op.add_column('orders',sa.Column('quote_organization_revision',sa.Integer(),nullable=False,server_default='0'),schema='sales')
    op.add_column('orders',sa.Column('commercial_terms_snapshot',JSONB()),schema='sales')
    op.create_check_constraint('ck_sales_order_context','orders',"(division_ref_id is null and society_ref_id is null and commercial_terms_snapshot is null and quote_organization_revision=0) or (division_ref_id is not null and society_ref_id is not null and commercial_terms_snapshot is not null and quote_organization_revision>0)",schema='sales')
    op.create_index('ix_sales_order_context','orders',['tenant_id','division_ref_id','status'],schema='sales')

def downgrade():
    op.execute('LOCK TABLE sales.orders IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM sales.orders WHERE division_ref_id IS NOT NULL) OR EXISTS (SELECT 1 FROM sales.audit_events WHERE action='order.context') THEN RAISE EXCEPTION 'Order context history exists; use forward-fix'; END IF; END $$""")
    op.drop_index('ix_sales_order_context',table_name='orders',schema='sales')
    op.drop_constraint('ck_sales_order_context','orders',type_='check',schema='sales')
    for name in ['commercial_terms_snapshot','quote_organization_revision','society_ref_id','division_ref_id']:
        op.drop_column('orders',name,schema='sales')
