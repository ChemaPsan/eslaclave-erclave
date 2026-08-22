"""Tenant unit-of-measure catalog with 50 defaults.

Revision ID: 20260817_0015
Revises: 20260817_0014
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260817_0015"
down_revision: str | None = "20260817_0014"
branch_labels = None
depends_on = None

# Historical migrations must remain self-contained: never import mutable app seeds.
DEFAULT_UNITS = (
    ("H87", "Pieza", "Piece", "pz", "count", 0), ("C62", "Unidad", "Unit", "u", "count", 0),
    ("DZN", "Docena", "Dozen", "doc", "count", 0), ("PR", "Par", "Pair", "par", "count", 0),
    ("SET", "Juego", "Set", "jgo", "count", 0), ("XBX", "Caja", "Box", "caja", "package", 0),
    ("XPK", "Paquete", "Package", "paq", "package", 0), ("XBG", "Bolsa", "Bag", "bolsa", "package", 0),
    ("XRL", "Rollo", "Reel", "rollo", "package", 0), ("XPL", "Tarima", "Pallet", "tarima", "package", 0),
    ("KGM", "Kilogramo", "Kilogram", "kg", "mass", 3), ("GRM", "Gramo", "Gram", "g", "mass", 3),
    ("MGM", "Miligramo", "Milligram", "mg", "mass", 3), ("TNE", "Tonelada métrica", "Metric tonne", "t", "mass", 3),
    ("LBR", "Libra", "Pound", "lb", "mass", 3), ("ONZ", "Onza", "Ounce", "oz", "mass", 3),
    ("MTR", "Metro", "Metre", "m", "length", 3), ("CMT", "Centímetro", "Centimetre", "cm", "length", 3),
    ("MMT", "Milímetro", "Millimetre", "mm", "length", 3), ("KMT", "Kilómetro", "Kilometre", "km", "length", 3),
    ("INH", "Pulgada", "Inch", "in", "length", 3), ("FOT", "Pie", "Foot", "ft", "length", 3),
    ("YRD", "Yarda", "Yard", "yd", "length", 3), ("MTK", "Metro cuadrado", "Square metre", "m²", "area", 3),
    ("CMK", "Centímetro cuadrado", "Square centimetre", "cm²", "area", 3), ("MMK", "Milímetro cuadrado", "Square millimetre", "mm²", "area", 3),
    ("HAR", "Hectárea", "Hectare", "ha", "area", 3), ("LTR", "Litro", "Litre", "L", "volume", 3),
    ("MLT", "Mililitro", "Millilitre", "mL", "volume", 3), ("MTQ", "Metro cúbico", "Cubic metre", "m³", "volume", 3),
    ("CMQ", "Centímetro cúbico", "Cubic centimetre", "cm³", "volume", 3), ("GLL", "Galón estadounidense", "US gallon", "gal", "volume", 3),
    ("SEC", "Segundo", "Second", "s", "time", 3), ("MIN", "Minuto", "Minute", "min", "time", 3),
    ("HUR", "Hora", "Hour", "h", "time", 3), ("DAY", "Día", "Day", "d", "time", 3),
    ("WEE", "Semana", "Week", "sem", "time", 3), ("MON", "Mes", "Month", "mes", "time", 3),
    ("ANN", "Año", "Year", "a", "time", 3), ("KWH", "Kilowatt hora", "Kilowatt hour", "kWh", "energy", 3),
    ("WHR", "Watt hora", "Watt hour", "Wh", "energy", 3), ("KWT", "Kilowatt", "Kilowatt", "kW", "power", 3),
    ("WTT", "Watt", "Watt", "W", "power", 3), ("AMP", "Ampere", "Ampere", "A", "electric", 3),
    ("VLT", "Volt", "Volt", "V", "electric", 3), ("CEL", "Grado Celsius", "Degree Celsius", "°C", "temperature", 2),
    ("KEL", "Kelvin", "Kelvin", "K", "temperature", 2), ("PAL", "Pascal", "Pascal", "Pa", "pressure", 3),
    ("BAR", "Bar", "Bar", "bar", "pressure", 3), ("P1", "Porcentaje", "Percent", "%", "ratio", 3),
)


def upgrade() -> None:
    op.create_table(
        "units_of_measure",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name_es", sa.String(120), nullable=False),
        sa.Column("name_en", sa.String(120), nullable=False),
        sa.Column("symbol", sa.String(24), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("decimal_places", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("system_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_units_of_measure_tenant_code"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_units_of_measure_status"),
        sa.CheckConstraint("decimal_places between 0 and 6", name="ck_units_of_measure_decimal_places"),
        schema="admin",
    )
    op.create_index("ix_units_of_measure_tenant_status_name", "units_of_measure", ["tenant_id", "status", "name_es"], schema="admin")
    connection = op.get_bind()
    def quoted(value): return "'" + str(value).replace("'", "''") + "'"
    values_sql=",".join(f"({quoted(code)},{quoted(name_es)},{quoted(name_en)},{quoted(symbol)},{quoted(category)},{decimal_places})" for code,name_es,name_en,symbol,category,decimal_places in DEFAULT_UNITS)
    connection.execute(sa.text(f"""create function admin.seed_default_units_of_measure() returns trigger language plpgsql as $$ begin insert into admin.units_of_measure(id,tenant_id,code,name_es,name_en,symbol,category,decimal_places,system_default,status) select 'uom_'||substr(md5(new.id||':'||seed.code),1,26),new.id,seed.code,seed.name_es,seed.name_en,seed.symbol,seed.category,seed.decimal_places,true,'active' from (values {values_sql}) as seed(code,name_es,name_en,symbol,category,decimal_places) on conflict(tenant_id,code) do nothing; return new; end $$"""))
    connection.execute(sa.text("create trigger trg_tenants_seed_units_of_measure after insert on admin.tenants for each row execute function admin.seed_default_units_of_measure()"))
    tenants = connection.execute(sa.text("select id from admin.tenants")).scalars().all()
    insert = sa.text("""insert into admin.units_of_measure(id,tenant_id,code,name_es,name_en,symbol,category,decimal_places,system_default,status) values(:id,:tenant_id,:code,:name_es,:name_en,:symbol,:category,:decimal_places,true,'active') on conflict(tenant_id,code) do nothing""")
    for tenant_id in tenants:
        for code, name_es, name_en, symbol, category, decimal_places in DEFAULT_UNITS:
            connection.execute(insert, {"id": f"uom_{__import__('hashlib').md5(f'{tenant_id}:{code}'.encode()).hexdigest()[:26]}", "tenant_id": tenant_id, "code": code, "name_es": name_es, "name_en": name_en, "symbol": symbol, "category": category, "decimal_places": decimal_places})
    legacy = "case lower({0}) when 'pieza' then 'H87' when 'pza' then 'H87' when 'pz' then 'H87' when 'unidad' then 'C62' when 'servicio' then 'C62' when 'kg' then 'KGM' when 'g' then 'GRM' when 'l' then 'LTR' when 'ml' then 'MLT' when 'm' then 'MTR' when 'cm' then 'CMT' when 'min' then 'MIN' when 'hora' then 'HUR' when 'h' then 'HUR' else upper({0}) end"
    for table, column in (("inventory.items","base_unit"),("inventory.movements","unit"),("production.product_services","base_unit"),("production.recipe_versions","base_unit"),("production.recipe_resources","unit"),("production.production_orders","unit")):
        connection.execute(sa.text(f"update {table} set {column}={legacy.format(column)}"))
    permissions = (
        ("admin.unit.read", "read", "Consultar unidades de medida", "Read units of measure", "Permite consultar el catálogo de unidades de medida.", "Allows reading the unit-of-measure catalog.", "low", 1070),
        ("admin.unit.create", "create", "Crear unidades de medida", "Create units of measure", "Permite agregar unidades propias del tenant.", "Allows adding tenant-specific units of measure.", "standard", 1071),
        ("admin.unit.update", "update", "Actualizar unidades de medida", "Update units of measure", "Permite editar o inactivar unidades de medida.", "Allows editing or deactivating units of measure.", "high", 1072),
    )
    for code, action, es, en, des, den, risk, order in permissions:
        connection.execute(sa.text("""insert into admin.permissions(id,code,module_code,resource,action,description,status,display_name_es,display_name_en,description_es,description_en,classification,assignable_to_tenant_role,risk_level,sort_order) values(:id,:code,'admin','unit',:action,:den,'active',:es,:en,:des,:den,'tenant',true,:risk,:order) on conflict(code) do nothing"""), {"id": f"per_{__import__('hashlib').md5(code.encode()).hexdigest()[:26]}", "code": code, "action": action, "es": es, "en": en, "des": des, "den": den, "risk": risk, "order": order})
    connection.execute(sa.text("""insert into admin.role_permissions(id,tenant_id,role_id,permission_id,scope) select 'rpe_'||substr(md5(r.tenant_id||':'||r.id||':'||p.id),1,26),r.tenant_id,r.id,p.id,'{}'::jsonb from admin.roles r cross join admin.permissions p where r.status='active' and (p.code='admin.unit.read' or (r.code='owner' and r.system_role=true and p.code in ('admin.unit.create','admin.unit.update'))) on conflict(tenant_id,role_id,permission_id) do nothing"""))


def downgrade() -> None:
    op.execute("drop trigger if exists trg_tenants_seed_units_of_measure on admin.tenants")
    op.execute("drop function if exists admin.seed_default_units_of_measure()")
    op.execute("delete from admin.role_permissions where permission_id in (select id from admin.permissions where code in ('admin.unit.read','admin.unit.create','admin.unit.update'))")
    op.execute("delete from admin.permissions where code in ('admin.unit.read','admin.unit.create','admin.unit.update')")
    op.drop_index("ix_units_of_measure_tenant_status_name", table_name="units_of_measure", schema="admin")
    op.drop_table("units_of_measure", schema="admin")
