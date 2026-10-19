"""Explicit commercial conditions per Division; no inheritance or backfill."""
from alembic import op
import sqlalchemy as sa
revision: str = "20260928_0045"
down_revision: str | None = "20260928_0044"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('customer_division_terms',sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('customer_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),sa.Column('society_ref_id',sa.String(40),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('currency',sa.String(12),nullable=False),sa.Column('payment_terms',sa.String(40),nullable=False),sa.Column('credit_limit',sa.Numeric(18,2),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.ForeignKeyConstraint(['tenant_id','customer_id','division_ref_id'],['sales.customer_division_assignments.tenant_id','sales.customer_division_assignments.customer_id','sales.customer_division_assignments.division_ref_id'],name='fk_sales_customer_terms',ondelete='RESTRICT'),sa.CheckConstraint("revision > 0 and currency ~ '^[A-Z0-9._-]{3,12}$' and payment_terms ~ '^[a-z0-9._-]{1,40}$' and credit_limit >= 0 and credit_limit <= 9999999999999999.99",name='ck_sales_customer_terms'),schema='sales')
    op.create_index('ix_sales_customer_terms_division','customer_division_terms',['tenant_id','division_ref_id'],schema='sales')
    op.create_table('supplier_division_terms',sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('supplier_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),sa.Column('society_ref_id',sa.String(40),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),sa.Column('currency',sa.String(12),nullable=False),sa.Column('payment_terms',sa.String(40),nullable=False),sa.Column('lead_time_days',sa.Integer(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.ForeignKeyConstraint(['tenant_id','supplier_id','division_ref_id'],['purchasing.supplier_division_assignments.tenant_id','purchasing.supplier_division_assignments.supplier_id','purchasing.supplier_division_assignments.division_ref_id'],name='fk_purchasing_supplier_terms',ondelete='RESTRICT'),sa.CheckConstraint("revision > 0 and currency ~ '^[A-Z0-9._-]{3,12}$' and payment_terms ~ '^[a-z0-9._-]{1,40}$' and lead_time_days between 0 and 3650",name='ck_purchasing_supplier_terms'),schema='purchasing')
    op.create_index('ix_purchasing_supplier_terms_division','supplier_division_terms',['tenant_id','division_ref_id'],schema='purchasing')

def downgrade():
    op.execute('LOCK TABLE sales.customer_division_terms,purchasing.supplier_division_terms IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM sales.customer_division_terms) OR EXISTS (SELECT 1 FROM purchasing.supplier_division_terms) OR EXISTS (SELECT 1 FROM sales.audit_events WHERE action='commercial_terms.customer') OR EXISTS (SELECT 1 FROM purchasing.audit_events WHERE action='commercial_terms.supplier') THEN RAISE EXCEPTION 'Commercial terms history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('supplier_division_terms',schema='purchasing')
    op.drop_table('customer_division_terms',schema='sales')
