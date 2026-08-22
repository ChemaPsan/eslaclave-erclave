"""Tenant-managed business document code sequences.

Revision ID: 20260821_0022
Revises: 20260821_0021
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0022"
down_revision: str | None = "20260821_0021"
branch_labels = None
depends_on = None

DEFAULT_SEQUENCES = (
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
)


def _values_sql() -> str:
    def quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"
    return ",".join(
        f"({quote(document_type)},{quote(module_code)},{quote(name_es)},{quote(name_en)},{quote(prefix)})"
        for document_type, module_code, name_es, name_en, prefix in DEFAULT_SEQUENCES
    )


def upgrade() -> None:
    op.create_table(
        "code_sequences",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("document_type", sa.String(80), nullable=False),
        sa.Column("module_code", sa.String(40), nullable=False),
        sa.Column("name_es", sa.String(160), nullable=False),
        sa.Column("name_en", sa.String(160), nullable=False),
        sa.Column("prefix", sa.String(24), nullable=False),
        sa.Column("separator", sa.String(3), nullable=False, server_default="-"),
        sa.Column("next_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("padding", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("mode", sa.String(20), nullable=False, server_default="managed"),
        sa.Column("system_default", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "document_type", name="uq_code_sequences_tenant_document_type"),
        sa.CheckConstraint("mode in ('managed','manual')", name="ck_code_sequences_mode"),
        sa.CheckConstraint("next_number >= 1", name="ck_code_sequences_next_number"),
        sa.CheckConstraint("padding between 1 and 12", name="ck_code_sequences_padding"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_code_sequences_status"),
        schema="admin",
    )
    op.create_index("ix_code_sequences_tenant_module", "code_sequences", ["tenant_id", "module_code", "document_type"], schema="admin")
    values_sql = _values_sql()
    connection = op.get_bind()
    connection.execute(sa.text(f"""create function admin.seed_default_code_sequences() returns trigger language plpgsql as $$
        begin
          insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
          select 'seq_'||substr(md5(new.id||':'||seed.document_type),1,26),new.id,seed.document_type,seed.module_code,seed.name_es,seed.name_en,seed.prefix,'-',1,6,'managed',true,'active'
          from (values {values_sql}) as seed(document_type,module_code,name_es,name_en,prefix)
          on conflict(tenant_id,document_type) do nothing;
          return new;
        end $$"""))
    connection.execute(sa.text("create trigger trg_tenants_seed_code_sequences after insert on admin.tenants for each row execute function admin.seed_default_code_sequences()"))
    connection.execute(sa.text(f"""insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
        select 'seq_'||substr(md5(t.id||':'||seed.document_type),1,26),t.id,seed.document_type,seed.module_code,seed.name_es,seed.name_en,seed.prefix,'-',1,6,'managed',true,'active'
        from admin.tenants t cross join (values {values_sql}) as seed(document_type,module_code,name_es,name_en,prefix)
        on conflict(tenant_id,document_type) do nothing"""))


def downgrade() -> None:
    op.execute("drop trigger if exists trg_tenants_seed_code_sequences on admin.tenants")
    op.execute("drop function if exists admin.seed_default_code_sequences()")
    op.drop_index("ix_code_sequences_tenant_module", table_name="code_sequences", schema="admin")
    op.drop_table("code_sequences", schema="admin")
