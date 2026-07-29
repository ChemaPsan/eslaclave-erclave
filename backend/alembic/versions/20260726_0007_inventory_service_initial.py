"""inventory service MVP.

Revision ID: 20260726_0007
Revises: 20260721_0006
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260726_0007"
down_revision: str | None = "20260721_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("create schema if not exists inventory")
    op.create_table("warehouses",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False), sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(40), nullable=False), sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("business_center", sa.String(160), nullable=False), sa.Column("location", sa.String(240), nullable=False),
        sa.Column("owner", sa.String(160), nullable=False), sa.Column("capacity", sa.String(80)),
        sa.Column("inventory_policy", sa.String(20), nullable=False, server_default="standard"),
        sa.Column("zone", sa.String(80)), sa.Column("aisle", sa.String(80)), sa.Column("rack", sa.String(80)), sa.Column("level", sa.String(80)), sa.Column("position", sa.String(80)),
        sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_inventory_warehouse_code"),
        sa.CheckConstraint("status in ('active','inactive','blocked')", name="ck_inventory_warehouse_status"), schema="inventory")
    op.create_index("ix_inventory_warehouses_tenant_status", "warehouses", ["tenant_id", "status"], schema="inventory")
    op.create_table("items",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False), sa.Column("name", sa.String(240), nullable=False),
        sa.Column("type", sa.String(40), nullable=False), sa.Column("category", sa.String(120)),
        sa.Column("base_unit", sa.String(40), nullable=False), sa.Column("inventory_policy", sa.String(20), nullable=False, server_default="standard"),
        sa.Column("suggested_warehouse_id", sa.String(40)), sa.Column("minimum_stock", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("maximum_stock", sa.Numeric(18, 6)), sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("description", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_inventory_item_code"),
        sa.CheckConstraint("inventory_policy in ('standard','lot','serial','restricted')", name="ck_inventory_item_policy"),
        sa.CheckConstraint("status in ('active','inactive','blocked')", name="ck_inventory_item_status"),
        sa.ForeignKeyConstraint(["suggested_warehouse_id"], ["inventory.warehouses.id"], name="fk_inventory_item_warehouse"), schema="inventory")
    op.create_index("ix_inventory_items_tenant_status", "items", ["tenant_id", "status"], schema="inventory")
    op.create_table("movements",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("movement_code", sa.String(80), nullable=False), sa.Column("movement_type", sa.String(40), nullable=False),
        sa.Column("inventory_item_id", sa.String(40), nullable=False), sa.Column("warehouse_id", sa.String(40), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False), sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False), sa.Column("unit_cost", sa.Numeric(18, 6)),
        sa.Column("reason", sa.Text(), nullable=False), sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_id", sa.String(120), nullable=False), sa.Column("transfer_group_id", sa.String(40)),
        sa.Column("reversal_of_id", sa.String(40)), sa.Column("status", sa.String(20), nullable=False, server_default="recorded"),
        sa.Column("actor_id", sa.String(80), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "movement_code", name="uq_inventory_movement_code"),
        sa.CheckConstraint("direction in ('in','out')", name="ck_inventory_movement_direction"),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_movement_quantity"),
        sa.CheckConstraint("status in ('recorded','reversed')", name="ck_inventory_movement_status"),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory.items.id"], name="fk_inventory_movement_item"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["inventory.warehouses.id"], name="fk_inventory_movement_warehouse"), schema="inventory")
    op.create_index("ix_inventory_movements_kardex", "movements", ["tenant_id", "inventory_item_id", "warehouse_id", "occurred_at"], schema="inventory")
    op.create_table("idempotency_records",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("operation", sa.String(120), nullable=False), sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False), sa.Column("response_payload", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_inventory_idempotency_scope"), schema="inventory")
    op.create_table("audit_events",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False), sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False), sa.Column("entity_id", sa.String(40), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), schema="inventory")
    op.create_index("ix_inventory_audit_tenant_created", "audit_events", ["tenant_id", "created_at"], schema="inventory")


def downgrade() -> None:
    op.drop_table("audit_events", schema="inventory")
    op.drop_table("idempotency_records", schema="inventory")
    op.drop_table("movements", schema="inventory")
    op.drop_table("items", schema="inventory")
    op.drop_table("warehouses", schema="inventory")
    op.execute("drop schema if exists inventory")
