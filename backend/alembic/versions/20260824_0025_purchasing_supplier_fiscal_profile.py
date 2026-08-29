"""purchasing supplier fiscal profile.

Revision ID: 20260824_0025
Revises: 20260824_0024
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260824_0025"
down_revision: str | None = "20260824_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("tax_regime", sa.String(10)), schema="purchasing")
    op.add_column("suppliers", sa.Column("billing_email", sa.String(254)), schema="purchasing")
    op.add_column("suppliers", sa.Column("contact_name", sa.String(200)), schema="purchasing")
    op.add_column("suppliers", sa.Column("website", sa.String(300)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_street", sa.String(200)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_exterior_number", sa.String(40)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_interior_number", sa.String(40)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_neighborhood", sa.String(160)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_municipality", sa.String(160)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_state", sa.String(120)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_postal_code", sa.String(12)), schema="purchasing")
    op.add_column("suppliers", sa.Column("fiscal_country", sa.String(2)), schema="purchasing")
    op.execute("update purchasing.suppliers set tax_id=regexp_replace(upper(tax_id), '[[:space:]-]', '', 'g') where tax_id is not null")
    op.create_index(
        "uq_purchasing_supplier_tax_id",
        "suppliers",
        ["tenant_id", "tax_id"],
        unique=True,
        schema="purchasing",
        postgresql_where=sa.text("tax_id is not null"),
    )


def downgrade() -> None:
    op.drop_index("uq_purchasing_supplier_tax_id", table_name="suppliers", schema="purchasing")
    for column in [
        "fiscal_country", "fiscal_postal_code", "fiscal_state", "fiscal_municipality",
        "fiscal_neighborhood", "fiscal_interior_number", "fiscal_exterior_number", "fiscal_street",
        "website", "contact_name", "billing_email", "tax_regime",
    ]:
        op.drop_column("suppliers", column, schema="purchasing")
