"""CC-15 Purchasing document context and explicit commercial snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20261012_0058"
down_revision: str | None = "20261012_0057"
branch_labels = None
depends_on = None

SNAPSHOTS = (
    ("requisitions", "organization_context"),
    ("purchase_orders", "organization_context"),
    ("purchase_orders", "commercial_terms_snapshot"),
    ("purchase_receipts", "organization_context"),
)
DOCUMENTS = ("requisitions", "purchase_orders", "purchase_receipts")


def upgrade():
    for table, column in SNAPSHOTS:
        op.add_column(table, sa.Column(column, JSONB(), nullable=True), schema="purchasing")
        op.create_check_constraint(f"ck_cc15_{table}_{column}", table,
            f"{column} is null or jsonb_typeof({column})='object'", schema="purchasing")
    for table in DOCUMENTS:
        op.create_index(f"ix_cc15_{table}_division", table,
            ["tenant_id", sa.text("(organization_context->>'division_ref_id')")], schema="purchasing")


def downgrade():
    # Preserve immutable document history once this expansion has been used.
    for table in DOCUMENTS:
        op.execute(f"LOCK TABLE purchasing.{table} IN ACCESS EXCLUSIVE MODE")
    for table, column in SNAPSHOTS:
        op.execute(f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM purchasing.{table} WHERE {column} IS NOT NULL) THEN RAISE EXCEPTION 'CC15 history exists; use forward-fix'; END IF; END $$")
    for table in reversed(DOCUMENTS):
        op.drop_index(f"ix_cc15_{table}_division", table_name=table, schema="purchasing")
    for table, column in reversed(SNAPSHOTS):
        op.drop_constraint(f"ck_cc15_{table}_{column}", table, type_="check", schema="purchasing")
        op.drop_column(table, column, schema="purchasing")
