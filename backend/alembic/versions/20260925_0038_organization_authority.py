"""Reviewed organization authority switch and optional fiscal address fields."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260925_0038"
down_revision: str | None = "20260922_0037"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fiscal_issuers", sa.Column("postal_code", sa.String(20)), schema="admin")
    op.add_column("fiscal_issuers", sa.Column("country_code", sa.String(2)), schema="admin")
    op.create_table(
        "organization_authorities",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("projection_hash", sa.String(64), nullable=False),
        sa.Column("source_profile", JSONB(), nullable=False),
        sa.Column("prior_shadow", JSONB(), nullable=False),
        sa.Column("operator", sa.String(120), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("length(source_hash)=64 and length(projection_hash)=64", name="ck_organization_authority_hashes"),
        schema="admin",
    )


def downgrade():
    op.execute("LOCK TABLE admin.organization_authorities, admin.fiscal_issuers IN ACCESS EXCLUSIVE MODE")
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM admin.organization_authorities)
         OR EXISTS (SELECT 1 FROM admin.fiscal_issuers WHERE postal_code IS NOT NULL OR country_code IS NOT NULL)
      THEN RAISE EXCEPTION 'Organization authority is active or fiscal data exists; use forward-fix'; END IF;
    END $$""")
    op.drop_table("organization_authorities", schema="admin")
    op.drop_column("fiscal_issuers", "country_code", schema="admin")
    op.drop_column("fiscal_issuers", "postal_code", schema="admin")
