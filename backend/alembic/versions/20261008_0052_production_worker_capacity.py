"""Physical worker commitments owned by Production; no inferred legacy allocation."""
from alembic import op
import sqlalchemy as sa
revision: str = "20261008_0052"
down_revision: str | None ='20261007_0051'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('labor_worker_commitments',
        sa.Column('id',sa.String(40),primary_key=True),sa.Column('tenant_id',sa.String(40),nullable=False),
        sa.Column('production_order_id',sa.String(40),nullable=False),sa.Column('labor_position_ref_id',sa.String(40),nullable=False),
        sa.Column('worker_ref_id',sa.String(40),nullable=False),sa.Column('planned_date',sa.Date(),nullable=False),
        sa.Column('quantity_minutes',sa.Numeric(18,6),nullable=False),sa.Column('status',sa.String(16),nullable=False,server_default='active'),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id','production_order_id'],['production.production_orders.tenant_id','production.production_orders.id'],name='fk_labor_worker_commitment_order',ondelete='RESTRICT'),
        sa.CheckConstraint("quantity_minutes>0 and quantity_minutes != 'NaN'::numeric",name='ck_labor_worker_commitment_minutes'),
        sa.CheckConstraint("status in ('active','completed','released')",name='ck_labor_worker_commitment_status'),
        sa.UniqueConstraint('tenant_id','production_order_id','labor_position_ref_id','worker_ref_id','planned_date',name='uq_labor_worker_commitment_allocation'),schema='production')
    op.create_index('ix_labor_worker_commitment_worker_day','labor_worker_commitments',['tenant_id','worker_ref_id','planned_date','status'],schema='production')
    op.create_index('ix_labor_worker_commitment_order','labor_worker_commitments',['tenant_id','production_order_id'],schema='production')

def downgrade():
    op.execute('LOCK TABLE production.labor_worker_commitments IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM production.labor_worker_commitments) THEN RAISE EXCEPTION 'Worker capacity history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('labor_worker_commitments',schema='production')
