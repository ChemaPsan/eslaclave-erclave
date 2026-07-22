"""production command idempotency records.

Revision ID: 20260721_0006
Revises: 20260721_0005
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260721_0006"
down_revision: str | None = "20260721_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(40), nullable=False),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("operation", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, server_default="processing"),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now() + interval '30 days'")),
        sa.CheckConstraint("state in ('processing', 'completed')", name="ck_production_idempotency_state"),
        sa.CheckConstraint("state <> 'completed' or (response_payload is not null and status_code is not null and completed_at is not null)", name="ck_production_idempotency_completed"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "operation", "idempotency_key", name="uq_production_idempotency_scope"),
        schema="production",
    )
    op.create_index("ix_production_idempotency_created", "idempotency_records", ["tenant_id", "created_at"], schema="production")
    op.create_index("ix_production_idempotency_expires", "idempotency_records", ["expires_at"], schema="production")


def downgrade() -> None:
    op.drop_index("ix_production_idempotency_created", table_name="idempotency_records", schema="production")
    op.drop_table("idempotency_records", schema="production")
    op.drop_index("ix_production_idempotency_expires", table_name="idempotency_records", schema="production")
