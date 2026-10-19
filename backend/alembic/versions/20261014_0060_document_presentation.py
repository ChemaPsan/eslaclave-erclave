"""CC-17 immutable document presentation for quotes and production orders."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "20261014_0060"
down_revision: str | None = "20261012_0059"
branch_labels = None
depends_on = None

DOCUMENTS = (("sales", "quotes"), ("production", "production_orders"))


def upgrade():
    for schema, table in DOCUMENTS:
        op.add_column(table, sa.Column("presentation_snapshot", JSONB(), nullable=True), schema=schema)
        op.create_check_constraint(f"ck_cc17_{table}_presentation_object", table,
            "presentation_snapshot is null or jsonb_typeof(presentation_snapshot)='object'", schema=schema)


def downgrade():
    for schema, table in DOCUMENTS:
        op.execute(f"LOCK TABLE {schema}.{table} IN ACCESS EXCLUSIVE MODE")
        op.execute(f"DO $$ BEGIN IF EXISTS(SELECT 1 FROM {schema}.{table} WHERE presentation_snapshot IS NOT NULL) "
                   "THEN RAISE EXCEPTION 'CC17 presentation history exists; use forward-fix'; END IF; END $$")
    for schema, table in reversed(DOCUMENTS):
        op.drop_constraint(f"ck_cc17_{table}_presentation_object", table, type_="check", schema=schema)
        op.drop_column(table, "presentation_snapshot", schema=schema)
