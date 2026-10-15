"""Admin-owned scoped document template overrides; corporate settings preserved."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260927_0039"
down_revision: str | None = "20260925_0038"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("scoped_settings",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        sa.Column("key", sa.String(160), nullable=False, primary_key=True),
        sa.Column("scope_type", sa.String(16), nullable=False, primary_key=True),
        sa.Column("scope_ref_id", sa.String(40), nullable=False, primary_key=True),
        sa.Column("value", JSONB(none_as_null=True), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("scope_type in ('society','division')", name="ck_scoped_settings_scope"),
        sa.CheckConstraint("key = 'document.template'", name="ck_scoped_settings_key"),
        sa.CheckConstraint("revision > 0", name="ck_scoped_settings_revision"), schema="admin")


def downgrade():
    op.execute("LOCK TABLE admin.scoped_settings IN ACCESS EXCLUSIVE MODE")
    op.execute("""DO $$ BEGIN IF EXISTS (SELECT 1 FROM admin.scoped_settings)
        THEN RAISE EXCEPTION 'Scoped configuration history exists; use forward-fix'; END IF; END $$""")
    op.drop_table("scoped_settings", schema="admin")
