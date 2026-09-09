"""Narrow authority for releasing reservations after failed order creation."""
from alembic import op
import sqlalchemy as sa

revision: str = "20260908_0034"
down_revision: str | None = "20260908_0033"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("reservation_source_rollbacks",
        sa.Column("tenant_id",sa.String(40),primary_key=True),sa.Column("source_id",sa.String(40),primary_key=True),
        sa.Column("actor_id",sa.String(128),nullable=False),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),schema="inventory")
    op.create_table("failed_order_creations",
        sa.Column("tenant_id",sa.String(40),primary_key=True),sa.Column("order_id",sa.String(40),primary_key=True),
        sa.Column("code",sa.String(80),nullable=False),sa.Column("actor_id",sa.String(128),nullable=False),
        sa.Column("status",sa.String(32),nullable=False,server_default="pending"),sa.Column("error_code",sa.String(120)),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
        sa.Column("recovered_at",sa.DateTime(timezone=True)),
        sa.CheckConstraint("status in ('pending','recovered')",name="ck_production_failed_creation_status"),schema="production")
    op.create_index("ix_production_failed_creation_actor","failed_order_creations",["tenant_id","actor_id","status","created_at"],schema="production")


def downgrade():
    has_rollbacks=sa.inspect(op.get_bind()).has_table("reservation_source_rollbacks",schema="inventory")
    if has_rollbacks and op.get_bind().execute(sa.text("select 1 from inventory.reservation_source_rollbacks limit 1")).first():
        raise RuntimeError("Reservation rollback tombstones must be preserved before downgrade.")
    if op.get_bind().execute(sa.text("select 1 from production.failed_order_creations where status='pending' limit 1")).first():
        raise RuntimeError("Recover pending creation reservations before downgrade.")
    op.drop_table("failed_order_creations",schema="production")
    if has_rollbacks:op.drop_table("reservation_source_rollbacks",schema="inventory")
