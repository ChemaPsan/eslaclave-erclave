"""Confirm resource tariff currency without reinterpreting historical costs."""
from alembic import op
import sqlalchemy as sa

revision: str = "20261007_0051"
down_revision: str | None = "20261007_0050"
branch_labels = None
depends_on = None

HR_CHECK = """(hourly_cost_currency_code IS NULL AND hourly_cost_society_ref_id IS NULL AND hourly_cost_confirmed_at IS NULL) OR (hourly_cost_currency_code IS NOT NULL AND hourly_cost_society_ref_id IS NOT NULL AND hourly_cost_confirmed_at IS NOT NULL AND hourly_cost_currency_code ~ '^[A-Z]{3}$' AND length(hourly_cost_society_ref_id)>0)"""
MACHINE_CHECK = """(cost_currency IS NULL AND cost_society_ref_id IS NULL AND cost_confirmed_at IS NULL) OR (cost_currency IS NOT NULL AND cost_society_ref_id IS NOT NULL AND cost_confirmed_at IS NOT NULL AND cost_currency ~ '^[A-Z]{3}$' AND length(cost_society_ref_id)>0 AND division_ref_id IS NOT NULL)"""


def upgrade():
    op.add_column('position_division_assignments', sa.Column('hourly_cost_currency_code', sa.String(3)), schema='hr')
    op.add_column('position_division_assignments', sa.Column('hourly_cost_society_ref_id', sa.String(40)), schema='hr')
    op.add_column('position_division_assignments', sa.Column('hourly_cost_confirmed_at', sa.DateTime(timezone=True)), schema='hr')
    op.create_check_constraint('ck_hr_position_assignment_currency', 'position_division_assignments', HR_CHECK, schema='hr')
    op.add_column('machines', sa.Column('cost_currency', sa.String(3)), schema='production')
    op.add_column('machines', sa.Column('cost_society_ref_id', sa.String(40)), schema='production')
    op.add_column('machines', sa.Column('cost_confirmed_at', sa.DateTime(timezone=True)), schema='production')
    op.create_check_constraint('ck_production_machine_cost_currency', 'machines', MACHINE_CHECK, schema='production')


def downgrade():
    # A rollback may never erase a confirmed monetary identity, including audit history.
    op.execute('LOCK TABLE hr.position_division_assignments, hr.audit_events, production.machines, production.audit_events IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM hr.position_division_assignments WHERE hourly_cost_currency_code IS NOT NULL)
         OR EXISTS (SELECT 1 FROM production.machines WHERE cost_currency IS NOT NULL)
         OR EXISTS (SELECT 1 FROM hr.audit_events WHERE payload->'after'->>'hourly_cost_currency_code' IS NOT NULL OR payload->'before'->>'hourly_cost_currency_code' IS NOT NULL)
         OR EXISTS (SELECT 1 FROM production.audit_events WHERE after_state->>'cost_currency' IS NOT NULL OR before_state->>'cost_currency' IS NOT NULL)
      THEN RAISE EXCEPTION 'Confirmed tariff currency history exists; use forward-fix'; END IF;
    END $$""")
    op.drop_constraint('ck_production_machine_cost_currency', 'machines', type_='check', schema='production')
    for name in ('cost_confirmed_at','cost_society_ref_id','cost_currency'):
        op.drop_column('machines', name, schema='production')
    op.drop_constraint('ck_hr_position_assignment_currency', 'position_division_assignments', type_='check', schema='hr')
    for name in ('hourly_cost_confirmed_at','hourly_cost_society_ref_id','hourly_cost_currency_code'):
        op.drop_column('position_division_assignments', name, schema='hr')
