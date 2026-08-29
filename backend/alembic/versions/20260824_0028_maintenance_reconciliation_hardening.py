"""maintenance reconciliation hardening.

Revision ID: 20260824_0028
Revises: 20260824_0027
"""
from alembic import op
import sqlalchemy as sa


revision: str = "20260824_0028"
down_revision: str | None = "20260824_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("integration_operation", sa.String(24)), schema="maintenance")
    op.add_column("orders", sa.Column("integration_attempts", sa.Integer(), nullable=False, server_default="0"), schema="maintenance")
    op.add_column("orders", sa.Column("last_integration_at", sa.DateTime(timezone=True)), schema="maintenance")
    op.create_check_constraint(
        "ck_maintenance_order_integration_operation", "orders",
        "integration_operation is null or integration_operation in ('block','release')", schema="maintenance",
    )
    op.drop_constraint("ck_maintenance_order_source_reference", "orders", schema="maintenance", type_="check")
    op.create_check_constraint(
        "ck_maintenance_order_source_reference", "orders",
        "(source_type='production_order' and source_production_order_ref_id is not null) or (source_type='manual' and source_production_order_ref_id is null)",
        schema="maintenance",
    )

    op.add_column("material_requests", sa.Column("pending_operation", sa.String(24)), schema="maintenance")
    op.add_column("material_requests", sa.Column("integration_attempts", sa.Integer(), nullable=False, server_default="0"), schema="maintenance")
    op.add_column("material_requests", sa.Column("last_integration_at", sa.DateTime(timezone=True)), schema="maintenance")
    op.create_check_constraint(
        "ck_maintenance_material_pending_operation", "material_requests",
        "pending_operation is null or pending_operation in ('reserve','issue','cancel')", schema="maintenance",
    )
    op.drop_constraint("ck_maintenance_material_request_status", "material_requests", schema="maintenance", type_="check")
    op.create_check_constraint(
        "ck_maintenance_material_request_status", "material_requests",
        "status in ('processing','reserved','issued','cancelling','cancelled','needs_reconciliation')", schema="maintenance",
    )

    op.execute("""
        update maintenance.assignments current
        set is_primary=false
        where current.is_primary and exists (
            select 1 from maintenance.assignments newer
            where newer.tenant_id=current.tenant_id and newer.order_id=current.order_id
              and newer.is_primary and (newer.assigned_at,newer.id)>(current.assigned_at,current.id)
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_maintenance_primary_assignment ON maintenance.assignments(tenant_id,order_id) WHERE is_primary")
    op.create_index("ix_maintenance_assignment_order", "assignments", ["tenant_id", "order_id"], schema="maintenance")
    op.create_index("ix_maintenance_time_order", "time_entries", ["tenant_id", "order_id"], schema="maintenance")
    op.create_index("ix_maintenance_material_order", "material_requests", ["tenant_id", "order_id"], schema="maintenance")


def downgrade() -> None:
    op.drop_index("ix_maintenance_material_order", table_name="material_requests", schema="maintenance")
    op.drop_index("ix_maintenance_time_order", table_name="time_entries", schema="maintenance")
    op.drop_index("ix_maintenance_assignment_order", table_name="assignments", schema="maintenance")
    op.execute("DROP INDEX IF EXISTS maintenance.uq_maintenance_primary_assignment")
    op.execute("update maintenance.material_requests set status='needs_reconciliation' where status='cancelling'")
    op.drop_constraint("ck_maintenance_material_request_status", "material_requests", schema="maintenance", type_="check")
    op.create_check_constraint(
        "ck_maintenance_material_request_status", "material_requests",
        "status in ('processing','reserved','issued','cancelled','needs_reconciliation')", schema="maintenance",
    )
    op.drop_constraint("ck_maintenance_material_pending_operation", "material_requests", schema="maintenance", type_="check")
    op.drop_column("material_requests", "last_integration_at", schema="maintenance")
    op.drop_column("material_requests", "integration_attempts", schema="maintenance")
    op.drop_column("material_requests", "pending_operation", schema="maintenance")

    op.drop_constraint("ck_maintenance_order_source_reference", "orders", schema="maintenance", type_="check")
    op.create_check_constraint(
        "ck_maintenance_order_source_reference", "orders",
        "(source_type='production_order' and source_production_order_ref_id is not null) or source_type='manual'",
        schema="maintenance",
    )
    op.drop_constraint("ck_maintenance_order_integration_operation", "orders", schema="maintenance", type_="check")
    op.drop_column("orders", "last_integration_at", schema="maintenance")
    op.drop_column("orders", "integration_attempts", schema="maintenance")
    op.drop_column("orders", "integration_operation", schema="maintenance")
