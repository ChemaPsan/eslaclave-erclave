"""Commercial master associations; no inferred backfill or document enforcement."""
from alembic import op
import sqlalchemy as sa
revision: str = "20260928_0044"
down_revision: str | None = "20260927_0043"
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('customer_division_assignments',sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('customer_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),sa.Column('society_ref_id',sa.String(40),nullable=False),sa.Column('status',sa.String(16),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.ForeignKeyConstraint(['tenant_id','customer_id'],['sales.customers.tenant_id','sales.customers.id'],name='fk_sales_customer_assignment',ondelete='RESTRICT'),sa.CheckConstraint("status in ('active','inactive') and revision>0",name='ck_sales_customer_assignment'),schema='sales')
    op.create_index('ix_sales_customer_assignment_division','customer_division_assignments',['tenant_id','division_ref_id','status'],schema='sales')
    op.create_table('supplier_division_assignments',sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('supplier_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),sa.Column('society_ref_id',sa.String(40),nullable=False),sa.Column('status',sa.String(16),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.ForeignKeyConstraint(['tenant_id','supplier_id'],['purchasing.suppliers.tenant_id','purchasing.suppliers.id'],name='fk_purchasing_supplier_assignment',ondelete='RESTRICT'),sa.CheckConstraint("status in ('active','inactive') and revision>0",name='ck_purchasing_supplier_assignment'),schema='purchasing')
    op.create_index('ix_purchasing_supplier_assignment_division','supplier_division_assignments',['tenant_id','division_ref_id','status'],schema='purchasing')

def downgrade():
    op.execute('LOCK TABLE sales.customer_division_assignments,purchasing.supplier_division_assignments IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM sales.customer_division_assignments) OR EXISTS (SELECT 1 FROM purchasing.supplier_division_assignments) OR EXISTS (SELECT 1 FROM sales.audit_events WHERE action='organization_assignment.customer') OR EXISTS (SELECT 1 FROM purchasing.audit_events WHERE action='organization_assignment.supplier') THEN RAISE EXCEPTION 'Commercial assignment history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('supplier_division_assignments',schema='purchasing')
    op.drop_table('customer_division_assignments',schema='sales')
