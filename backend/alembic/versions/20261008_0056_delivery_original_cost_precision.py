"""Preserve six-decimal inventory cost before Sales currency conversion.

Existing historical amounts are preserved; lost precision is never inferred.
"""
from alembic import op
import sqlalchemy as sa
revision: str = "20261008_0056"
down_revision: str | None = "20261008_0055"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('delivery_lines', 'original_actual_cost', schema='sales',
                    existing_type=sa.Numeric(18, 2), type_=sa.Numeric(22, 6),
                    existing_nullable=True)


def downgrade():
    op.execute('LOCK TABLE sales.delivery_lines IN ACCESS EXCLUSIVE MODE')
    op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM sales.delivery_lines WHERE original_actual_cost != round(original_actual_cost, 2)) THEN RAISE EXCEPTION 'Original cost precision would be lost; use forward-fix'; END IF; END $$")
    op.alter_column('delivery_lines', 'original_actual_cost', schema='sales',
                    existing_type=sa.Numeric(22, 6), type_=sa.Numeric(18, 2),
                    existing_nullable=True)
