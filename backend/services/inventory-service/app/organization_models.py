"""Inventory-owned dimension assignments; external IDs have no cross-schema FKs."""
from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime, CheckConstraint, UniqueConstraint, ForeignKeyConstraint, Index, text
from sqlalchemy.dialects.postgresql import JSONB
metadata = MetaData(schema='inventory')
items = Table('items', metadata, Column('tenant_id', String(40), nullable=False), Column('id', String(40), primary_key=True), UniqueConstraint('tenant_id', 'id', name='uq_inventory_items_tenant_id'))
warehouses = Table('warehouses', metadata, Column('id', String(40), primary_key=True), Column('tenant_id', String(40), nullable=False), Column('division_ref_id', String(40)), Column('division_revision', Integer, nullable=False, server_default='0'), CheckConstraint('(division_ref_id is null and division_revision=0) or (division_ref_id is not null and division_revision>0)', name='ck_inventory_warehouse_division'), Index('ix_inventory_warehouse_division', 'tenant_id', 'division_ref_id'))
assignments = Table('item_division_assignments', metadata, Column('tenant_id', String(40), primary_key=True), Column('item_id', String(40), primary_key=True), Column('division_ref_id', String(40), primary_key=True), Column('cost_center_ref_id', String(40)), Column('cost_center_snapshot', JSONB), Column('status', String(16), nullable=False), Column('revision', Integer, nullable=False), Column('created_at', DateTime(timezone=True), nullable=False, server_default=text('now()')), Column('updated_at', DateTime(timezone=True), nullable=False, server_default=text('now()')), ForeignKeyConstraint(['tenant_id', 'item_id'], ['inventory.items.tenant_id', 'inventory.items.id'], name='fk_inventory_assignment_item', ondelete='RESTRICT'), CheckConstraint("status in ('active','inactive') and revision>0", name='ck_inventory_assignment_state'), Index('ix_inventory_assignment_division', 'tenant_id', 'division_ref_id', 'status'))

# Operational context expansion; full transaction schemas remain migration-owned.
for table_name in ("reservations", "movements"):
    Table(table_name, metadata, Column("id", String(40), primary_key=True), Column("tenant_id", String(40), nullable=False), Column("organization_context", JSONB()))

metadata.tables['inventory.movements'].append_column(Column('source_line_id', String(40)))
metadata.tables['inventory.movements'].append_column(Column('source_id', String(40)))
metadata.tables['inventory.movements'].append_column(Column('source_type', String(40)))
metadata.tables['inventory.movements'].append_column(Column('monetary_snapshot', JSONB()))
Index('uq_inventory_purchase_receipt_effect', metadata.tables['inventory.movements'].c.tenant_id,
      metadata.tables['inventory.movements'].c.source_id, metadata.tables['inventory.movements'].c.source_line_id, unique=True,
      postgresql_where=text("source_type='purchase_receipt'"))
Table('transfers', metadata, Column('id', String(40), primary_key=True),
      Column('tenant_id', String(40), nullable=False), Column('destination_context', JSONB()))
