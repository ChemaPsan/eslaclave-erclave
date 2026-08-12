"""Inventory balance search indexes.

Revision ID: 20260727_0008
Revises: 20260726_0007
"""
from alembic import op

revision: str = "20260727_0008"
down_revision: str | None = "20260726_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pg_trgm is an instance capability and may be shared by other schemas. We
    # enable it idempotently, but deliberately do not remove it on downgrade.
    op.execute("create extension if not exists pg_trgm")
    op.execute("""
        create or replace function inventory.search_normalize(value text)
        returns text language sql immutable parallel safe as $$
          select translate(lower(coalesce(value, '')), 'áéíóúüñ', 'aeiouun')
        $$
    """)
    op.create_index("ix_inventory_items_tenant_category", "items", ["tenant_id", "category"], schema="inventory")
    op.create_index("ix_inventory_items_tenant_type_status", "items", ["tenant_id", "type", "status"], schema="inventory")
    op.create_index("ix_inventory_movements_balance", "movements", ["tenant_id", "status", "inventory_item_id", "warehouse_id", "unit"], schema="inventory")
    op.execute("create index ix_inventory_items_search_trgm on inventory.items using gin (inventory.search_normalize(code||' '||name||' '||coalesce(category,'')) gin_trgm_ops)")
    op.execute("create index ix_inventory_warehouses_search_trgm on inventory.warehouses using gin (inventory.search_normalize(code||' '||name) gin_trgm_ops)")


def downgrade() -> None:
    op.execute("drop index if exists inventory.ix_inventory_warehouses_search_trgm")
    op.execute("drop index if exists inventory.ix_inventory_items_search_trgm")
    op.drop_index("ix_inventory_movements_balance", table_name="movements", schema="inventory")
    op.drop_index("ix_inventory_items_tenant_type_status", table_name="items", schema="inventory")
    op.drop_index("ix_inventory_items_tenant_category", table_name="items", schema="inventory")
    op.execute("drop function if exists inventory.search_normalize(text)")
