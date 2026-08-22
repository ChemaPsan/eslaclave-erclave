"""authoritative resources, reservations, capacity and operational costing.

Revision ID: 20260818_0017
Revises: 20260818_0016
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260818_0017"
down_revision: str | None = "20260818_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("items", sa.Column("default_unit_cost", sa.Numeric(18, 6), nullable=False, server_default="0"), schema="inventory")
    op.create_check_constraint("ck_inventory_item_default_unit_cost", "items", "default_unit_cost >= 0", schema="inventory")
    op.create_check_constraint("ck_inventory_item_stock_limits", "items", "maximum_stock is null or maximum_stock >= minimum_stock", schema="inventory")
    op.create_unique_constraint("uq_inventory_item_tenant_id", "items", ["tenant_id", "id"], schema="inventory")
    op.create_unique_constraint("uq_inventory_warehouse_tenant_id", "warehouses", ["tenant_id", "id"], schema="inventory")

    op.create_table(
        "reservations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("inventory_item_id", sa.String(40), nullable=False),
        sa.Column("warehouse_id", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("unit_cost_snapshot", sa.Numeric(18, 6), nullable=False),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("source_id", sa.String(120), nullable=False),
        sa.Column("source_line_id", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_reservation_quantity"),
        sa.CheckConstraint("unit_cost_snapshot >= 0", name="ck_inventory_reservation_cost"),
        sa.CheckConstraint("status in ('active','released','consumed','expired')", name="ck_inventory_reservation_status"),
        sa.UniqueConstraint("tenant_id", "source_type", "source_id", "source_line_id", "inventory_item_id", "warehouse_id", "unit", name="uq_inventory_reservation_source"),
        sa.ForeignKeyConstraint(["tenant_id", "inventory_item_id"], ["inventory.items.tenant_id", "inventory.items.id"], name="fk_inventory_reservation_item_tenant"),
        sa.ForeignKeyConstraint(["tenant_id", "warehouse_id"], ["inventory.warehouses.tenant_id", "inventory.warehouses.id"], name="fk_inventory_reservation_warehouse_tenant"),
        schema="inventory",
    )
    op.create_index("ix_inventory_reservations_available", "reservations", ["tenant_id", "inventory_item_id", "warehouse_id", "unit", "status", "expires_at"], schema="inventory")
    op.create_index("ix_inventory_reservations_source", "reservations", ["tenant_id", "source_type", "source_id", "status"], schema="inventory")

    op.add_column("machines", sa.Column("area_ref_id", sa.String(40)), schema="production")
    op.create_index("ix_production_machines_tenant_area", "machines", ["tenant_id", "area_ref_id", "status"], schema="production")

    op.create_table(
        "capacity_commitments",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("production_order_id", sa.String(40), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=False),
        sa.Column("resource_ref_id", sa.String(40), nullable=False),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("quantity_minutes", sa.Numeric(18, 6), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("resource_type in ('labor','machine')", name="ck_production_capacity_resource_type"),
        sa.CheckConstraint("quantity_minutes > 0", name="ck_production_capacity_quantity"),
        sa.CheckConstraint("status in ('active','released','completed')", name="ck_production_capacity_status"),
        sa.UniqueConstraint("tenant_id", "production_order_id", "resource_type", "resource_ref_id", name="uq_production_capacity_order_resource"),
        sa.ForeignKeyConstraint(["production_order_id"], ["production.production_orders.id"], name="fk_production_capacity_order", ondelete="CASCADE"),
        schema="production",
    )
    op.create_index("ix_production_capacity_available", "capacity_commitments", ["tenant_id", "resource_type", "resource_ref_id", "planned_date", "status"], schema="production")

    op.create_table(
        "production_order_resources",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("production_order_id", sa.String(40), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=False),
        sa.Column("resource_ref_id", sa.String(40), nullable=False),
        sa.Column("resource_code", sa.String(80), nullable=False),
        sa.Column("resource_name_snapshot", sa.String(240), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("planned_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("actual_quantity", sa.Numeric(18, 6)),
        sa.Column("unit_cost_snapshot", sa.Numeric(18, 6), nullable=False),
        sa.Column("planned_cost", sa.Numeric(18, 6), nullable=False),
        sa.Column("actual_cost", sa.Numeric(18, 6)),
        sa.Column("reservation_ref_id", sa.String(40)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("resource_type in ('material','labor','machine','other')", name="ck_production_order_resource_type"),
        sa.CheckConstraint("planned_quantity > 0", name="ck_production_order_resource_planned_quantity"),
        sa.CheckConstraint("actual_quantity is null or actual_quantity >= 0", name="ck_production_order_resource_actual_quantity"),
        sa.CheckConstraint("unit_cost_snapshot >= 0 and planned_cost >= 0 and (actual_cost is null or actual_cost >= 0)", name="ck_production_order_resource_costs"),
        sa.UniqueConstraint("tenant_id", "production_order_id", "resource_type", "resource_ref_id", "unit", name="uq_production_order_resource"),
        sa.ForeignKeyConstraint(["production_order_id"], ["production.production_orders.id"], name="fk_production_order_resource_order", ondelete="CASCADE"),
        schema="production",
    )
    op.create_index("ix_production_order_resources_order", "production_order_resources", ["tenant_id", "production_order_id", "resource_type"], schema="production")
    op.create_unique_constraint("uq_production_order_resource_tenant_id", "production_order_resources", ["tenant_id", "id"], schema="production")
    op.create_table(
        "production_order_resource_reservations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("production_order_resource_id", sa.String(40), nullable=False),
        sa.Column("reservation_ref_id", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "reservation_ref_id", name="uq_production_resource_reservation_ref"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "production_order_resource_id"],
            ["production.production_order_resources.tenant_id", "production.production_order_resources.id"],
            name="fk_production_resource_reservation_resource_tenant",
            ondelete="CASCADE",
        ),
        schema="production",
    )
    op.create_index("ix_production_resource_reservations_resource", "production_order_resource_reservations", ["tenant_id", "production_order_resource_id"], schema="production")


def downgrade() -> None:
    op.drop_index("ix_production_resource_reservations_resource", table_name="production_order_resource_reservations", schema="production")
    op.drop_table("production_order_resource_reservations", schema="production")
    op.drop_constraint("uq_production_order_resource_tenant_id", "production_order_resources", schema="production", type_="unique")
    op.drop_index("ix_production_order_resources_order", table_name="production_order_resources", schema="production")
    op.drop_table("production_order_resources", schema="production")
    op.drop_index("ix_production_capacity_available", table_name="capacity_commitments", schema="production")
    op.drop_table("capacity_commitments", schema="production")
    op.drop_index("ix_production_machines_tenant_area", table_name="machines", schema="production")
    op.drop_column("machines", "area_ref_id", schema="production")
    op.drop_index("ix_inventory_reservations_source", table_name="reservations", schema="inventory")
    op.drop_index("ix_inventory_reservations_available", table_name="reservations", schema="inventory")
    op.drop_table("reservations", schema="inventory")
    op.drop_constraint("uq_inventory_warehouse_tenant_id", "warehouses", schema="inventory", type_="unique")
    op.drop_constraint("uq_inventory_item_tenant_id", "items", schema="inventory", type_="unique")
    op.drop_constraint("ck_inventory_item_stock_limits", "items", schema="inventory", type_="check")
    op.drop_constraint("ck_inventory_item_default_unit_cost", "items", schema="inventory", type_="check")
    op.drop_column("items", "default_unit_cost", schema="inventory")
