"""Normalize unambiguous legacy unit aliases with an audit trail.

Revision ID: 20260821_0023
Revises: 20260821_0022
"""
from alembic import op
import sqlalchemy as sa

revision: str = "20260821_0023"
down_revision: str | None = "20260821_0022"
branch_labels = None
depends_on = None

CORRELATION_ID = "migration:20260821_0023"
UNIT_COLUMNS = (
    ("inventory", "items", "base_unit"),
    ("inventory", "movements", "unit"),
    ("inventory", "reservations", "unit"),
    ("production", "product_services", "base_unit"),
    ("production", "recipe_versions", "base_unit"),
    ("production", "recipe_resources", "unit"),
    ("production", "production_orders", "unit"),
    ("production", "production_order_resources", "unit"),
    ("production", "sales_order_requests", "unit"),
    ("sales", "quote_lines", "unit"),
    ("sales", "order_lines", "unit"),
    ("sales", "delivery_lines", "unit"),
)


def _target_code_sql(column: str) -> str:
    return f"case upper(btrim({column})) when 'LTS' then 'LTR' when 'MT' then 'MTR' end"


def upgrade() -> None:
    connection = op.get_bind()
    for schema, table, column in UNIT_COLUMNS:
        qualified_table = f"{schema}.{table}"
        resource_type = f"{qualified_table}.{column}"
        target_code = _target_code_sql(column)
        missing_targets = connection.execute(
            sa.text(
                f"""
                select distinct source.tenant_id, upper(btrim(source.{column})) as legacy_code,
                       {target_code.replace(column, f'source.{column}')} as target_code
                  from {qualified_table} source
                 where upper(btrim(source.{column})) in ('LTS', 'MT')
                   and not exists (
                       select 1
                         from admin.units_of_measure target
                        where target.tenant_id = source.tenant_id
                          and target.code = {target_code.replace(column, f'source.{column}')}
                          and target.status = 'active'
                   )
                """
            )
        ).mappings().all()
        if missing_targets:
            details = ", ".join(
                f"tenant={row['tenant_id']} {row['legacy_code']}->{row['target_code']}"
                for row in missing_targets
            )
            raise RuntimeError(f"Cannot normalize legacy unit aliases without active target units: {details}")

        connection.execute(
            sa.text(
                f"""
                insert into admin.audit_events (
                    id, tenant_id, actor_user_id, actor_type, action, resource_type,
                    resource_id, source_service, correlation_id, idempotency_key,
                    before_state, after_state, metadata
                )
                select
                    'aud_' || substr(md5(cast(:correlation_id as text) || ':' || cast(:resource_type as text) || ':' || source.id), 1, 26),
                    source.tenant_id,
                    null,
                    'system',
                    'migration.unit_alias.normalize',
                    cast(:resource_type as text),
                    source.id,
                    'alembic',
                    cast(:correlation_id as text),
                    null,
                    jsonb_build_object('column', cast(:column as text), 'code', source.{column}),
                    jsonb_build_object('column', cast(:column as text), 'code', {target_code}),
                    jsonb_build_object(
                        'revision', '20260821_0023',
                        'schema', cast(:schema as text),
                        'table', cast(:table as text),
                        'column', cast(:column as text),
                        'reason', 'unambiguous_legacy_unit_alias'
                    )
                  from {qualified_table} source
                 where upper(btrim(source.{column})) in ('LTS', 'MT')
                on conflict (id) do nothing
                """
            ),
            {
                "correlation_id": CORRELATION_ID,
                "resource_type": resource_type,
                "schema": schema,
                "table": table,
                "column": column,
            },
        )
        connection.execute(
            sa.text(
                f"""
                update {qualified_table}
                   set {column} = {target_code}
                 where upper(btrim({column})) in ('LTS', 'MT')
                """
            )
        )


def downgrade() -> None:
    connection = op.get_bind()
    for schema, table, column in reversed(UNIT_COLUMNS):
        qualified_table = f"{schema}.{table}"
        resource_type = f"{qualified_table}.{column}"
        connection.execute(
            sa.text(
                f"""
                update {qualified_table} source
                   set {column} = audit.before_state ->> 'code'
                  from admin.audit_events audit
                 where audit.correlation_id = :correlation_id
                   and audit.action = 'migration.unit_alias.normalize'
                   and audit.resource_type = :resource_type
                   and audit.tenant_id = source.tenant_id
                   and audit.resource_id = source.id
                   and source.{column} = audit.after_state ->> 'code'
                """
            ),
            {"correlation_id": CORRELATION_ID, "resource_type": resource_type},
        )
    connection.execute(
        sa.text(
            "delete from admin.audit_events "
            "where correlation_id = :correlation_id "
            "and action = 'migration.unit_alias.normalize'"
        ),
        {"correlation_id": CORRELATION_ID},
    )
