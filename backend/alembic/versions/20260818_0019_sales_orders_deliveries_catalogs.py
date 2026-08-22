"""sales orders, deliveries, commercial catalogs and document branding.

Revision ID: 20260818_0019
Revises: 20260818_0018
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260818_0019"
down_revision: str | None = "20260818_0018"
branch_labels = None
depends_on = None


CATALOG_DEFAULTS = (
    ("currencies", "MXN", "Peso mexicano", "Mexican peso", '{"symbol":"$","decimal_places":2}'),
    ("currencies", "USD", "Dólar estadounidense", "US dollar", '{"symbol":"$","decimal_places":2}'),
    ("currencies", "EUR", "Euro", "Euro", '{"symbol":"€","decimal_places":2}'),
    ("payment_terms", "cash", "Contado", "Cash", '{"days":0}'),
    ("payment_terms", "credit_7", "Crédito 7 días", "Net 7", '{"days":7}'),
    ("payment_terms", "credit_15", "Crédito 15 días", "Net 15", '{"days":15}'),
    ("payment_terms", "credit_30", "Crédito 30 días", "Net 30", '{"days":30}'),
    ("payment_terms", "credit_45", "Crédito 45 días", "Net 45", '{"days":45}'),
    ("payment_terms", "credit_60", "Crédito 60 días", "Net 60", '{"days":60}'),
)


def quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    op.create_table(
        "catalog_items",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("catalog_code", sa.String(60), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name_es", sa.String(160), nullable=False),
        sa.Column("name_en", sa.String(160), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("system_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("catalog_code in ('currencies','payment_terms')", name="ck_admin_catalog_item_catalog"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_admin_catalog_item_status"),
        sa.UniqueConstraint("tenant_id", "catalog_code", "code", name="uq_admin_catalog_item_code"),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], name="fk_admin_catalog_item_tenant", ondelete="CASCADE"),
        schema="admin",
    )
    op.create_index("ix_admin_catalog_items_lookup", "catalog_items", ["tenant_id", "catalog_code", "status", "name_es"], schema="admin")

    values_sql = ",".join(
        f"({quoted(catalog)},{quoted(code)},{quoted(name_es)},{quoted(name_en)},{quoted(metadata)}::jsonb)"
        for catalog, code, name_es, name_en, metadata in CATALOG_DEFAULTS
    )
    op.get_bind().exec_driver_sql(f"""
        create function admin.seed_default_commercial_catalogs() returns trigger language plpgsql as $$
        begin
          insert into admin.catalog_items(id,tenant_id,catalog_code,code,name_es,name_en,metadata,system_default,status)
          select 'cat_'||substr(md5(new.id||':'||seed.catalog_code||':'||seed.code),1,26),new.id,
                 seed.catalog_code,seed.code,seed.name_es,seed.name_en,seed.metadata,true,'active'
          from (values {values_sql}) as seed(catalog_code,code,name_es,name_en,metadata)
          on conflict(tenant_id,catalog_code,code) do nothing;
          insert into admin.tenant_settings(id,tenant_id,key,module_code,value)
          values('set_'||substr(md5(new.id||':document.template'),1,26),new.id,'document.template','admin',
            '{{"logo_data_url":null,"primary_color":"#6106A0","accent_color":"#F557D3","text_color":"#190F34","footer_text":null,"show_page_number":true}}'::jsonb)
          on conflict(tenant_id,key) do nothing;
          return new;
        end $$
    """)
    op.execute("create trigger trg_tenants_seed_commercial_catalogs after insert on admin.tenants for each row execute function admin.seed_default_commercial_catalogs()")
    connection = op.get_bind()
    insert_catalog = sa.text("""
        insert into admin.catalog_items(id,tenant_id,catalog_code,code,name_es,name_en,metadata,system_default,status)
        values(:id,:tenant,:catalog,:code,:name_es,:name_en,cast(:metadata as jsonb),true,'active')
        on conflict(tenant_id,catalog_code,code) do nothing
    """)
    tenant_ids = connection.execute(sa.text("select id from admin.tenants")).scalars().all()
    for tenant_id in tenant_ids:
        for catalog, code, name_es, name_en, metadata in CATALOG_DEFAULTS:
            connection.execute(insert_catalog, {"id": f"cat_{__import__('hashlib').md5(f'{tenant_id}:{catalog}:{code}'.encode()).hexdigest()[:26]}", "tenant": tenant_id, "catalog": catalog, "code": code, "name_es": name_es, "name_en": name_en, "metadata": metadata})
        connection.execute(sa.text("""
            insert into admin.tenant_settings(id,tenant_id,key,module_code,value)
            values(:id,:tenant,'document.template','admin',cast(:value as jsonb))
            on conflict(tenant_id,key) do nothing
        """), {"id": f"set_{__import__('hashlib').md5(f'{tenant_id}:document.template'.encode()).hexdigest()[:26]}", "tenant": tenant_id, "value": '{"logo_data_url":null,"primary_color":"#6106A0","accent_color":"#F557D3","text_color":"#190F34","footer_text":null,"show_page_number":true}'})

    op.drop_constraint("ck_sales_customer_currency", "customers", schema="sales", type_="check")
    op.drop_constraint("ck_sales_customer_payment_terms", "customers", schema="sales", type_="check")
    op.drop_constraint("ck_sales_quote_currency", "quotes", schema="sales", type_="check")
    op.drop_constraint("ck_sales_quote_payment_terms", "quotes", schema="sales", type_="check")

    op.create_table(
        "orders",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("quote_id", sa.String(40), nullable=False),
        sa.Column("quote_code_snapshot", sa.String(60), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False),
        sa.Column("customer_code_snapshot", sa.String(60), nullable=False),
        sa.Column("customer_name_snapshot", sa.String(200), nullable=False),
        sa.Column("responsible_worker_ref_id", sa.String(40), nullable=False),
        sa.Column("responsible_worker_name", sa.String(240), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="confirmed"),
        sa.Column("currency", sa.String(12), nullable=False),
        sa.Column("payment_terms", sa.String(40), nullable=False),
        sa.Column("promised_delivery_date", sa.Date()),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(18, 2)),
        sa.Column("estimated_margin", sa.Numeric(9, 4)),
        sa.Column("actual_cost", sa.Numeric(18, 2)),
        sa.Column("actual_margin", sa.Numeric(9, 4)),
        sa.Column("notes", sa.Text()),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('confirmed','fulfillment_pending','ready','partially_delivered','delivered','cancelled')", name="ck_sales_order_status"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sales_order_code"),
        sa.UniqueConstraint("tenant_id", "quote_id", name="uq_sales_order_quote"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sales_order_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "quote_id"], ["sales.quotes.tenant_id", "sales.quotes.id"], name="fk_sales_order_quote_tenant"),
        sa.ForeignKeyConstraint(["tenant_id", "customer_id"], ["sales.customers.tenant_id", "sales.customers.id"], name="fk_sales_order_customer_tenant"),
        schema="sales",
    )
    op.create_index("ix_sales_orders_search", "orders", ["tenant_id", "status", "promised_delivery_date", "code"], schema="sales")
    op.create_index("ix_sales_orders_customer", "orders", ["tenant_id", "customer_id", "created_at"], schema="sales")

    op.create_table(
        "order_lines",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("order_id", sa.String(40), nullable=False),
        sa.Column("quote_line_id", sa.String(40), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_service_ref_id", sa.String(40), nullable=False),
        sa.Column("product_service_code", sa.String(80), nullable=False),
        sa.Column("product_service_name", sa.String(240), nullable=False),
        sa.Column("product_service_type", sa.String(20), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("delivered_quantity", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(7, 4), nullable=False),
        sa.Column("total", sa.Numeric(18, 2), nullable=False),
        sa.Column("standard_unit_cost_snapshot", sa.Numeric(18, 6)),
        sa.Column("estimated_cost", sa.Numeric(18, 2)),
        sa.Column("fulfillment_mode", sa.String(24), nullable=False),
        sa.Column("fulfillment_status", sa.String(32), nullable=False),
        sa.Column("inventory_item_ref_id", sa.String(40)),
        sa.Column("production_request_ref_id", sa.String(40)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("fulfillment_mode in ('pending','stock','production','service')", name="ck_sales_order_line_mode"),
        sa.CheckConstraint("fulfillment_status in ('pending','reserved','production_requested','ready','partially_delivered','delivered','cancelled')", name="ck_sales_order_line_fulfillment_status"),
        sa.CheckConstraint("ordered_quantity > 0 and delivered_quantity >= 0 and delivered_quantity <= ordered_quantity", name="ck_sales_order_line_quantities"),
        sa.UniqueConstraint("tenant_id", "order_id", "line_number", name="uq_sales_order_line_number"),
        sa.UniqueConstraint("tenant_id", "quote_line_id", name="uq_sales_order_quote_line"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sales_order_line_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["sales.orders.tenant_id", "sales.orders.id"], name="fk_sales_order_line_order_tenant", ondelete="CASCADE"),
        schema="sales",
    )
    op.create_index("ix_sales_order_lines_product", "order_lines", ["tenant_id", "product_service_ref_id", "fulfillment_status"], schema="sales")

    op.create_table(
        "order_line_reservations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("order_line_id", sa.String(40), nullable=False),
        sa.Column("reservation_ref_id", sa.String(40), nullable=False),
        sa.Column("warehouse_ref_id", sa.String(40), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("consumed_quantity", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("unit_cost_snapshot", sa.Numeric(18, 6), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('active','released','consumed')", name="ck_sales_order_reservation_status"),
        sa.CheckConstraint("reserved_quantity > 0 and consumed_quantity >= 0 and consumed_quantity <= reserved_quantity", name="ck_sales_order_reservation_quantities"),
        sa.UniqueConstraint("tenant_id", "reservation_ref_id", name="uq_sales_order_reservation_ref"),
        sa.ForeignKeyConstraint(["tenant_id", "order_line_id"], ["sales.order_lines.tenant_id", "sales.order_lines.id"], name="fk_sales_order_reservation_line_tenant", ondelete="CASCADE"),
        schema="sales",
    )

    op.create_table(
        "deliveries",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("order_id", sa.String(40), nullable=False),
        sa.Column("order_code_snapshot", sa.String(60), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False),
        sa.Column("customer_name_snapshot", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("recipient_name", sa.String(200)),
        sa.Column("evidence_reference", sa.String(300)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft','confirmed','cancelled')", name="ck_sales_delivery_status"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sales_delivery_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sales_delivery_tenant_id"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["sales.orders.tenant_id", "sales.orders.id"], name="fk_sales_delivery_order_tenant"),
        schema="sales",
    )
    op.create_index("ix_sales_deliveries_search", "deliveries", ["tenant_id", "status", "scheduled_date", "code"], schema="sales")

    op.create_table(
        "delivery_lines",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("delivery_id", sa.String(40), nullable=False),
        sa.Column("order_line_id", sa.String(40), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_service_ref_id", sa.String(40), nullable=False),
        sa.Column("product_service_code", sa.String(80), nullable=False),
        sa.Column("product_service_name", sa.String(240), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("actual_cost", sa.Numeric(18, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("quantity > 0", name="ck_sales_delivery_line_quantity"),
        sa.UniqueConstraint("tenant_id", "delivery_id", "order_line_id", name="uq_sales_delivery_order_line"),
        sa.ForeignKeyConstraint(["tenant_id", "delivery_id"], ["sales.deliveries.tenant_id", "sales.deliveries.id"], name="fk_sales_delivery_line_delivery_tenant", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id", "order_line_id"], ["sales.order_lines.tenant_id", "sales.order_lines.id"], name="fk_sales_delivery_line_order_line_tenant"),
        schema="sales",
    )

    op.create_table(
        "sales_order_requests",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("sales_order_id", sa.String(40), nullable=False),
        sa.Column("sales_order_line_id", sa.String(40), nullable=False),
        sa.Column("product_service_ref_id", sa.String(40), nullable=False),
        sa.Column("product_service_code_snapshot", sa.String(80), nullable=False),
        sa.Column("product_service_name_snapshot", sa.String(240), nullable=False),
        sa.Column("recipe_version_ref_id", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("requested_due_date", sa.Date()),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_configuration"),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('pending_configuration','converted','cancelled')", name="ck_production_sales_order_request_status"),
        sa.CheckConstraint("quantity > 0", name="ck_production_sales_order_request_quantity"),
        sa.UniqueConstraint("tenant_id", "sales_order_line_id", name="uq_production_sales_order_request_line"),
        schema="production",
    )
    op.create_index("ix_production_sales_requests_status", "sales_order_requests", ["tenant_id", "status", "requested_due_date"], schema="production")


def downgrade() -> None:
    op.drop_index("ix_production_sales_requests_status", table_name="sales_order_requests", schema="production")
    op.drop_table("sales_order_requests", schema="production")
    op.drop_table("delivery_lines", schema="sales")
    op.drop_index("ix_sales_deliveries_search", table_name="deliveries", schema="sales")
    op.drop_table("deliveries", schema="sales")
    op.drop_table("order_line_reservations", schema="sales")
    op.drop_index("ix_sales_order_lines_product", table_name="order_lines", schema="sales")
    op.drop_table("order_lines", schema="sales")
    op.drop_index("ix_sales_orders_customer", table_name="orders", schema="sales")
    op.drop_index("ix_sales_orders_search", table_name="orders", schema="sales")
    op.drop_table("orders", schema="sales")
    op.create_check_constraint("ck_sales_quote_payment_terms", "quotes", "payment_terms in ('cash','credit_7','credit_15','credit_30','credit_45','credit_60')", schema="sales")
    op.create_check_constraint("ck_sales_quote_currency", "quotes", "currency in ('MXN','USD','EUR')", schema="sales")
    op.create_check_constraint("ck_sales_customer_payment_terms", "customers", "payment_terms in ('cash','credit_7','credit_15','credit_30','credit_45','credit_60')", schema="sales")
    op.create_check_constraint("ck_sales_customer_currency", "customers", "currency in ('MXN','USD','EUR')", schema="sales")
    op.execute("drop trigger if exists trg_tenants_seed_commercial_catalogs on admin.tenants")
    op.execute("drop function if exists admin.seed_default_commercial_catalogs()")
    op.drop_index("ix_admin_catalog_items_lookup", table_name="catalog_items", schema="admin")
    op.drop_table("catalog_items", schema="admin")
