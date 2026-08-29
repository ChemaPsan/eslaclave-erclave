"""maintenance corrective cycle.

Revision ID: 20260824_0027
Revises: 20260824_0026
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260824_0027"
down_revision: str | None = "20260824_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("labor_roles", sa.Column("intervenes_in_maintenance", sa.Boolean(), nullable=False, server_default=sa.false()), schema="hr")
    op.add_column("machines", sa.Column("maintenance_order_ref_id", sa.String(40)), schema="production")
    op.execute("CREATE SCHEMA IF NOT EXISTS maintenance")
    op.create_table(
        "orders",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("production_machine_ref_id", sa.String(40)),
        sa.Column("machine_code_snapshot", sa.String(80)),
        sa.Column("machine_name_snapshot", sa.String(240)),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("source_production_order_ref_id", sa.String(40)),
        sa.Column("source_production_order_code_snapshot", sa.String(80)),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(300), nullable=False),
        sa.Column("safety_notes", sa.Text()),
        sa.Column("diagnosis", sa.Text()),
        sa.Column("root_cause", sa.Text()),
        sa.Column("work_performed", sa.Text()),
        sa.Column("verification_notes", sa.Text()),
        sa.Column("assigned_worker_ref_id", sa.String(40)),
        sa.Column("assigned_worker_name_snapshot", sa.String(240)),
        sa.Column("integration_status", sa.String(32), nullable=False, server_default="not_required"),
        sa.Column("integration_error", sa.Text()),
        sa.Column("requested_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_actor_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('draft','requested','assigned','in_progress','waiting_parts','resolved','closed','cancelled')", name="ck_maintenance_order_status"),
        sa.CheckConstraint("target_type in ('production_machine','facility','other')", name="ck_maintenance_order_target"),
        sa.CheckConstraint("source_type in ('manual','production_order')", name="ck_maintenance_order_source"),
        sa.CheckConstraint("priority in ('low','medium','high','critical')", name="ck_maintenance_order_priority"),
        sa.CheckConstraint("integration_status in ('not_required','processing','completed','needs_reconciliation')", name="ck_maintenance_order_integration"),
        sa.CheckConstraint("(target_type='production_machine' and production_machine_ref_id is not null) or (target_type<>'production_machine' and production_machine_ref_id is null)", name="ck_maintenance_order_target_reference"),
        sa.CheckConstraint("(source_type='production_order' and source_production_order_ref_id is not null) or source_type='manual'", name="ck_maintenance_order_source_reference"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_maintenance_order_code"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_maintenance_order_tenant_id"),
        schema="maintenance",
    )
    op.create_index("ix_maintenance_orders_search", "orders", ["tenant_id", "status", "priority", "created_at"], schema="maintenance")
    op.execute("CREATE UNIQUE INDEX uq_maintenance_active_machine ON maintenance.orders(tenant_id, production_machine_ref_id) WHERE production_machine_ref_id IS NOT NULL AND status IN ('requested','assigned','in_progress','waiting_parts')")
    op.create_table(
        "assignments",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("order_id", sa.String(40), nullable=False), sa.Column("worker_ref_id", sa.String(40), nullable=False),
        sa.Column("worker_name_snapshot", sa.String(240), nullable=False), sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("assigned_by_actor_id", sa.String(128), nullable=False), sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["maintenance.orders.tenant_id", "maintenance.orders.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "order_id", "worker_ref_id", name="uq_maintenance_assignment_worker"), schema="maintenance",
    )
    op.create_table(
        "time_entries",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("order_id", sa.String(40), nullable=False), sa.Column("worker_ref_id", sa.String(40), nullable=False),
        sa.Column("worker_name_snapshot", sa.String(240), nullable=False), sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False), sa.Column("minutes", sa.Integer(), nullable=False), sa.Column("notes", sa.Text()),
        sa.Column("created_by_actor_id", sa.String(128), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("minutes > 0", name="ck_maintenance_time_minutes"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["maintenance.orders.tenant_id", "maintenance.orders.id"], ondelete="CASCADE"),
        schema="maintenance",
    )
    op.create_index("ix_maintenance_time_worker", "time_entries", ["tenant_id", "worker_ref_id", "started_at"], schema="maintenance")
    op.create_table(
        "material_requests",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("order_id", sa.String(40), nullable=False), sa.Column("warehouse_ref_id", sa.String(40), nullable=False),
        sa.Column("warehouse_name_snapshot", sa.String(240), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="processing"),
        sa.Column("integration_error", sa.Text()), sa.Column("requested_by_actor_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status in ('processing','reserved','issued','cancelled','needs_reconciliation')", name="ck_maintenance_material_request_status"),
        sa.ForeignKeyConstraint(["tenant_id", "order_id"], ["maintenance.orders.tenant_id", "maintenance.orders.id"]),
        sa.UniqueConstraint("tenant_id", "id", name="uq_maintenance_material_request_tenant_id"), schema="maintenance",
    )
    op.create_table(
        "material_request_lines",
        sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("material_request_id", sa.String(40), nullable=False), sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("inventory_item_ref_id", sa.String(40), nullable=False), sa.Column("item_code_snapshot", sa.String(80), nullable=False),
        sa.Column("item_name_snapshot", sa.String(240), nullable=False), sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit_code", sa.String(20), nullable=False), sa.Column("reservation_ref_id", sa.String(40)),
        sa.Column("inventory_movement_ref_id", sa.String(40)), sa.Column("unit_cost_snapshot", sa.Numeric(18, 6)),
        sa.Column("line_status", sa.String(24), nullable=False, server_default="pending"),
        sa.CheckConstraint("quantity > 0", name="ck_maintenance_material_line_quantity"),
        sa.CheckConstraint("line_status in ('pending','reserved','issued','released','failed')", name="ck_maintenance_material_line_status"),
        sa.ForeignKeyConstraint(["tenant_id", "material_request_id"], ["maintenance.material_requests.tenant_id", "maintenance.material_requests.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "material_request_id", "line_number", name="uq_maintenance_material_line_number"), schema="maintenance",
    )
    op.create_table("idempotency_records", sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("operation", sa.String(100), nullable=False), sa.Column("idempotency_key", sa.String(200), nullable=False), sa.Column("request_hash", sa.String(64), nullable=False), sa.Column("response_payload", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_maintenance_idempotency"), schema="maintenance")
    op.create_table("audit_events", sa.Column("id", sa.String(40), primary_key=True), sa.Column("tenant_id", sa.String(40), nullable=False), sa.Column("actor_id", sa.String(128), nullable=False), sa.Column("action", sa.String(100), nullable=False), sa.Column("entity_type", sa.String(80), nullable=False), sa.Column("entity_id", sa.String(40), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), schema="maintenance")


def downgrade() -> None:
    for table in ["audit_events", "idempotency_records", "material_request_lines", "material_requests", "time_entries", "assignments", "orders"]:
        op.drop_table(table, schema="maintenance")
    op.execute("DROP SCHEMA IF EXISTS maintenance")
    op.drop_column("machines", "maintenance_order_ref_id", schema="production")
    op.drop_column("labor_roles", "intervenes_in_maintenance", schema="hr")
