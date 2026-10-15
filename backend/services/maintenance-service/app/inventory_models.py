"""Maintenance-owned CC-14 persistence extension, migration 0057."""
from sqlalchemy import MetaData, Table, Column, String, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(schema='maintenance')
material_requests = Table(
    'material_requests', metadata,
    Column('id', String(40), primary_key=True),
    Column('tenant_id', String(40), nullable=False),
    Column('organization_context', JSONB, nullable=True),
    CheckConstraint("organization_context is null or jsonb_typeof(organization_context)='object'", name='ck_cc14_organization_context'),
    Index('ix_maintenance_material_context', 'tenant_id', text("(organization_context->>'division_ref_id')")),
)
