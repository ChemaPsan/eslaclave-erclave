"""Written service evidence and expiring private attachment references."""
from alembic import op
import sqlalchemy as sa

revision: str = "20260913_0036"
down_revision: str | None = "20260913_0035"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("service_evidence",
        sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),
        sa.Column("order_id",sa.String(40),nullable=False),sa.Column("phase",sa.String(10),nullable=False),
        sa.Column("description",sa.Text(),nullable=False),sa.Column("request_hash",sa.String(64),nullable=False),
        sa.Column("actor_id",sa.String(128),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.text("now()"),nullable=False),
        sa.UniqueConstraint("tenant_id","order_id","phase",name="uq_service_evidence_phase"),
        sa.UniqueConstraint("tenant_id","id",name="uq_service_evidence_tenant_id"),
        sa.CheckConstraint("phase in ('start','finish')",name="ck_service_evidence_phase"),
        sa.CheckConstraint("length(trim(description)) between 3 and 4000",name="ck_service_evidence_description"),
        sa.ForeignKeyConstraint(["tenant_id","order_id"],["production.production_orders.tenant_id","production.production_orders.id"]),schema="production")
    op.create_table("service_evidence_files",
        sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),
        sa.Column("evidence_id",sa.String(40),nullable=False),sa.Column("filename",sa.String(180),nullable=False),
        sa.Column("media_type",sa.String(100),nullable=False),sa.Column("size_bytes",sa.Integer(),nullable=False),
        sa.Column("sha256",sa.String(64),nullable=False),sa.Column("object_key",sa.String(200),nullable=True),
        sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("deleted_at",sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id","evidence_id"],["production.service_evidence.tenant_id","production.service_evidence.id"]),
        sa.CheckConstraint("size_bytes > 0 and size_bytes <= 2097152",name="ck_service_evidence_file_size"),schema="production")
    op.create_index("ix_service_evidence_expiry","service_evidence_files",["expires_at"],schema="production",postgresql_where=sa.text("deleted_at is null"))
    op.create_index("ix_service_evidence_files_owner","service_evidence_files",["tenant_id","evidence_id"],schema="production")


def downgrade():
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM production.service_evidence) THEN
        RAISE EXCEPTION 'Service evidence exists; archive explicitly before rollback'; END IF; END $$""")
    op.drop_table("service_evidence_files",schema="production")
    op.drop_table("service_evidence",schema="production")
