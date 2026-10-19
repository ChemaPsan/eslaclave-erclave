"""Basic cost-center catalog; no analytical Costing or Accounting activation."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision: str = "20260927_0040"
down_revision: str | None = "20260927_0039"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS costing")
    op.create_table("cost_centers",
        sa.Column("tenant_id",sa.String(40),primary_key=True),sa.Column("id",sa.String(40),primary_key=True),
        sa.Column("code",sa.String(80),nullable=False),sa.Column("name",sa.String(240),nullable=False),
        sa.Column("division_ref_id",sa.String(40),nullable=False),sa.Column("status",sa.String(16),nullable=False),sa.Column("revision",sa.Integer(),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id","code",name="uq_cost_centers_code"),
        sa.CheckConstraint("status in ('active','inactive')",name="ck_cost_centers_status"),
        sa.CheckConstraint("revision > 0 and length(trim(name)) > 0 and length(trim(code)) > 0",name="ck_cost_centers_identity"),schema="costing")
    op.create_index("ix_cost_centers_division","cost_centers",["tenant_id","division_ref_id","status"],schema="costing")
    op.create_table("command_receipts",sa.Column("tenant_id",sa.String(40),primary_key=True),sa.Column("key",sa.String(160),primary_key=True),
        sa.Column("request_hash",sa.String(64),nullable=False),sa.Column("response",JSONB,nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),schema="costing")
    op.create_table("audit_events",sa.Column("tenant_id",sa.String(40),primary_key=True),sa.Column("id",sa.String(40),primary_key=True),
        sa.Column("actor_id",sa.String(40),nullable=False),sa.Column("action",sa.String(80),nullable=False),sa.Column("entity_id",sa.String(40),nullable=False),
        sa.Column("before_state",JSONB),sa.Column("after_state",JSONB,nullable=False),sa.Column("correlation_id",sa.String(160),nullable=False),sa.Column("idempotency_key",sa.String(160),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),schema="costing")
    op.create_index("ix_costing_audit_entity","audit_events",["tenant_id","entity_id","created_at"],schema="costing")

def downgrade():
    op.execute("LOCK TABLE costing.cost_centers,costing.command_receipts,costing.audit_events IN ACCESS EXCLUSIVE MODE")
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM costing.cost_centers) OR EXISTS (SELECT 1 FROM costing.command_receipts) OR EXISTS (SELECT 1 FROM costing.audit_events)
    THEN RAISE EXCEPTION 'Cost center history exists; use forward-fix'; END IF; END $$""")
    op.drop_table("audit_events",schema="costing");op.drop_table("command_receipts",schema="costing");op.drop_table("cost_centers",schema="costing")
