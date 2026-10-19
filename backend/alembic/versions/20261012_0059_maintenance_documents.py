"""CC16 Maintenance context, technician and monetary time snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20261012_0059"
down_revision: str | None = "20261012_0058"
branch_labels=None
depends_on=None
SNAPSHOTS=(('orders','organization_context'),('assignments','worker_context_snapshot'),('time_entries','organization_context'),('time_entries','labor_cost_snapshot'))

def upgrade():
    for table,column in SNAPSHOTS:
        op.add_column(table,sa.Column(column,JSONB(),nullable=True),schema='maintenance')
        op.create_check_constraint(f'ck_cc16_{table}_{column}',table,f"{column} is null or jsonb_typeof({column})='object'",schema='maintenance')
    op.create_index('ix_cc16_orders_division','orders',['tenant_id',sa.text("(organization_context->>'division_ref_id')")],schema='maintenance')
    op.create_index('ix_cc16_time_worker_interval','time_entries',['tenant_id','worker_ref_id','started_at','ended_at'],schema='maintenance')

def downgrade():
    for table in ('orders','assignments','time_entries'):op.execute(f'LOCK TABLE maintenance.{table} IN ACCESS EXCLUSIVE MODE')
    for table,column in SNAPSHOTS:op.execute(f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM maintenance.{table} WHERE {column} IS NOT NULL) THEN RAISE EXCEPTION 'CC16 history exists; use forward-fix'; END IF; END $$")
    op.drop_index('ix_cc16_time_worker_interval',table_name='time_entries',schema='maintenance')
    op.drop_index('ix_cc16_orders_division',table_name='orders',schema='maintenance')
    for table,column in reversed(SNAPSHOTS):
        op.drop_constraint(f'ck_cc16_{table}_{column}',table,type_='check',schema='maintenance')
        op.drop_column(table,column,schema='maintenance')
