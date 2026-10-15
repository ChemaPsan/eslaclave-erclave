"""Production dimension expansion; no inferred backfill or transaction enforcement."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20260927_0042"
down_revision: str | None = "20260927_0041"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('machines',sa.Column('division_ref_id',sa.String(40)),schema='production')
    op.add_column('machines',sa.Column('division_revision',sa.Integer(),nullable=False,server_default='0'),schema='production')
    op.create_check_constraint('ck_production_machine_division','machines','(division_ref_id is null and division_revision=0) or (division_ref_id is not null and division_revision>0)',schema='production')
    op.create_index('ix_production_machine_division','machines',['tenant_id','division_ref_id'],schema='production')
    op.create_unique_constraint('uq_production_product_services_tenant_id','product_services',['tenant_id','id'],schema='production')
    op.create_table('product_service_division_assignments',
        sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('product_service_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),
        sa.Column('cost_center_ref_id',sa.String(40)),sa.Column('cost_center_snapshot',JSONB),sa.Column('status',sa.String(16),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id','product_service_id'],['production.product_services.tenant_id','production.product_services.id'],name='fk_production_assignment_product_service',ondelete='RESTRICT'),
        sa.CheckConstraint("status in ('active','inactive') and revision>0",name='ck_production_assignment_state'),schema='production')
    op.create_index('ix_production_assignment_division','product_service_division_assignments',['tenant_id','division_ref_id','status'],schema='production')

def downgrade():
    op.execute('LOCK TABLE production.machines,production.product_service_division_assignments IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM production.machines WHERE division_ref_id IS NOT NULL) OR EXISTS (SELECT 1 FROM production.product_service_division_assignments) OR EXISTS (SELECT 1 FROM production.audit_events WHERE action LIKE 'organization_assignment.%') THEN RAISE EXCEPTION 'Production assignment history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('product_service_division_assignments',schema='production')
    op.drop_constraint('uq_production_product_services_tenant_id','product_services',schema='production')
    op.drop_index('ix_production_machine_division',table_name='machines',schema='production')
    op.drop_constraint('ck_production_machine_division','machines',schema='production')
    op.drop_column('machines','division_revision',schema='production');op.drop_column('machines','division_ref_id',schema='production')
