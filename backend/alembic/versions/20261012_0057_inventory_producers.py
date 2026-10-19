"""CC-14 producer proofs and frozen transfer destination. No historical backfill."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20261012_0057"
down_revision: str | None = "20261008_0056"
branch_labels = None
depends_on = None

SNAPSHOTS = (
    ('inventory', 'transfers', 'destination_context'),
    ('inventory', 'movements', 'monetary_snapshot'),
    ('maintenance', 'material_requests', 'organization_context'),
    ('purchasing', 'purchase_receipt_lines', 'inventory_context_snapshot'),
)


def upgrade():
    for schema, table, column in SNAPSHOTS:
        op.add_column(table, sa.Column(column, JSONB(), nullable=True), schema=schema)
        op.create_check_constraint('ck_cc14_' + column, table,
            f"{column} is null or jsonb_typeof({column})='object'", schema=schema)
    op.add_column('movements', sa.Column('source_line_id', sa.String(40), nullable=True), schema='inventory')
    op.create_index('uq_inventory_purchase_receipt_effect', 'movements',
        ['tenant_id', 'source_id', 'source_line_id'], unique=True, schema='inventory',
        postgresql_where=sa.text("source_type='purchase_receipt'"))
    op.create_index('ix_maintenance_material_context', 'material_requests',
        ['tenant_id', sa.text("(organization_context->>'division_ref_id')")], schema='maintenance')


def downgrade():
    # Dropping snapshots after physical effects would silently reinterpret history.
    for schema, table, column in SNAPSHOTS:
        op.execute(f'LOCK TABLE {schema}.{table} IN ACCESS EXCLUSIVE MODE')
        op.execute(f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM {schema}.{table} WHERE {column} IS NOT NULL) THEN RAISE EXCEPTION 'CC14 history exists; use forward-fix'; END IF; END $$")
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM inventory.movements WHERE source_line_id IS NOT NULL) THEN RAISE EXCEPTION 'CC14 source history exists; use forward-fix'; END IF; END $$")
    op.drop_index('ix_maintenance_material_context', table_name='material_requests', schema='maintenance')
    op.drop_index('uq_inventory_purchase_receipt_effect', table_name='movements', schema='inventory')
    op.drop_column('movements', 'source_line_id', schema='inventory')
    for schema, table, column in reversed(SNAPSHOTS):
        op.drop_constraint('ck_cc14_' + column, table, type_='check', schema=schema)
        op.drop_column(table, column, schema=schema)
