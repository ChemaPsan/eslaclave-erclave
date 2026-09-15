"""Allow expected profit over cost above 100 percent without a numeric precision cap."""
from alembic import op
import sqlalchemy as sa

revision: str = "20260913_0035"
down_revision: str | None = "20260908_0034"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_product_services_expected_margin", "product_services", schema="production", type_="check")
    op.alter_column("product_services", "expected_margin", schema="production", existing_type=sa.Numeric(9, 4), type_=sa.Numeric(), existing_nullable=True)
    op.create_check_constraint("ck_product_services_expected_margin", "product_services", "expected_margin is null or (expected_margin >= 0 and expected_margin < 'Infinity'::numeric)", schema="production")


def downgrade():
    # Refuse a lossy rollback; do not clamp or round business values silently.
    op.execute("""DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM production.product_services WHERE expected_margin > 100 OR expected_margin <> round(expected_margin, 4)) THEN
            RAISE EXCEPTION 'Expected margins cannot fit the previous schema; resolve values explicitly before rollback';
        END IF;
    END $$""")
    op.drop_constraint("ck_product_services_expected_margin", "product_services", schema="production", type_="check")
    op.alter_column("product_services", "expected_margin", schema="production", existing_type=sa.Numeric(), type_=sa.Numeric(9, 4), existing_nullable=True)
    op.create_check_constraint("ck_product_services_expected_margin", "product_services", "expected_margin is null or (expected_margin >= 0 and expected_margin <= 100)", schema="production")
