"""purchasing supplier-to-receipt first slice.

Revision ID: 20260824_0024
Revises: 20260821_0023
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260824_0024"
down_revision: str | None = "20260821_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS purchasing")
    op.create_table("suppliers",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(40), nullable=False), sa.Column("commercial_name", sa.String(240), nullable=False),
        sa.Column("legal_name", sa.String(240)), sa.Column("tax_id", sa.String(40)),
        sa.Column("currency", sa.String(12), nullable=False), sa.Column("payment_terms", sa.String(40), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False, server_default="0"), sa.Column("email", sa.String(254)), sa.Column("phone", sa.String(30)),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_purchasing_supplier_status"), sa.CheckConstraint("lead_time_days >= 0", name="ck_purchasing_supplier_lead"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_purchasing_supplier_code"), sa.UniqueConstraint("tenant_id", "id", name="uq_purchasing_supplier_tenant_id"), schema="purchasing")
    op.create_index("ix_purchasing_suppliers_search", "suppliers", ["tenant_id", "status", "commercial_name"], schema="purchasing")

    op.create_table("requisitions",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("code", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"), sa.Column("required_date", sa.Date(), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False), sa.Column("source_type", sa.String(32), nullable=False, server_default="manual"), sa.Column("source_id", sa.String(40)),
        sa.Column("requested_by_actor_id", sa.String(128), nullable=False), sa.Column("approved_by_actor_id", sa.String(128)), sa.Column("rejection_reason", sa.Text()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)), sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft','submitted','approved','rejected','converted','cancelled')", name="ck_purchasing_requisition_status"),
        sa.CheckConstraint("priority in ('normal','urgent')", name="ck_purchasing_requisition_priority"),
        sa.CheckConstraint("source_type in ('manual','inventory_shortage','production_shortage')", name="ck_purchasing_requisition_source"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_purchasing_requisition_code"), sa.UniqueConstraint("tenant_id", "id", name="uq_purchasing_requisition_tenant_id"), schema="purchasing")
    op.create_index("ix_purchasing_requisitions_search", "requisitions", ["tenant_id", "status", "required_date"], schema="purchasing")
    op.create_table("requisition_lines",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("requisition_id", sa.String(40), nullable=False), sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("line_type", sa.String(24), nullable=False), sa.Column("inventory_item_ref_id", sa.String(40)), sa.Column("item_code_snapshot", sa.String(80)), sa.Column("item_name_snapshot", sa.String(240)),
        sa.Column("description", sa.String(300), nullable=False), sa.Column("quantity", sa.Numeric(18, 6), nullable=False), sa.Column("unit_code", sa.String(20), nullable=False),
        sa.CheckConstraint("line_type in ('inventory_item','service')", name="ck_purchasing_req_line_type"), sa.CheckConstraint("quantity > 0", name="ck_purchasing_req_line_quantity"),
        sa.CheckConstraint("(line_type='inventory_item' and inventory_item_ref_id is not null) or line_type='service'", name="ck_purchasing_req_line_reference"),
        sa.UniqueConstraint("tenant_id", "requisition_id", "line_number", name="uq_purchasing_req_line_number"),
        sa.ForeignKeyConstraint(["tenant_id", "requisition_id"], ["purchasing.requisitions.tenant_id", "purchasing.requisitions.id"], ondelete="CASCADE"), schema="purchasing")

    op.create_table("purchase_orders",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("code", sa.String(60), nullable=False),
        sa.Column("requisition_id", sa.String(40)), sa.Column("supplier_id", sa.String(40), nullable=False), sa.Column("supplier_code_snapshot", sa.String(40), nullable=False), sa.Column("supplier_name_snapshot", sa.String(240), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"), sa.Column("currency", sa.String(12), nullable=False), sa.Column("payment_terms", sa.String(40), nullable=False),
        sa.Column("direct_purchase_reason", sa.String(500)), sa.Column("subtotal", sa.Numeric(18,2), nullable=False, server_default="0"), sa.Column("buyer_actor_id", sa.String(128), nullable=False), sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft','issued','partially_received','received','closed','cancelled')", name="ck_purchasing_order_status"),
        sa.CheckConstraint("requisition_id is not null or direct_purchase_reason is not null", name="ck_purchasing_order_origin"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_purchasing_order_code"), sa.UniqueConstraint("tenant_id", "id", name="uq_purchasing_order_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "supplier_id"], ["purchasing.suppliers.tenant_id", "purchasing.suppliers.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "requisition_id"], ["purchasing.requisitions.tenant_id", "purchasing.requisitions.id"]), schema="purchasing")
    op.create_index("ix_purchasing_orders_search", "purchase_orders", ["tenant_id", "status", "created_at"], schema="purchasing")
    op.create_table("purchase_order_lines",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("purchase_order_id", sa.String(40), nullable=False), sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("line_type", sa.String(24), nullable=False), sa.Column("inventory_item_ref_id", sa.String(40)), sa.Column("item_code_snapshot", sa.String(80)), sa.Column("item_name_snapshot", sa.String(240)),
        sa.Column("description", sa.String(300), nullable=False), sa.Column("quantity", sa.Numeric(18,6), nullable=False), sa.Column("received_quantity", sa.Numeric(18,6), nullable=False, server_default="0"),
        sa.Column("unit_code", sa.String(20), nullable=False), sa.Column("unit_price", sa.Numeric(18,2), nullable=False), sa.Column("line_total", sa.Numeric(18,2), nullable=False),
        sa.CheckConstraint("line_type in ('inventory_item','service')", name="ck_purchasing_order_line_type"), sa.CheckConstraint("quantity > 0 and received_quantity >= 0 and received_quantity <= quantity and unit_price >= 0", name="ck_purchasing_order_line_values"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_purchasing_order_line_tenant_id"),
        sa.UniqueConstraint("tenant_id", "purchase_order_id", "line_number", name="uq_purchasing_order_line_number"),
        sa.ForeignKeyConstraint(["tenant_id", "purchase_order_id"], ["purchasing.purchase_orders.tenant_id", "purchasing.purchase_orders.id"], ondelete="CASCADE"), schema="purchasing")

    op.create_table("purchase_receipts",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("code", sa.String(60), nullable=False), sa.Column("purchase_order_id", sa.String(40), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="processing"), sa.Column("supplier_document_reference", sa.String(120)), sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("receiver_actor_id", sa.String(128), nullable=False), sa.Column("reconciliation_error", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('processing','completed','needs_reconciliation')", name="ck_purchasing_receipt_status"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_purchasing_receipt_code"), sa.UniqueConstraint("tenant_id", "id", name="uq_purchasing_receipt_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "purchase_order_id"], ["purchasing.purchase_orders.tenant_id", "purchasing.purchase_orders.id"]), schema="purchasing")
    op.create_index("ix_purchasing_receipts_search", "purchase_receipts", ["tenant_id", "status", "received_at"], schema="purchasing")
    op.create_table("purchase_receipt_lines",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("receipt_id", sa.String(40), nullable=False), sa.Column("order_line_id", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Numeric(18,6), nullable=False), sa.Column("warehouse_ref_id", sa.String(40), nullable=False), sa.Column("inventory_movement_ref_id", sa.String(40)), sa.Column("reconciliation_status", sa.String(16), nullable=False, server_default="pending"),
        sa.CheckConstraint("quantity > 0", name="ck_purchasing_receipt_line_quantity"), sa.CheckConstraint("reconciliation_status in ('pending','completed','failed')", name="ck_purchasing_receipt_line_reconciliation"),
        sa.UniqueConstraint("tenant_id", "receipt_id", "order_line_id", name="uq_purchasing_receipt_order_line"),
        sa.ForeignKeyConstraint(["tenant_id", "receipt_id"], ["purchasing.purchase_receipts.tenant_id", "purchasing.purchase_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "order_line_id"], ["purchasing.purchase_order_lines.tenant_id", "purchasing.purchase_order_lines.id"]), schema="purchasing")
    op.create_table("idempotency_records", sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("operation", sa.String(100), nullable=False), sa.Column("idempotency_key", sa.String(200), nullable=False), sa.Column("request_hash", sa.String(64), nullable=False), sa.Column("response_payload", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_purchasing_idempotency"), schema="purchasing")
    op.create_table("audit_events", sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("actor_id", sa.String(128), nullable=False), sa.Column("action", sa.String(100), nullable=False), sa.Column("entity_type", sa.String(80), nullable=False), sa.Column("entity_id", sa.String(40), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), schema="purchasing")


def downgrade() -> None:
    for table in ["audit_events", "idempotency_records", "purchase_receipt_lines", "purchase_receipts", "purchase_order_lines", "purchase_orders", "requisition_lines", "requisitions", "suppliers"]:
        op.drop_table(table, schema="purchasing")
    op.execute("DROP SCHEMA IF EXISTS purchasing")
