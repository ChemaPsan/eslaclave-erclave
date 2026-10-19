"""Inventory dimension expansion; no inferred backfill or transaction enforcement."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20260927_0041"
down_revision: str | None = "20260927_0040"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('warehouses',sa.Column('division_ref_id',sa.String(40)),schema='inventory')
    op.add_column('warehouses',sa.Column('division_revision',sa.Integer(),nullable=False,server_default='0'),schema='inventory')
    op.create_check_constraint('ck_inventory_warehouse_division','warehouses','(division_ref_id is null and division_revision=0) or (division_ref_id is not null and division_revision>0)',schema='inventory')
    op.create_index('ix_inventory_warehouse_division','warehouses',['tenant_id','division_ref_id'],schema='inventory')
    op.create_unique_constraint('uq_inventory_items_tenant_id','items',['tenant_id','id'],schema='inventory')
    op.create_table('item_division_assignments',
        sa.Column('tenant_id',sa.String(40),primary_key=True),sa.Column('item_id',sa.String(40),primary_key=True),sa.Column('division_ref_id',sa.String(40),primary_key=True),
        sa.Column('cost_center_ref_id',sa.String(40)),sa.Column('cost_center_snapshot',JSONB),sa.Column('status',sa.String(16),nullable=False),sa.Column('revision',sa.Integer(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False,server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id','item_id'],['inventory.items.tenant_id','inventory.items.id'],name='fk_inventory_assignment_item',ondelete='RESTRICT'),
        sa.CheckConstraint("status in ('active','inactive') and revision>0",name='ck_inventory_assignment_state'),schema='inventory')
    op.create_index('ix_inventory_assignment_division','item_division_assignments',['tenant_id','division_ref_id','status'],schema='inventory')

def downgrade():
    op.execute('LOCK TABLE inventory.warehouses,inventory.item_division_assignments IN ACCESS EXCLUSIVE MODE')
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM inventory.warehouses WHERE division_ref_id IS NOT NULL) OR EXISTS (SELECT 1 FROM inventory.item_division_assignments) OR EXISTS (SELECT 1 FROM inventory.audit_events WHERE action LIKE 'organization_assignment.%') THEN RAISE EXCEPTION 'Inventory assignment history exists; use forward-fix'; END IF; END $$""")
    op.drop_table('item_division_assignments',schema='inventory')
    op.drop_constraint('uq_inventory_items_tenant_id','items',schema='inventory')
    op.drop_index('ix_inventory_warehouse_division',table_name='warehouses',schema='inventory')
    op.drop_constraint('ck_inventory_warehouse_division','warehouses',schema='inventory')
    op.drop_column('warehouses','division_revision',schema='inventory');op.drop_column('warehouses','division_ref_id',schema='inventory')
