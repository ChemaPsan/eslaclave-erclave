"""purchasing source-to-receipt hardening.

Revision ID: 20260824_0026
Revises: 20260824_0025
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260824_0026"
down_revision: str | None = "20260824_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("requisitions", "purchase_orders"):
        op.add_column(table, sa.Column("cancellation_reason", sa.String(500)), schema="purchasing")
        op.add_column(table, sa.Column("cancelled_by_actor_id", sa.String(128)), schema="purchasing")
        op.add_column(table, sa.Column("cancelled_at", sa.DateTime(timezone=True)), schema="purchasing")

    op.add_column("purchase_receipts", sa.Column("reconciliation_attempts", sa.Integer(), nullable=False, server_default="0"), schema="purchasing")
    op.add_column("purchase_receipts", sa.Column("last_reconciliation_at", sa.DateTime(timezone=True)), schema="purchasing")
    op.add_column("purchase_receipts", sa.Column("reconciled_by_actor_id", sa.String(128)), schema="purchasing")
    op.create_check_constraint("ck_purchasing_receipt_reconciliation_attempts", "purchase_receipts", "reconciliation_attempts >= 0", schema="purchasing")

    op.add_column("purchase_receipt_lines", sa.Column("line_number", sa.Integer()), schema="purchasing")
    op.add_column("purchase_receipt_lines", sa.Column("inventory_idempotency_key", sa.String(200)), schema="purchasing")
    op.execute("""
        with numbered as (
            select id, row_number() over(partition by tenant_id, receipt_id order by id)::integer line_number
            from purchasing.purchase_receipt_lines
        )
        update purchasing.purchase_receipt_lines line
        set line_number=numbered.line_number,
            inventory_idempotency_key='purchase-receipt-' || line.id
        from numbered where numbered.id=line.id
    """)
    op.alter_column("purchase_receipt_lines", "line_number", nullable=False, schema="purchasing")
    op.alter_column("purchase_receipt_lines", "inventory_idempotency_key", nullable=False, schema="purchasing")
    op.create_unique_constraint("uq_purchasing_receipt_line_number", "purchase_receipt_lines", ["tenant_id", "receipt_id", "line_number"], schema="purchasing")
    op.create_unique_constraint("uq_purchasing_receipt_inventory_key", "purchase_receipt_lines", ["tenant_id", "inventory_idempotency_key"], schema="purchasing")


def downgrade() -> None:
    op.drop_constraint("uq_purchasing_receipt_inventory_key", "purchase_receipt_lines", schema="purchasing", type_="unique")
    op.drop_constraint("uq_purchasing_receipt_line_number", "purchase_receipt_lines", schema="purchasing", type_="unique")
    op.drop_column("purchase_receipt_lines", "inventory_idempotency_key", schema="purchasing")
    op.drop_column("purchase_receipt_lines", "line_number", schema="purchasing")
    op.drop_constraint("ck_purchasing_receipt_reconciliation_attempts", "purchase_receipts", schema="purchasing", type_="check")
    op.drop_column("purchase_receipts", "reconciled_by_actor_id", schema="purchasing")
    op.drop_column("purchase_receipts", "last_reconciliation_at", schema="purchasing")
    op.drop_column("purchase_receipts", "reconciliation_attempts", schema="purchasing")
    for table in ("purchase_orders", "requisitions"):
        op.drop_column(table, "cancelled_at", schema="purchasing")
        op.drop_column(table, "cancelled_by_actor_id", schema="purchasing")
        op.drop_column(table, "cancellation_reason", schema="purchasing")
