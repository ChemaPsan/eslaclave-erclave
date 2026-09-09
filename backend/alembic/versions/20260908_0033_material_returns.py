"""Physical material returns with independently owned order adjustments."""
from alembic import op
import sqlalchemy as sa

revision: str = "20260908_0033"
down_revision: str | None = "20260908_0032"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("material_returns",
        sa.Column("id",sa.String(40),primary_key=True),sa.Column("tenant_id",sa.String(40),nullable=False),
        sa.Column("original_movement_id",sa.String(40),nullable=False),sa.Column("movement_id",sa.String(40)),
        sa.Column("source_type",sa.String(40),nullable=False),sa.Column("source_id",sa.String(40),nullable=False),
        sa.Column("source_code",sa.String(80),nullable=False),sa.Column("reservation_id",sa.String(40),nullable=False),
        sa.Column("quantity",sa.Numeric(18,6),nullable=False),sa.Column("reason",sa.String(500),nullable=False),
        sa.Column("status",sa.String(40),nullable=False,server_default="pending"),sa.Column("error_code",sa.String(120)),
        sa.Column("requested_by",sa.String(128),nullable=False),sa.Column("received_by",sa.String(128)),
        sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),sa.Column("received_at",sa.DateTime(timezone=True)),
        sa.CheckConstraint("quantity>0",name="ck_inventory_material_return_quantity"),
        sa.CheckConstraint("source_type in ('production_order','maintenance_order')",name="ck_inventory_material_return_source"),
        sa.CheckConstraint("status in ('pending','received_pending_reconciliation','completed','cancelled')",name="ck_inventory_material_return_status"),
        sa.ForeignKeyConstraint(["tenant_id","original_movement_id"],["inventory.movements.tenant_id","inventory.movements.id"]),
        sa.ForeignKeyConstraint(["tenant_id","movement_id"],["inventory.movements.tenant_id","inventory.movements.id"]),schema="inventory")
    op.create_index("ix_inventory_material_return_pending","material_returns",["tenant_id","status","created_at"],schema="inventory")
    op.create_index("ix_inventory_material_return_original","material_returns",["tenant_id","original_movement_id"],schema="inventory")
    for schema,table in (("production","production_orders"),("maintenance","orders")):
        op.create_table("material_return_adjustments",
            sa.Column("tenant_id",sa.String(40),primary_key=True),sa.Column("return_id",sa.String(40),primary_key=True),
            sa.Column("order_id",sa.String(40),nullable=False),sa.Column("resource_id",sa.String(40),nullable=False),
            sa.Column("original_movement_id",sa.String(40),nullable=False),sa.Column("movement_id",sa.String(40),nullable=False),
            sa.Column("quantity",sa.Numeric(18,6),nullable=False),sa.Column("unit_cost",sa.Numeric(18,6),nullable=False),
            sa.Column("actor_id",sa.String(128),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False,server_default=sa.text("now()")),
            sa.CheckConstraint("quantity>0 and unit_cost>=0",name=f"ck_{schema}_material_return_values"),
            sa.ForeignKeyConstraint(["tenant_id","order_id"],[f"{schema}.{table}.tenant_id",f"{schema}.{table}.id"]),schema=schema)
        op.create_index(f"ix_{schema}_material_return_order","material_return_adjustments",["tenant_id","order_id","resource_id"],schema=schema)


def downgrade():
    if op.get_bind().execute(sa.text("select 1 from inventory.material_returns limit 1")).first():
        raise RuntimeError("Material return history must be preserved before downgrade.")
    for schema in ("production","maintenance"):
        if op.get_bind().execute(sa.text(f"select 1 from {schema}.material_return_adjustments limit 1")).first():
            raise RuntimeError("Order return adjustments must be preserved before downgrade.")
        op.drop_table("material_return_adjustments",schema=schema)
    op.drop_table("material_returns",schema="inventory")
