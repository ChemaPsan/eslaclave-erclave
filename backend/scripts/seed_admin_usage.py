from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import os
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine, text


def stable_usage_id(tenant_id: str, usage_date: date) -> str:
    return f"tud_{uuid5(NAMESPACE_URL, f'erclave.tenant_usage_daily:{tenant_id}:{usage_date.isoformat()}').hex[:26]}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate derived daily tenant usage metrics for admin-service.")
    parser.add_argument("--days", type=int, default=30, help="Number of days to populate ending today.")
    parser.add_argument("--tenant-id", default="", help="Optional tenant id to populate.")
    parser.add_argument("--dry-run", action="store_true", help="Print the rows that would be written.")
    return parser.parse_args()


def build_usage_rows(database_url: str, days: int, tenant_id: str = "") -> list[dict]:
    today = date.today()
    from_date = today - timedelta(days=max(1, days) - 1)
    params = {
        "from_date": from_date,
        "to_date": today,
        "tenant_id": tenant_id or None,
    }
    tenant_clause = "and tenants.id = :tenant_id" if tenant_id else ""
    engine = create_engine(database_url)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                with days as (
                    select generate_series(cast(:from_date as date), cast(:to_date as date), interval '1 day')::date as usage_date
                ),
                tenant_base as (
                    select
                        tenants.id as tenant_id,
                        tenants.slug,
                        tenants.status,
                        count(distinct memberships.id) filter (where memberships.status = 'active') as active_users,
                        count(distinct memberships.id) as total_users,
                        count(distinct tenant_modules.id) filter (where tenant_modules.status = 'active') as active_modules,
                        coalesce(sum(octet_length(tenant_settings.value::text)), 0) as settings_bytes
                    from admin.tenants tenants
                    left join admin.memberships memberships on memberships.tenant_id = tenants.id
                    left join admin.tenant_modules tenant_modules on tenant_modules.tenant_id = tenants.id
                    left join admin.tenant_settings tenant_settings on tenant_settings.tenant_id = tenants.id
                    where tenants.status in ('provisioning', 'active', 'suspended')
                    {tenant_clause}
                    group by tenants.id, tenants.slug, tenants.status
                ),
                audit_by_day as (
                    select
                        audit_events.tenant_id,
                        audit_events.occurred_at::date as usage_date,
                        count(*) as audit_events
                    from admin.audit_events audit_events
                    where audit_events.occurred_at::date between :from_date and :to_date
                    group by audit_events.tenant_id, audit_events.occurred_at::date
                )
                select
                    tenant_base.tenant_id,
                    tenant_base.slug,
                    days.usage_date,
                    greatest(tenant_base.active_users, 0)::int as active_users,
                    (
                        coalesce(audit_by_day.audit_events, 0)
                        + greatest(tenant_base.active_users, 0) * 8
                        + greatest(tenant_base.active_modules, 0) * 12
                        + case when tenant_base.status = 'active' then 10 else 2 end
                    )::int as api_requests,
                    round(
                        greatest(
                            (
                                tenant_base.settings_bytes
                                + greatest(tenant_base.total_users, 0) * 1024
                                + greatest(tenant_base.active_modules, 0) * 2048
                            )::numeric / 1048576,
                            0.01
                        ),
                        2
                    ) as storage_mb,
                    round(
                        (
                            greatest(tenant_base.active_users, 0) * 0.35
                            + (
                                coalesce(audit_by_day.audit_events, 0)
                                + greatest(tenant_base.active_users, 0) * 8
                                + greatest(tenant_base.active_modules, 0) * 12
                                + case when tenant_base.status = 'active' then 10 else 2 end
                            ) * 0.002
                            + greatest(tenant_base.active_modules, 0) * 0.15
                            + greatest(
                                (
                                    tenant_base.settings_bytes
                                    + greatest(tenant_base.total_users, 0) * 1024
                                    + greatest(tenant_base.active_modules, 0) * 2048
                                )::numeric / 1048576,
                                0.01
                            ) * 0.08
                        )::numeric,
                        2
                    ) as estimated_cost_mxn,
                    coalesce(audit_by_day.audit_events, 0)::int as audit_events,
                    tenant_base.active_modules::int as active_modules,
                    tenant_base.total_users::int as total_users
                from tenant_base
                cross join days
                left join audit_by_day
                    on audit_by_day.tenant_id = tenant_base.tenant_id
                    and audit_by_day.usage_date = days.usage_date
                order by days.usage_date desc, tenant_base.slug
                """
            ),
            params,
        ).mappings().all()

    return [
        {
            "id": stable_usage_id(row["tenant_id"], row["usage_date"]),
            "tenant_id": row["tenant_id"],
            "usage_date": row["usage_date"],
            "active_users": row["active_users"],
            "api_requests": row["api_requests"],
            "storage_mb": row["storage_mb"],
            "estimated_cost_mxn": row["estimated_cost_mxn"],
            "source": "derived_admin_snapshot",
            "metadata": {
                "formula": "active memberships, active modules, audit events and settings footprint",
                "audit_events": row["audit_events"],
                "active_modules": row["active_modules"],
                "total_users": row["total_users"],
                "tenant_slug": row["slug"],
            },
        }
        for row in rows
    ]


def upsert_usage_rows(database_url: str, rows: list[dict]) -> int:
    if not rows:
        return 0

    statement = text(
        """
        insert into admin.tenant_usage_daily (
            id,
            tenant_id,
            usage_date,
            active_users,
            api_requests,
            storage_mb,
            estimated_cost_mxn,
            source,
            metadata
        )
        values (
            :id,
            :tenant_id,
            :usage_date,
            :active_users,
            :api_requests,
            :storage_mb,
            :estimated_cost_mxn,
            :source,
            cast(:metadata as jsonb)
        )
        on conflict (tenant_id, usage_date) do update set
            active_users = excluded.active_users,
            api_requests = excluded.api_requests,
            storage_mb = excluded.storage_mb,
            estimated_cost_mxn = excluded.estimated_cost_mxn,
            source = excluded.source,
            metadata = excluded.metadata,
            updated_at = now()
        """
    )
    payload = [{**row, "metadata": json.dumps(row["metadata"])} for row in rows]
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(statement, payload)
    return len(rows)


def main() -> int:
    args = parse_args()
    database_url = os.getenv("ERCLAVE_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ERCLAVE_DATABASE_URL is required to populate tenant usage metrics.")

    rows = build_usage_rows(database_url, days=args.days, tenant_id=args.tenant_id)
    if args.dry_run:
        print(f"Would upsert {len(rows)} tenant usage rows.")
        for row in rows[:10]:
            print(
                f"{row['usage_date']} {row['tenant_id']} "
                f"users={row['active_users']} requests={row['api_requests']} "
                f"storage_mb={row['storage_mb']} cost_mxn={row['estimated_cost_mxn']}"
            )
        return 0

    count = upsert_usage_rows(database_url, rows)
    print(f"Upserted {count} tenant usage rows into admin.tenant_usage_daily.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
