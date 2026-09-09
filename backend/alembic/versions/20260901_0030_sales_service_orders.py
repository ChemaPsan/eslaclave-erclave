"""Sales service-order execution lifecycle and service defaults.

Revision ID: 20260901_0030
Revises: 20260825_0029
"""
from alembic import op
import sqlalchemy as sa


revision: str = "20260901_0030"
down_revision: str | None = "20260825_0029"
branch_labels = None
depends_on = None


SEQUENCES = (
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

PERMISSIONS = (
    "sales.service_order.read", "sales.service_order.plan", "sales.service_order.assign",
    "sales.service_order.start", "sales.service_order.wait", "sales.service_order.resume",
    "sales.service_order.submit_acceptance", "sales.service_order.accept", "sales.service_order.cancel",
    "sales.service_order.time.create", "sales.service_order.cost.create", "sales.service_order.evidence.create",
)


def _values_sql():
    quoted = lambda value: "'" + value.replace("'", "''") + "'"
    return ",".join(f"({quoted(a)},{quoted(b)},{quoted(c)},{quoted(d)},{quoted(e)})" for a, b, c, d, e in SEQUENCES)


def upgrade() -> None:
    op.create_table(
        "service_orders",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(60), nullable=False), sa.Column("order_id", sa.String(40), nullable=False),
        sa.Column("order_line_id", sa.String(40), nullable=False), sa.Column("order_code_snapshot", sa.String(60), nullable=False),
        sa.Column("customer_id", sa.String(40), nullable=False), sa.Column("customer_name_snapshot", sa.String(240), nullable=False),
        sa.Column("product_service_ref_id", sa.String(40), nullable=False), sa.Column("product_service_code", sa.String(60), nullable=False),
        sa.Column("product_service_name", sa.String(240), nullable=False), sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(18, 6), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("responsible_worker_ref_id", sa.String(40)), sa.Column("responsible_worker_name", sa.String(240)),
        sa.Column("planned_start_date", sa.Date()), sa.Column("planned_end_date", sa.Date()), sa.Column("notes", sa.Text()),
        sa.Column("actual_cost", sa.Numeric(18, 2)), sa.Column("planned_at", sa.DateTime(timezone=True)),
        sa.Column("assigned_at", sa.DateTime(timezone=True)), sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("acceptance_requested_at", sa.DateTime(timezone=True)), sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("ordered_quantity > 0", name="ck_sales_service_order_quantity"),
        sa.CheckConstraint("status in ('draft','planned','assigned','in_progress','on_hold','pending_acceptance','accepted','cancelled')", name="ck_sales_service_order_status"),
        sa.CheckConstraint("planned_end_date is null or planned_start_date is not null", name="ck_sales_service_order_plan_start"),
        sa.CheckConstraint("planned_end_date is null or planned_end_date >= planned_start_date", name="ck_sales_service_order_plan_dates"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_sales_service_order_tenant_id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sales_service_order_code"),
        sa.UniqueConstraint("tenant_id", "order_line_id", name="uq_sales_service_order_line"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["sales.orders.tenant_id", "sales.orders.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "order_line_id"], ["sales.order_lines.tenant_id", "sales.order_lines.id"]), schema="sales",
    )
    op.create_index("ix_sales_service_orders_search", "service_orders", ["tenant_id", "status", "created_at"], schema="sales")
    op.create_index("ix_sales_service_orders_customer", "service_orders", ["tenant_id", "customer_id", "created_at"], schema="sales")
    op.create_table(
        "service_time_entries",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("service_order_id", sa.String(40), nullable=False), sa.Column("worker_ref_id", sa.String(40), nullable=False),
        sa.Column("worker_name", sa.String(240), nullable=False), sa.Column("worked_on", sa.Date(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False), sa.Column("hourly_cost", sa.Numeric(18, 6), nullable=False),
        sa.Column("total_cost", sa.Numeric(18, 2), nullable=False), sa.Column("notes", sa.Text()),
        sa.Column("created_by_actor_id", sa.String(128), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("minutes > 0 and minutes <= 1440 and hourly_cost >= 0 and total_cost >= 0", name="ck_sales_service_time_values"),
        sa.ForeignKeyConstraint(["tenant_id", "service_order_id"], ["sales.service_orders.tenant_id", "sales.service_orders.id"], ondelete="CASCADE"), schema="sales",
    )
    op.create_index("ix_sales_service_time_order", "service_time_entries", ["tenant_id", "service_order_id", "worked_on"], schema="sales")
    op.create_table(
        "service_cost_entries",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("service_order_id", sa.String(40), nullable=False), sa.Column("cost_type", sa.String(20), nullable=False),
        sa.Column("description", sa.String(300), nullable=False), sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 6), nullable=False), sa.Column("total_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("evidence_reference", sa.String(500)), sa.Column("created_by_actor_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("cost_type in ('labor','material','external','other')", name="ck_sales_service_cost_type"),
        sa.CheckConstraint("quantity > 0 and unit_cost >= 0 and total_cost >= 0", name="ck_sales_service_cost_values"),
        sa.ForeignKeyConstraint(["tenant_id", "service_order_id"], ["sales.service_orders.tenant_id", "sales.service_orders.id"], ondelete="CASCADE"), schema="sales",
    )
    op.create_index("ix_sales_service_cost_order", "service_cost_entries", ["tenant_id", "service_order_id", "created_at"], schema="sales")
    op.create_table(
        "service_evidence",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("service_order_id", sa.String(40), nullable=False), sa.Column("evidence_reference", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("created_by_actor_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id", "service_order_id"], ["sales.service_orders.tenant_id", "sales.service_orders.id"], ondelete="CASCADE"), schema="sales",
    )
    op.create_index("ix_sales_service_evidence_order", "service_evidence", ["tenant_id", "service_order_id", "created_at"], schema="sales")

    # Tighten the already-supported Purchasing service-line discriminator.
    op.execute("update purchasing.requisition_lines set inventory_item_ref_id=null where line_type='service' and inventory_item_ref_id is not null")
    op.execute("update purchasing.purchase_order_lines set inventory_item_ref_id=null where line_type='service' and inventory_item_ref_id is not null")
    op.drop_constraint("ck_purchasing_req_line_reference", "requisition_lines", schema="purchasing", type_="check")
    op.create_check_constraint("ck_purchasing_req_line_reference", "requisition_lines", "(line_type='inventory_item' and inventory_item_ref_id is not null) or (line_type='service' and inventory_item_ref_id is null)", schema="purchasing")
    op.create_check_constraint("ck_purchasing_order_line_reference", "purchase_order_lines", "(line_type='inventory_item' and inventory_item_ref_id is not null) or (line_type='service' and inventory_item_ref_id is null)", schema="purchasing")
    op.alter_column("purchase_receipt_lines", "warehouse_ref_id", existing_type=sa.String(40), nullable=True, schema="purchasing")

    connection = op.get_bind()
    values_sql = _values_sql()
    connection.exec_driver_sql(f"""create or replace function admin.seed_default_code_sequences() returns trigger language plpgsql as $$
        begin
          insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
          select 'seq_'||substr(md5(new.id||':'||seed.document_type),1,26),new.id,seed.document_type,seed.module_code,seed.name_es,seed.name_en,seed.prefix,'-',1,6,'managed',true,'active'
          from (values {values_sql}) as seed(document_type,module_code,name_es,name_en,prefix)
          on conflict(tenant_id,document_type) do nothing;
          return new;
        end $$""")
    connection.exec_driver_sql("""insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
        select 'seq_'||substr(md5(t.id||':sales.service_order'),1,26),t.id,'sales.service_order','sales','Orden de servicio','Service order','OS','-',1,6,'managed',true,'active'
        from admin.tenants t on conflict(tenant_id,document_type) do nothing""")
    connection.exec_driver_sql("""insert into admin.units_of_measure(id,tenant_id,code,name_es,name_en,symbol,category,decimal_places,system_default,status)
        select 'uom_'||substr(md5(t.id||':E48'),1,26),t.id,'E48','Unidad de servicio','Service unit','serv','service',3,true,'active'
        from admin.tenants t on conflict(tenant_id,code) do nothing""")
    connection.exec_driver_sql("""create function admin.seed_service_unit() returns trigger language plpgsql as $$ begin
        insert into admin.units_of_measure(id,tenant_id,code,name_es,name_en,symbol,category,decimal_places,system_default,status)
        values('uom_'||substr(md5(new.id||':E48'),1,26),new.id,'E48','Unidad de servicio','Service unit','serv','service',3,true,'active')
        on conflict(tenant_id,code) do nothing; return new; end $$""")
    connection.exec_driver_sql("create trigger trg_tenants_seed_service_unit after insert on admin.tenants for each row execute function admin.seed_service_unit()")
    for index, code in enumerate(PERMISSIONS, start=1160):
        resource, action = code.removeprefix("sales.").rsplit(".", 1)
        action_es = {"read": "Ver", "plan": "Planear", "assign": "Asignar", "start": "Iniciar", "wait": "Poner en espera", "resume": "Reanudar", "submit_acceptance": "Enviar a aceptacion", "accept": "Aceptar", "cancel": "Cancelar", "create": "Crear"}[action]
        action_en = {"read": "View", "plan": "Plan", "assign": "Assign", "start": "Start", "wait": "Put on hold", "resume": "Resume", "submit_acceptance": "Submit for acceptance", "accept": "Accept", "cancel": "Cancel", "create": "Create"}[action]
        resource_es = {"service_order": "ordenes de servicio", "service_order.time": "tiempos de ordenes de servicio", "service_order.cost": "costos de ordenes de servicio", "service_order.evidence": "evidencias de ordenes de servicio"}[resource]
        resource_en = {"service_order": "service orders", "service_order.time": "service-order time entries", "service_order.cost": "service-order costs", "service_order.evidence": "service-order evidence"}[resource]
        label_es, label_en = f"{action_es} {resource_es}", f"{action_en} {resource_en}"
        connection.execute(sa.text("""insert into admin.permissions(id,code,module_code,resource,action,description,status,display_name_es,display_name_en,description_es,description_en,classification,assignable_to_tenant_role,risk_level,sort_order)
            values('per_'||substr(md5(:code),1,26),:code,'sales',:resource,:action,:description,'active',:label_es,:label_en,:description_es,:description_en,'tenant',true,:risk,:sort)
            on conflict(code) do nothing"""), {"code": code, "resource": resource, "action": action, "description": f"Allows {label_en.lower()}.", "label_es": label_es, "label_en": label_en,
            "description_es": f"Permite {label_es.lower()} dentro de Ventas.", "description_en": f"Allows users to {label_en.lower()} in Sales.", "risk": "high" if action in {"accept", "cancel"} else "standard", "sort": index})
    connection.execute(sa.text("""insert into admin.role_permissions(id,tenant_id,role_id,permission_id,scope)
        select 'rpe_'||substr(md5(r.tenant_id||':'||r.id||':'||p.id),1,26),r.tenant_id,r.id,p.id,'{}'::jsonb
        from admin.roles r cross join admin.permissions p where r.code='owner' and r.system_role=true and r.status='active' and p.code like 'sales.service_order.%'
        on conflict(tenant_id,role_id,permission_id) do nothing"""))


def downgrade() -> None:
    op.execute("drop trigger if exists trg_tenants_seed_service_unit on admin.tenants")
    op.execute("drop function if exists admin.seed_service_unit()")
    op.execute("delete from admin.role_permissions where permission_id in (select id from admin.permissions where code like 'sales.service_order.%')")
    op.execute("delete from admin.permissions where code like 'sales.service_order.%'")
    op.execute("delete from admin.units_of_measure where code='E48' and system_default=true")
    op.execute("delete from admin.code_sequences where document_type='sales.service_order' and system_default=true")
    old_values_sql = ",".join(
        "(" + ",".join("'" + value.replace("'", "''") + "'" for value in item) + ")" for item in SEQUENCES[:-1]
    )
    op.execute(sa.text(f"""create or replace function admin.seed_default_code_sequences() returns trigger language plpgsql as $$
        begin
          insert into admin.code_sequences(id,tenant_id,document_type,module_code,name_es,name_en,prefix,separator,next_number,padding,mode,system_default,status)
          select 'seq_'||substr(md5(new.id||':'||seed.document_type),1,26),new.id,seed.document_type,seed.module_code,seed.name_es,seed.name_en,seed.prefix,'-',1,6,'managed',true,'active'
          from (values {old_values_sql}) as seed(document_type,module_code,name_es,name_en,prefix)
          on conflict(tenant_id,document_type) do nothing; return new; end $$"""))
    op.drop_constraint("ck_purchasing_order_line_reference", "purchase_order_lines", schema="purchasing", type_="check")
    op.execute("""do $$ begin if exists(select 1 from purchasing.purchase_receipt_lines where warehouse_ref_id is null) then
        raise exception 'cannot downgrade: service receipt lines without warehouse exist'; end if; end $$""")
    op.alter_column("purchase_receipt_lines", "warehouse_ref_id", existing_type=sa.String(40), nullable=False, schema="purchasing")
    op.drop_constraint("ck_purchasing_req_line_reference", "requisition_lines", schema="purchasing", type_="check")
    op.create_check_constraint("ck_purchasing_req_line_reference", "requisition_lines", "(line_type='inventory_item' and inventory_item_ref_id is not null) or line_type='service'", schema="purchasing")
    for table in ("service_evidence", "service_cost_entries", "service_time_entries", "service_orders"):
        op.drop_table(table, schema="sales")
