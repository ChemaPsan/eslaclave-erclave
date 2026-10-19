"""Production-owned context and durable reservation preparation; no backfill."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20261007_0050"
down_revision: str | None = "20261005_0049"
branch_labels = None
depends_on = None

CONTEXT_CHECK = "organization_context is null or (jsonb_typeof(organization_context)='object' and organization_context ?& array['division_ref_id','society_ref_id','division_code','division_name','cost_currency'] and length(organization_context->>'division_ref_id')>0 and length(organization_context->>'society_ref_id')>0 and (organization_context->>'cost_currency') ~ '^[A-Z]{3}$') is true"

def upgrade():
    for table in ('production_orders','sales_order_requests'):
        op.add_column(table,sa.Column('organization_context',JSONB),schema='production')
        op.create_check_constraint('ck_'+table+'_context',table,CONTEXT_CHECK,schema='production')
        op.create_index('ix_'+table+'_division',table,['tenant_id',sa.text("(organization_context->>'division_ref_id')")],schema='production')
    op.create_table('order_creation_contexts',
        sa.Column('tenant_id',sa.String(40),primary_key=True),
        sa.Column('order_id',sa.String(40),primary_key=True),
        sa.Column('actor_id',sa.String(128),nullable=False),
        sa.Column('request_hash',sa.String(64),nullable=False),
        sa.Column('organization_context',JSONB,nullable=False),
        sa.Column('allocations',JSONB,nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.text('now()'),nullable=False),
        sa.CheckConstraint(CONTEXT_CHECK,name='ck_creation_context'),
        sa.CheckConstraint("jsonb_typeof(allocations)='array'",name='ck_creation_allocations'),schema='production')

def downgrade():
    op.execute('LOCK TABLE production.production_orders,production.sales_order_requests,production.order_creation_contexts IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM production.production_orders WHERE organization_context IS NOT NULL) OR EXISTS(SELECT 1 FROM production.sales_order_requests WHERE organization_context IS NOT NULL) OR EXISTS(SELECT 1 FROM production.order_creation_contexts) THEN RAISE EXCEPTION 'Production context history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('order_creation_contexts',schema='production')
    for table in ('production_orders','sales_order_requests'):
        op.drop_index('ix_'+table+'_division',table_name=table,schema='production')
        op.drop_constraint('ck_'+table+'_context',table,type_='check',schema='production')
        op.drop_column(table,'organization_context',schema='production')
