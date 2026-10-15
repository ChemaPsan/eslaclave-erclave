"""CC-18: sequence catalog and historical numbering mode for remaining owners."""

from alembic import op
import sqlalchemy as sa

revision: str = "20261014_0061"
down_revision: str | None = "20261014_0060"
branch_labels = None
depends_on = None

PRIOR = (
    ("production.product_service", "production", "Producto o servicio", "Product or service", "PRD"),
    ("production.recipe", "production", "Receta", "Recipe", "REC"),
    ("production.order", "production", "Orden de produccion", "Production order", "OP"),
    ("production.machine", "production", "Maquinaria", "Machine", "MAQ"),
    ("inventory.warehouse", "inventory", "Almacen", "Warehouse", "ALM"),
    ("inventory.item", "inventory", "Articulo", "Item", "ART"),
    ("inventory.movement", "inventory", "Movimiento de inventario", "Inventory movement", "MOV"),
    ("hr.area", "hr", "Area", "Area", "AREA"),
    ("hr.position", "hr", "Puesto", "Position", "PUE"),
    ("hr.worker", "hr", "Empleado", "Worker", "EMP"),
    ("sales.customer", "sales", "Cliente", "Customer", "CLI"),
    ("sales.quote", "sales", "Cotizacion", "Quote", "COT"),
    ("sales.order", "sales", "Pedido", "Sales order", "PED"),
    ("sales.delivery", "sales", "Entrega", "Delivery", "ENT"),
    ("sales.service_order", "sales", "Orden de servicio", "Service order", "OS"),
)
NEW = (
    ("purchasing.supplier", "purchasing", "Proveedor", "Supplier", "PROV"),
    ("purchasing.requisition", "purchasing", "Requisicion", "Requisition", "REQ"),
    ("purchasing.order", "purchasing", "Orden de compra", "Purchase order", "OC"),
    ("purchasing.receipt", "purchasing", "Recepcion de compra", "Purchase receipt", "REC-C"),
    ("maintenance.order", "maintenance", "Orden de mantenimiento", "Maintenance order", "OM"),
)
CODE_MODE_TABLES = (
    ("purchasing", "suppliers"),
    ("purchasing", "requisitions"),
    ("purchasing", "purchase_orders"),
    ("purchasing", "purchase_receipts"),
    ("maintenance", "orders"),
)


def _values_sql(rows):
    def quote(value):
        return "'" + value.replace("'", "''") + "'"
    return ",".join("(" + ",".join(quote(value) for value in row) + ")" for row in rows)


def _seed_function(rows):
    values = _values_sql(rows)
    op.execute(f"""create or replace function admin.seed_default_code_sequences() returns trigger language plpgsql as $$
        begin
          insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
          select 'seq_'||substr(md5(new.id||':'||seed.document_type),1,26),new.id,seed.document_type,seed.module_code,seed.name_es,seed.name_en,seed.prefix,'-',1,6,'managed',true,'active'
          from (values {values}) as seed(document_type,module_code,name_es,name_en,prefix)
          on conflict(tenant_id,document_type) do nothing;
          return new;
        end $$""")


def upgrade():
    op.add_column("labor_roles", sa.Column("code", sa.String(80), nullable=True), schema="hr")
    op.create_unique_constraint("uq_hr_position_code", "labor_roles", ["tenant_id", "code"], schema="hr")
    for schema, table in CODE_MODE_TABLES:
        op.add_column(table, sa.Column("code_mode", sa.String(7), nullable=True), schema=schema)
        op.create_check_constraint(f"ck_cc18_{table}_code_mode", table,
            "code_mode is null or code_mode in ('managed','manual')", schema=schema)
    _seed_function(PRIOR + NEW)
    op.execute(f"""insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
        select 'seq_'||substr(md5(t.id||':'||seed.document_type),1,26),t.id,seed.document_type,seed.module_code,seed.name_es,seed.name_en,seed.prefix,'-',1,6,'managed',true,'active'
        from admin.tenants t cross join (values {_values_sql(NEW)}) as seed(document_type,module_code,name_es,name_en,prefix)
        on conflict(tenant_id,document_type) do nothing""")


def downgrade():
    op.execute("LOCK TABLE hr.labor_roles, purchasing.suppliers, purchasing.requisitions, purchasing.purchase_orders, purchasing.purchase_receipts, maintenance.orders, admin.code_sequences IN ACCESS EXCLUSIVE MODE")
    predicates = " or ".join(f"exists(select 1 from {schema}.{table} where code_mode is not null)" for schema, table in CODE_MODE_TABLES)
    types = ",".join("'" + row[0] + "'" for row in NEW)
    op.execute(f"""DO $$ BEGIN IF exists(select 1 from hr.labor_roles where code is not null)
        or {predicates}
        or exists(select 1 from admin.code_sequences where document_type in ({types})
            and (next_number <> 1 or mode <> 'managed' or status <> 'active' or system_default is not true))
        or exists(select 1 from admin.audit_events where action in ('admin.code_sequence.allocate','admin.code_sequence.update')
            and metadata->>'document_type' in ({types}))
        THEN RAISE EXCEPTION 'CC18 numbering history or configuration exists; use forward-fix'; END IF; END $$""")
    _seed_function(PRIOR)
    op.execute(f"delete from admin.code_sequences where document_type in ({types})")
    for schema, table in reversed(CODE_MODE_TABLES):
        op.drop_constraint(f"ck_cc18_{table}_code_mode", table, type_="check", schema=schema)
        op.drop_column(table, "code_mode", schema=schema)
    op.drop_constraint("uq_hr_position_code", "labor_roles", type_="unique", schema="hr")
    op.drop_column("labor_roles", "code", schema="hr")
