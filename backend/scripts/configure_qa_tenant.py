from __future__ import annotations

import os
from pathlib import Path
import sys

from sqlalchemy import create_engine, text


APP_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = APP_ROOT / "contracts" / "api"

sys.path.insert(0, str(APP_ROOT / "scripts"))
from seed_admin_mvp import extract_permission_seeds, upsert_permissions  # noqa: E402


def reconcile_existing_tenant(database_url: str, tenant_id: str, permissions) -> int:
    """Reconcile catalog and existing system owners; never provision tenant data."""
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            tenant = connection.execute(text(
                "select id from admin.tenants where id=:tenant_id and status='active' for update"
            ), {"tenant_id": tenant_id}).scalar_one_or_none()
            if tenant is None:
                raise RuntimeError("The explicitly selected QA tenant must already exist and be active.")
            owners = connection.execute(text(
                "select id from admin.roles where tenant_id=:tenant_id and code='owner' "
                "and system_role=true and status='active' for update"
            ), {"tenant_id": tenant_id}).scalars().all()
            if not owners:
                raise RuntimeError("QA configuration requires an existing active system owner role.")
            upsert_permissions(database_url, permissions, owner_tenant_id=tenant_id, connection=connection)
            granted = connection.execute(text("""
                insert into admin.role_permissions (id, tenant_id, role_id, permission_id, scope)
                select 'rpe_' || substr(md5(r.tenant_id || ':' || r.id || ':' || p.id), 1, 26),
                    r.tenant_id, r.id, p.id, '{}'::jsonb
                from admin.roles r cross join admin.permissions p
                where r.tenant_id=:tenant_id and r.code='owner'
                    and r.system_role=true and r.status='active'
                    and p.status='active' and p.classification='tenant'
                    and p.assignable_to_tenant_role=true
                    and (p.module_code='admin' or exists (
                        select 1 from admin.tenant_modules m
                        where m.tenant_id=r.tenant_id and m.module_code=p.module_code and m.status='active'
                            and m.tenant_enabled=true
                            and (m.starts_at is null or m.starts_at<=now())
                            and (m.ends_at is null or m.ends_at>now())
                    ))
                on conflict (tenant_id, role_id, permission_id) do nothing
            """), {"tenant_id": tenant_id}).rowcount
        return granted
    finally:
        engine.dispose()


def main() -> int:
    if os.getenv("ERCLAVE_ENVIRONMENT") != "qa":
        raise RuntimeError("QA tenant configuration only runs with ERCLAVE_ENVIRONMENT=qa.")
    if os.getenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION") != "CONFIGURE_ERCLAVE_QA":
        raise RuntimeError("Missing explicit QA tenant configuration confirmation.")
    if not os.getenv("ERCLAVE_DATABASE_URL"):
        raise RuntimeError("ERCLAVE_DATABASE_URL is required.")
    tenant_id = os.getenv("ERCLAVE_QA_CONFIGURATION_TENANT_ID", "").strip()
    if not tenant_id or not tenant_id.startswith("ten_") or not tenant_id[4:].isalnum():
        raise RuntimeError("ERCLAVE_QA_CONFIGURATION_TENANT_ID must explicitly select an existing tenant.")
    if not CONTRACTS_DIR.is_dir():
        raise RuntimeError(f"OpenAPI contracts are missing at {CONTRACTS_DIR}.")

    permissions = extract_permission_seeds(CONTRACTS_DIR)
    granted = reconcile_existing_tenant(os.environ["ERCLAVE_DATABASE_URL"], tenant_id, permissions)
    print(f"Reconciled global permission catalog and {granted} grants for existing owners in {tenant_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
