"""Harden Sales orchestration, mappings and actual-cost provenance.

Revision ID: 20260818_0020
Revises: 20260818_0019
"""
from alembic import op
import sqlalchemy as sa


revision: str = "20260818_0020"
down_revision: str | None = "20260818_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_services", sa.Column("inventory_item_ref_id", sa.String(40)), schema="production")
    op.create_index(
        "uq_production_product_inventory_mapping",
        "product_services",
        ["tenant_id", "inventory_item_ref_id"],
        unique=True,
        schema="production",
        postgresql_where=sa.text("inventory_item_ref_id is not null"),
    )

    op.add_column("order_lines", sa.Column("inventory_item_code_snapshot", sa.String(80)), schema="sales")
    op.add_column("order_lines", sa.Column("inventory_item_name_snapshot", sa.String(240)), schema="sales")
    for column in ("fulfillment", "cancellation"):
        op.add_column("orders", sa.Column(f"{column}_state", sa.String(24), nullable=False, server_default="idle"), schema="sales")
        op.add_column("orders", sa.Column(f"{column}_key", sa.String(200)), schema="sales")
        op.add_column("orders", sa.Column(f"{column}_hash", sa.String(64)), schema="sales")
        op.create_check_constraint(
            f"ck_sales_order_{column}_state",
            "orders",
            f"{column}_state in ('idle','processing','completed','needs_reconciliation')",
            schema="sales",
        )

    op.add_column("deliveries", sa.Column("confirmation_state", sa.String(24), nullable=False, server_default="idle"), schema="sales")
    op.add_column("deliveries", sa.Column("confirmation_key", sa.String(200)), schema="sales")
    op.add_column("deliveries", sa.Column("confirmation_hash", sa.String(64)), schema="sales")
    op.create_check_constraint(
        "ck_sales_delivery_confirmation_state",
        "deliveries",
        "confirmation_state in ('idle','processing','completed','needs_reconciliation')",
        schema="sales",
    )
    op.add_column("delivery_lines", sa.Column("actual_cost_source", sa.String(32)), schema="sales")
    op.create_check_constraint(
        "ck_sales_delivery_cost_source",
        "delivery_lines",
        "actual_cost_source is null or actual_cost_source in ('inventory_consumption','service_capture','production_report')",
        schema="sales",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sales_delivery_cost_source", "delivery_lines", schema="sales", type_="check")
    op.drop_column("delivery_lines", "actual_cost_source", schema="sales")
    op.drop_constraint("ck_sales_delivery_confirmation_state", "deliveries", schema="sales", type_="check")
    op.drop_column("deliveries", "confirmation_hash", schema="sales")
    op.drop_column("deliveries", "confirmation_key", schema="sales")
    op.drop_column("deliveries", "confirmation_state", schema="sales")
    for column in ("cancellation", "fulfillment"):
        op.drop_constraint(f"ck_sales_order_{column}_state", "orders", schema="sales", type_="check")
        op.drop_column("orders", f"{column}_hash", schema="sales")
        op.drop_column("orders", f"{column}_key", schema="sales")
        op.drop_column("orders", f"{column}_state", schema="sales")
    op.drop_column("order_lines", "inventory_item_name_snapshot", schema="sales")
    op.drop_column("order_lines", "inventory_item_code_snapshot", schema="sales")
    op.drop_index("uq_production_product_inventory_mapping", table_name="product_services", schema="production")
    op.drop_column("product_services", "inventory_item_ref_id", schema="production")
