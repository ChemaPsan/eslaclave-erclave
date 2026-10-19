"""CONT-01: tenant-safe organization, one issuer per society; compatible expansion.

No automatic data backfill and no change to organization.profile readers/writers.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20260922_0037"
down_revision: str | None = "20260913_0036"
branch_labels = None
depends_on = None


def identity_columns():
    return [
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["admin.tenants.id"], ondelete="RESTRICT"),
    ]


def upgrade() -> None:
    op.create_table(
        "fiscal_issuers",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        *identity_columns(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("legal_name", sa.String(240), nullable=False),
        sa.Column("tax_id", sa.String(80)),
        sa.Column("fiscal_regime", sa.String(80)),
        sa.Column("cfdi_usage", sa.String(80)),
        sa.Column("fiscal_address", sa.Text()),
        sa.Column("contact", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_fiscal_issuers_code"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_fiscal_issuers_status"),
        sa.CheckConstraint("length(trim(code)) > 0 and length(trim(legal_name)) > 0", name="ck_fiscal_issuers_identity"),
        schema="admin",
    )
    op.create_index("ix_fiscal_issuers_tenant_status", "fiscal_issuers", ["tenant_id", "status"], schema="admin")
    op.create_table(
        "societies",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        *identity_columns(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("issuer_id", sa.String(40), nullable=False),
        sa.Column("base_currency", sa.String(40), nullable=False, server_default="MXN"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_societies_code"),
        sa.UniqueConstraint("tenant_id", "id", "issuer_id", name="uq_societies_issuer"),
        sa.ForeignKeyConstraint(["tenant_id", "issuer_id"], ["admin.fiscal_issuers.tenant_id", "admin.fiscal_issuers.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_societies_status"),
        sa.CheckConstraint("length(trim(code)) > 0 and length(trim(name)) > 0", name="ck_societies_identity"),
        sa.CheckConstraint("length(trim(base_currency)) > 0", name="ck_societies_currency"),
        schema="admin",
    )
    op.create_index("ix_societies_tenant_issuer", "societies", ["tenant_id", "issuer_id"], schema="admin")
    op.create_index("ix_societies_tenant_status", "societies", ["tenant_id", "status"], schema="admin")
    op.create_table(
        "divisions",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        *identity_columns(),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("society_id", sa.String(40), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("phone", sa.String(80)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_divisions_code"),
        sa.UniqueConstraint("tenant_id", "id", "society_id", name="uq_divisions_society"),
        sa.ForeignKeyConstraint(["tenant_id", "society_id"], ["admin.societies.tenant_id", "admin.societies.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("status in ('active','inactive')", name="ck_divisions_status"),
        sa.CheckConstraint("length(trim(code)) > 0 and length(trim(name)) > 0", name="ck_divisions_identity"),
        schema="admin",
    )
    op.create_index("ix_divisions_tenant_society", "divisions", ["tenant_id", "society_id"], schema="admin")
    op.create_index("ix_divisions_tenant_status", "divisions", ["tenant_id", "status"], schema="admin")
    op.create_table(
        "organization_imports",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        *identity_columns(),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("plan_hash", sa.String(64), nullable=False),
        sa.Column("source_profile", JSONB(), nullable=False),
        sa.Column("resolutions", JSONB(), nullable=False),
        sa.Column("operator", sa.String(120), nullable=False),
        sa.Column("correlation_id", sa.String(120), nullable=False),
        sa.UniqueConstraint("tenant_id", name="uq_organization_import_tenant"),
        sa.CheckConstraint("length(source_hash) = 64 and length(plan_hash) = 64", name="ck_organization_import_hashes"),
        schema="admin",
    )
    op.create_table(
        "organization_legacy_mappings",
        sa.Column("tenant_id", sa.String(40), nullable=False, primary_key=True),
        sa.Column("collection", sa.String(20), primary_key=True),
        sa.Column("legacy_id", sa.String(120), primary_key=True),
        sa.Column("import_id", sa.String(40), nullable=False),
        sa.Column("society_id", sa.String(40), nullable=False),
        sa.Column("issuer_id", sa.String(40)),
        sa.Column("division_id", sa.String(40)),
        sa.Column("source_item", JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id", "import_id"], ["admin.organization_imports.tenant_id", "admin.organization_imports.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "society_id"], ["admin.societies.tenant_id", "admin.societies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "society_id", "issuer_id"], ["admin.societies.tenant_id", "admin.societies.id", "admin.societies.issuer_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id", "division_id", "society_id"], ["admin.divisions.tenant_id", "admin.divisions.id", "admin.divisions.society_id"], ondelete="RESTRICT"),
        sa.CheckConstraint("(collection = 'legal_entities' and issuer_id is not null and division_id is null) or (collection = 'branches' and division_id is not null and issuer_id is null)", name="ck_organization_mapping_kind"),
        schema="admin",
    )
    op.create_index("ix_organization_mappings_import", "organization_legacy_mappings", ["tenant_id", "import_id"], schema="admin")


def downgrade() -> None:
    # Never discard a backfill, equivalence or data written after the future switch.
    op.execute("""LOCK TABLE admin.organization_imports, admin.organization_legacy_mappings,
        admin.divisions, admin.societies, admin.fiscal_issuers IN ACCESS EXCLUSIVE MODE""")
    op.execute("""DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM admin.organization_imports)
         OR EXISTS (SELECT 1 FROM admin.organization_legacy_mappings)
         OR EXISTS (SELECT 1 FROM admin.divisions)
         OR EXISTS (SELECT 1 FROM admin.societies)
         OR EXISTS (SELECT 1 FROM admin.fiscal_issuers) THEN
        RAISE EXCEPTION 'Organization data exists; preserve and reconcile before rollback';
      END IF;
    END $$""")
    op.drop_table("organization_legacy_mappings", schema="admin")
    op.drop_table("organization_imports", schema="admin")
    op.drop_table("divisions", schema="admin")
    op.drop_table("societies", schema="admin")
    op.drop_table("fiscal_issuers", schema="admin")
