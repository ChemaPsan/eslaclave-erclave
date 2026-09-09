"""Durable warehouse issuance of production materials.

Revision ID: 20260908_0031
Revises: 20260901_0030
"""
from alembic import op

revision: str = "20260908_0031"
down_revision: str | None = "20260901_0030"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter table production.production_orders add constraint uq_production_orders_tenant_id unique(tenant_id,id)")
    op.execute("""create table production.material_issues (
        tenant_id varchar(40) not null,
        production_order_id varchar(40) not null,
        status varchar(32) not null check (status in ('processing','needs_reconciliation','issued')),
        movements jsonb not null default '{}'::jsonb,
        last_error_code varchar(120),
        authorized_by varchar(40) not null,
        created_at timestamptz not null default now(),
        updated_at timestamptz not null default now(),
        primary key (tenant_id,production_order_id),
        foreign key (tenant_id,production_order_id) references production.production_orders(tenant_id,id)
    )""")
    op.execute("create index ix_production_material_issues_pending on production.material_issues(tenant_id,status,created_at)")


def downgrade():
    op.execute("drop table production.material_issues")
    op.execute("alter table production.production_orders drop constraint uq_production_orders_tenant_id")
