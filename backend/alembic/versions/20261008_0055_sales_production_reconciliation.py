"""Durable Sales-owned reconciliation of received manufactured products."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20261008_0055"
down_revision: str | None = "20261008_0054"
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('orders',sa.Column('fulfillment_plan',JSONB()),schema='sales')
    op.create_table('production_reconciliations',
        sa.Column('tenant_id',sa.String(40),primary_key=True),
        sa.Column('order_line_id',sa.String(40),primary_key=True),
        sa.Column('order_id',sa.String(40),nullable=False),
        sa.Column('request_id',sa.String(40),nullable=False),
        sa.Column('production_order_id',sa.String(40),nullable=False),
        sa.Column('warehouse_id',sa.String(40),nullable=False),
        sa.Column('inventory_item_id',sa.String(40),nullable=False),
        sa.Column('quantity',sa.Numeric(18,6),nullable=False),
        sa.Column('unit',sa.String(40),nullable=False),
        sa.Column('command_key',sa.String(160),nullable=False),
        sa.Column('request_hash',sa.String(64),nullable=False),
        sa.Column('status',sa.String(32),nullable=False),
        sa.Column('source_snapshot',JSONB(),nullable=False),
        sa.Column('reservation_ref_id',sa.String(40)),
        sa.Column('error_code',sa.String(120)),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id','order_id'],['sales.orders.tenant_id','sales.orders.id'],name='fk_sales_production_reconcile_order',ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id','order_line_id'],['sales.order_lines.tenant_id','sales.order_lines.id'],name='fk_sales_production_reconcile_line',ondelete='RESTRICT'),
        sa.CheckConstraint("quantity>0 and quantity!='NaN'::numeric and status in ('processing','needs_reconciliation','completed') and jsonb_typeof(source_snapshot)='object' and (status!='completed' or reservation_ref_id is not null)",name='ck_sales_production_reconcile'),
        schema='sales')
    op.create_index('ix_sales_production_reconcile_order','production_reconciliations',['tenant_id','order_id','status'],schema='sales')


def downgrade():
    op.execute('LOCK TABLE sales.production_reconciliations IN ACCESS EXCLUSIVE MODE')
    op.execute("DO $$ BEGIN IF EXISTS(SELECT 1 FROM sales.production_reconciliations) OR EXISTS(SELECT 1 FROM sales.orders WHERE fulfillment_plan IS NOT NULL) THEN RAISE EXCEPTION 'Production reconciliation history exists; use forward-fix'; END IF; END $$")
    op.drop_index('ix_sales_production_reconcile_order',table_name='production_reconciliations',schema='sales')
    op.drop_table('production_reconciliations',schema='sales')
    op.drop_column('orders','fulfillment_plan',schema='sales')
