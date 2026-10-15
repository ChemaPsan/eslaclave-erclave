"""HR organization assignments; no inferred backfill or operational enforcement."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20260927_0043"
down_revision: str | None = "20260927_0042"
branch_labels = None
depends_on = None

def upgrade():
    op.create_unique_constraint('uq_hr_worker_tenant_id','workers',['tenant_id','id'],schema='hr')
    op.create_table('position_division_assignments',
        sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('position_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),
        sa.Column('status',sa.String(16),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id','position_id'],['hr.labor_roles.tenant_id','hr.labor_roles.id'],name='fk_hr_position_assignment_resource',ondelete='RESTRICT'),
        sa.CheckConstraint("status in ('active','inactive') and revision>0",name='ck_hr_position_assignment_state'),sa.Column('hourly_cost',sa.Numeric(18,6),nullable=False),sa.CheckConstraint("hourly_cost>=0 and hourly_cost<1000000000000",name='ck_hr_position_assignment_cost'),sa.Column('cost_center_ref_id',sa.String(40)),sa.Column('cost_center_snapshot',JSONB),schema='hr')
    op.create_index('ix_hr_position_assignment_division','position_division_assignments',['tenant_id','division_ref_id','status'],schema='hr')
    op.create_table('worker_division_assignments',
        sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('worker_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),
        sa.Column('status',sa.String(16),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id','worker_id'],['hr.workers.tenant_id','hr.workers.id'],name='fk_hr_worker_assignment_resource',ondelete='RESTRICT'),
        sa.CheckConstraint("status in ('active','inactive') and revision>0",name='ck_hr_worker_assignment_state'),sa.Column('labor_position_id',sa.String(40),nullable=False),sa.ForeignKeyConstraint(['tenant_id','labor_position_id'],['hr.labor_roles.tenant_id','hr.labor_roles.id'],name='fk_hr_worker_assignment_position',ondelete='RESTRICT'),schema='hr')
    op.create_index('ix_hr_worker_assignment_division','worker_division_assignments',['tenant_id','division_ref_id','status'],schema='hr')

def downgrade():
    op.execute('LOCK TABLE hr.position_division_assignments,hr.worker_division_assignments IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM hr.position_division_assignments) OR EXISTS (SELECT 1 FROM hr.worker_division_assignments) OR EXISTS (SELECT 1 FROM hr.audit_events WHERE action LIKE 'organization_assignment.%') THEN RAISE EXCEPTION 'HR assignment history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('worker_division_assignments',schema='hr')
    op.drop_table('position_division_assignments',schema='hr')
    op.drop_constraint('uq_hr_worker_tenant_id','workers',schema='hr')
