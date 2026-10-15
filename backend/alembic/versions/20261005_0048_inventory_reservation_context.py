"""Immutable organization snapshots for reservations and their stock effects."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20261005_0048"
down_revision: str | None = "20261005_0047"
branch_labels = None
depends_on = None

def upgrade():
    for table in ("reservations", "movements"):
        op.add_column(table, sa.Column("organization_context", JSONB()), schema="inventory")
        op.create_check_constraint("ck_inventory_" + table + "_context", table,
            "organization_context is null or (jsonb_typeof(organization_context)='object' and organization_context ?& array['division_ref_id','society_ref_id','division_code','division_name'] and coalesce(length(organization_context->>'division_ref_id'),0)>0 and coalesce(length(organization_context->>'society_ref_id'),0)>0)", schema="inventory")
        op.execute("CREATE INDEX ix_inventory_" + table + "_context ON inventory." + table + " (tenant_id, (organization_context->>'division_ref_id'))")

def downgrade():
    op.execute("LOCK TABLE inventory.reservations, inventory.movements IN ACCESS EXCLUSIVE MODE")
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM inventory.reservations WHERE organization_context IS NOT NULL) OR EXISTS (SELECT 1 FROM inventory.movements WHERE organization_context IS NOT NULL) THEN RAISE EXCEPTION 'Inventory context history exists; use forward-fix'; END IF; END $$""")
    for table in ("movements", "reservations"):
        op.drop_index("ix_inventory_" + table + "_context", table_name=table, schema="inventory")
        op.drop_constraint("ck_inventory_" + table + "_context", table, type_="check", schema="inventory")
        op.drop_column(table, "organization_context", schema="inventory")
