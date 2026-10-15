"""HR-owned organization expansion; external IDs have no cross-schema FKs."""
from sqlalchemy import (
    MetaData, Table, Column, String, Integer, Numeric, DateTime,
    UniqueConstraint, CheckConstraint, ForeignKeyConstraint, Index, text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(schema='hr')
roles = Table(
    'labor_roles', metadata,
    Column('id', String(40), primary_key=True),
    Column('tenant_id', String(40), nullable=False),
    UniqueConstraint('tenant_id', 'id', name='uq_hr_labor_role_tenant_id'),
)
workers = Table(
    'workers', metadata,
    Column('id', String(40), primary_key=True),
    Column('tenant_id', String(40), nullable=False),
    UniqueConstraint('tenant_id', 'id', name='uq_hr_worker_tenant_id'),
)
position_assignments = Table(
    'position_division_assignments', metadata,
    Column('tenant_id', String(40), primary_key=True),
    Column('position_id', String(40), primary_key=True),
    Column('division_ref_id', String(40), primary_key=True),
    Column('status', String(16), nullable=False),
    Column('revision', Integer(), nullable=False),
    Column('created_at', DateTime(timezone=True), nullable=False, server_default=text('now()')),
    Column('updated_at', DateTime(timezone=True), nullable=False, server_default=text('now()')),
    Column('hourly_cost', Numeric(18, 6), nullable=False),
    Column('hourly_cost_currency_code', String(3)),
    Column('hourly_cost_society_ref_id', String(40)),
    Column('hourly_cost_confirmed_at', DateTime(timezone=True)),
    Column('cost_center_ref_id', String(40)),
    Column('cost_center_snapshot', JSONB),
    ForeignKeyConstraint(
        ['tenant_id', 'position_id'], ['hr.labor_roles.tenant_id', 'hr.labor_roles.id'],
        name='fk_hr_position_assignment_resource', ondelete='RESTRICT',
    ),
    CheckConstraint("status in ('active','inactive') and revision>0", name='ck_hr_position_assignment_state'),
    CheckConstraint('hourly_cost>=0 and hourly_cost<1000000000000', name='ck_hr_position_assignment_cost'),
    CheckConstraint(
        "(hourly_cost_currency_code IS NULL AND hourly_cost_society_ref_id IS NULL AND hourly_cost_confirmed_at IS NULL) OR (hourly_cost_currency_code IS NOT NULL AND hourly_cost_society_ref_id IS NOT NULL AND hourly_cost_confirmed_at IS NOT NULL AND hourly_cost_currency_code ~ '^[A-Z]{3}$' AND length(hourly_cost_society_ref_id)>0)",
        name='ck_hr_position_assignment_currency',
    ),
    Index('ix_hr_position_assignment_division', 'tenant_id', 'division_ref_id', 'status'),
)
worker_assignments = Table(
    'worker_division_assignments', metadata,
    Column('tenant_id', String(40), primary_key=True),
    Column('worker_id', String(40), primary_key=True),
    Column('division_ref_id', String(40), primary_key=True),
    Column('status', String(16), nullable=False),
    Column('revision', Integer(), nullable=False),
    Column('created_at', DateTime(timezone=True), nullable=False, server_default=text('now()')),
    Column('updated_at', DateTime(timezone=True), nullable=False, server_default=text('now()')),
    Column('labor_position_id', String(40), nullable=False),
    ForeignKeyConstraint(
        ['tenant_id', 'worker_id'], ['hr.workers.tenant_id', 'hr.workers.id'],
        name='fk_hr_worker_assignment_resource', ondelete='RESTRICT',
    ),
    ForeignKeyConstraint(
        ['tenant_id', 'labor_position_id'], ['hr.labor_roles.tenant_id', 'hr.labor_roles.id'],
        name='fk_hr_worker_assignment_position', ondelete='RESTRICT',
    ),
    CheckConstraint("status in ('active','inactive') and revision>0", name='ck_hr_worker_assignment_state'),
    Index('ix_hr_worker_assignment_division', 'tenant_id', 'division_ref_id', 'status'),
)
