"""sales customers and quotes first real slice.

Revision ID: 20260818_0018
Revises: 20260818_0017
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260818_0018"
down_revision: str | None = "20260818_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS sales")
    op.create_table(
        "customers",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("commercial_name", sa.String(200), nullable=False),
        sa.Column("customer_type", sa.String(24), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="prospect"),
        sa.Column("responsible_worker_ref_id", sa.String(40), nullable=False),
        sa.Column("responsible_worker_name", sa.String(240), nullable=False),
        sa.Column("payment_terms", sa.String(24), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("credit_limit", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("legal_name", sa.String(240)),
        sa.Column("tax_id", sa.String(20)),
        sa.Column("tax_regime", sa.String(120)),
        sa.Column("cfdi_use", sa.String(10)),
        sa.Column("billing_email", sa.String(254)),
        sa.Column("billing_phone", sa.String(30)),
        sa.Column("billing_address", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("customer_type in ('company','individual','government','internal')", name="ck_sales_customer_type"),
        sa.CheckConstraint("status in ('prospect','active','inactive','blocked')", name="ck_sales_customer_status"),
        sa.CheckConstraint("currency in ('MXN','USD','EUR')", name="ck_sales_customer_currency"),
        sa.CheckConstraint("payment_terms in ('cash','credit_7','credit_15','credit_30','credit_45','credit_60')", name="ck_sales_customer_payment_terms"),
        sa.CheckConstraint("credit_limit >= 0", name="ck_sales_customer_credit_limit"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sales_customer_code"),
        sa.UniqueConstraint("tenant_id", "tax_id", name="uq_sales_customer_tax_id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sales_customer_tenant_id"),
        schema="sales",
    )
    op.create_index("ix_sales_customers_search", "customers", ["tenant_id", "status", "commercial_name", "code"], schema="sales")
    op.create_index("ix_sales_customers_responsible", "customers", ["tenant_id", "responsible_worker_ref_id"], schema="sales")

    op.create_table(
        "customer_contacts",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("role", sa.String(120)),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_sales_customer_contact_status"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["sales.customers.tenant_id", "sales.customers.id"], name="fk_sales_contact_customer_tenant", ondelete="CASCADE"),
        schema="sales",
    )
    op.create_index("ix_sales_contacts_customer", "customer_contacts", ["tenant_id", "customer_id", "status"], schema="sales")
    op.create_index("uq_sales_primary_contact", "customer_contacts", ["tenant_id", "customer_id"], unique=True, schema="sales", postgresql_where=sa.text("is_primary and status = 'active'"))

    op.create_table(
        "quotes",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False),
        sa.Column("customer_code_snapshot", sa.String(60), nullable=False),
        sa.Column("customer_name_snapshot", sa.String(200), nullable=False),
        sa.Column("responsible_worker_ref_id", sa.String(40), nullable=False),
        sa.Column("responsible_worker_name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("payment_terms", sa.String(24), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("promised_delivery_date", sa.Date()),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(18, 2)),
        sa.Column("estimated_margin", sa.Numeric(9, 4)),
        sa.Column("notes", sa.Text()),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft','quoted','approved','expired','cancelled')", name="ck_sales_quote_status"),
        sa.CheckConstraint("currency in ('MXN','USD','EUR')", name="ck_sales_quote_currency"),
        sa.CheckConstraint("payment_terms in ('cash','credit_7','credit_15','credit_30','credit_45','credit_60')", name="ck_sales_quote_payment_terms"),
        sa.CheckConstraint("subtotal >= 0 and discount_total >= 0 and total >= 0 and discount_total <= subtotal", name="ck_sales_quote_totals"),
        sa.CheckConstraint("estimated_cost is null or estimated_cost >= 0", name="ck_sales_quote_estimated_cost"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sales_quote_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sales_quote_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["sales.customers.tenant_id", "sales.customers.id"], name="fk_sales_quote_customer_tenant"),
        schema="sales",
    )
    op.create_index("ix_sales_quotes_search", "quotes", ["tenant_id", "status", "valid_until", "code"], schema="sales")
    op.create_index("ix_sales_quotes_customer", "quotes", ["tenant_id", "customer_id", "created_at"], schema="sales")

    op.create_table(
        "quote_lines",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("quote_id", sa.String(40), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_service_ref_id", sa.String(40), nullable=False),
        sa.Column("product_service_code", sa.String(80), nullable=False),
        sa.Column("product_service_name", sa.String(240), nullable=False),
        sa.Column("product_service_type", sa.String(20), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(7, 4), nullable=False, server_default="0"),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("standard_unit_cost_snapshot", sa.Numeric(18, 6)),
        sa.Column("estimated_cost", sa.Numeric(18, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("line_number > 0 and quantity > 0 and unit_price >= 0", name="ck_sales_quote_line_values"),
        sa.CheckConstraint("discount_percentage >= 0 and discount_percentage <= 100", name="ck_sales_quote_line_discount_percentage"),
        sa.CheckConstraint("discount_amount >= 0 and total >= 0 and discount_amount <= subtotal", name="ck_sales_quote_line_totals"),
        sa.CheckConstraint("standard_unit_cost_snapshot is null or standard_unit_cost_snapshot >= 0", name="ck_sales_quote_line_cost"),
        sa.UniqueConstraint("tenant_id", "quote_id", "line_number", name="uq_sales_quote_line_number"),
        sa.ForeignKeyConstraint(["tenant_id", "quote_id"], ["sales.quotes.tenant_id", "sales.quotes.id"], name="fk_sales_quote_line_quote_tenant", ondelete="CASCADE"),
        schema="sales",
    )
    op.create_index("ix_sales_quote_lines_product", "quote_lines", ["tenant_id", "product_service_ref_id"], schema="sales")

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_payload", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_sales_idempotency"),
        schema="sales",
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="sales",
    )
    op.create_index("ix_sales_audit_entity", "audit_events", ["tenant_id", "entity_type", "entity_id", "occurred_at"], schema="sales")


def downgrade() -> None:
    op.drop_index("ix_sales_audit_entity", table_name="audit_events", schema="sales")
    op.drop_table("audit_events", schema="sales")
    op.drop_table("idempotency_records", schema="sales")
    op.drop_index("ix_sales_quote_lines_product", table_name="quote_lines", schema="sales")
    op.drop_table("quote_lines", schema="sales")
    op.drop_index("ix_sales_quotes_customer", table_name="quotes", schema="sales")
    op.drop_index("ix_sales_quotes_search", table_name="quotes", schema="sales")
    op.drop_table("quotes", schema="sales")
    op.drop_index("uq_sales_primary_contact", table_name="customer_contacts", schema="sales")
    op.drop_index("ix_sales_contacts_customer", table_name="customer_contacts", schema="sales")
    op.drop_table("customer_contacts", schema="sales")
    op.drop_index("ix_sales_customers_responsible", table_name="customers", schema="sales")
    op.drop_index("ix_sales_customers_search", table_name="customers", schema="sales")
    op.drop_table("customers", schema="sales")
    op.execute("DROP SCHEMA IF EXISTS sales")
