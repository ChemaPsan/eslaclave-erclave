"""Explicit physical receipt and service acceptance, preserving historical receipts."""
from alembic import op
import sqlalchemy as sa

revision: str = "20260908_0032"
down_revision: str | None = "20260908_0031"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_inventory_movement_tenant_id", "movements", ["tenant_id","id"], schema="inventory")
    op.create_table("transfers",
        sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),
        sa.Column("outgoing_movement_id",sa.String(40),nullable=False),sa.Column("destination_warehouse_id",sa.String(40),nullable=False),
        sa.Column("status",sa.String(32),nullable=False,server_default="in_transit"),
        sa.Column("received_quantity",sa.Numeric(18,6),nullable=False,server_default="0"),
        sa.Column("returned_quantity",sa.Numeric(18,6),nullable=False,server_default="0"),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('in_transit','partially_received','received','return_requested','returned')",name="ck_inventory_transfer_status"),
        sa.CheckConstraint("received_quantity>=0 and returned_quantity>=0",name="ck_inventory_transfer_quantities"),
        sa.ForeignKeyConstraint(["tenant_id","outgoing_movement_id"],["inventory.movements.tenant_id","inventory.movements.id"]),
        sa.ForeignKeyConstraint(["tenant_id","destination_warehouse_id"],["inventory.warehouses.tenant_id","inventory.warehouses.id"]),
        sa.UniqueConstraint("tenant_id","outgoing_movement_id",name="uq_inventory_transfer_outgoing"),schema="inventory")
    op.create_index("ix_inventory_transfer_pending","transfers",["tenant_id","status","created_at"],schema="inventory")
    op.drop_constraint("ck_purchasing_receipt_status", "purchase_receipts", schema="purchasing")
    op.create_check_constraint("ck_purchasing_receipt_status", "purchase_receipts", "status in ('pending_confirmation','processing','completed','needs_reconciliation')", schema="purchasing")
    op.add_column("purchase_receipt_lines", sa.Column("confirmed_by_actor_id", sa.String(128)), schema="purchasing")
    op.add_column("purchase_receipt_lines", sa.Column("confirmed_at", sa.DateTime(timezone=True)), schema="purchasing")


def downgrade():
    if op.get_bind().execute(sa.text("select 1 from inventory.transfers limit 1")).first():
        raise RuntimeError("Transfer history requires this revision; preserve it before downgrade.")
    # Never turn pending physical goods/services into previously completed receipts.
    if op.get_bind().execute(sa.text("select 1 from purchasing.purchase_receipts where status='pending_confirmation' limit 1")).first():
        raise RuntimeError("Complete pending warehouse receipts and service acceptances before downgrade.")
    op.drop_column("purchase_receipt_lines", "confirmed_at", schema="purchasing")
    op.drop_column("purchase_receipt_lines", "confirmed_by_actor_id", schema="purchasing")
    op.drop_constraint("ck_purchasing_receipt_status", "purchase_receipts", schema="purchasing")
    op.create_check_constraint("ck_purchasing_receipt_status", "purchase_receipts", "status in ('processing','completed','needs_reconciliation')", schema="purchasing")
    op.drop_table("transfers",schema="inventory")
    op.drop_constraint("uq_inventory_movement_tenant_id","movements",schema="inventory")
