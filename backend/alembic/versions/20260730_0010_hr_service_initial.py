"""hr-service initial schema.

Revision ID: 20260730_0010
Revises: 20260730_0009
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260730_0010"
down_revision: str | None = "20260730_0009"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("create schema if not exists hr")
    op.create_table("labor_areas",
        sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),
        sa.Column("code",sa.String(80),nullable=False),sa.Column("name",sa.String(160),nullable=False),
        sa.Column("description",sa.Text()),sa.Column("status",sa.String(20),nullable=False,server_default="active"),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id","id",name="uq_hr_labor_area_tenant_id"),sa.UniqueConstraint("tenant_id","code",name="uq_hr_labor_area_code"),sa.CheckConstraint("status in ('active','inactive')",name="ck_hr_labor_area_status"),schema="hr")
    op.create_index("ix_hr_labor_areas_tenant_status","labor_areas",["tenant_id","status"],schema="hr")
    op.create_table("labor_roles",
        sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),sa.Column("labor_area_id",sa.String(40),nullable=False),
        sa.Column("position",sa.String(160),nullable=False),sa.Column("recipe_name",sa.String(160),nullable=False),
        sa.Column("resource_quantity",sa.Integer(),nullable=False,server_default="1"),sa.Column("minutes_per_resource",sa.Integer(),nullable=False,server_default="480"),
        sa.Column("hourly_cost",sa.Numeric(18,6),nullable=False,server_default="0"),sa.Column("intervenes_in_production",sa.Boolean(),nullable=False,server_default=sa.text("false")),
        sa.Column("status",sa.String(20),nullable=False,server_default="active"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id","labor_area_id","position",name="uq_hr_labor_role_area_position"),
        sa.CheckConstraint("resource_quantity > 0",name="ck_hr_labor_role_quantity"),sa.CheckConstraint("minutes_per_resource > 0",name="ck_hr_labor_role_minutes"),sa.CheckConstraint("hourly_cost >= 0",name="ck_hr_labor_role_cost"),sa.CheckConstraint("status in ('active','inactive')",name="ck_hr_labor_role_status"),
        sa.ForeignKeyConstraint(["tenant_id","labor_area_id"],["hr.labor_areas.tenant_id","hr.labor_areas.id"],name="fk_hr_labor_role_area_tenant"),schema="hr")
    op.create_index("ix_hr_labor_roles_tenant_area","labor_roles",["tenant_id","labor_area_id","status"],schema="hr")
    op.create_index("ix_hr_labor_roles_tenant_production","labor_roles",["tenant_id","intervenes_in_production","status"],schema="hr")
    op.create_table("idempotency_records",sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),sa.Column("operation",sa.String(120),nullable=False),sa.Column("idempotency_key",sa.String(200),nullable=False),sa.Column("request_hash",sa.String(64),nullable=False),sa.Column("response_payload",postgresql.JSONB()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),sa.UniqueConstraint("tenant_id","operation","idempotency_key",name="uq_hr_idempotency_scope"),schema="hr")
    op.create_table("audit_events",sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),sa.Column("actor_id",sa.String(80),nullable=False),sa.Column("action",sa.String(120),nullable=False),sa.Column("entity_type",sa.String(80),nullable=False),sa.Column("entity_id",sa.String(40),nullable=False),sa.Column("payload",postgresql.JSONB(),nullable=False,server_default=sa.text("'{}'::jsonb")),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),schema="hr")
    op.create_index("ix_hr_audit_tenant_created","audit_events",["tenant_id","created_at"],schema="hr")

def downgrade() -> None:
    op.drop_table("audit_events",schema="hr");op.drop_table("idempotency_records",schema="hr");op.drop_table("labor_roles",schema="hr");op.drop_table("labor_areas",schema="hr");op.execute("drop schema if exists hr")
