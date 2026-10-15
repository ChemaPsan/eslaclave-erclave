"""CONT-03: preview or apply reviewed membership scope conversion in isolated Local only."""
import argparse
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from organization_backfill_local import local_database_url, LOCAL_TENANT, OrganizationMigrationError
from app.organization_scope import scope_migration_plan, migrate_scopes
from app.repositories import AdminRepository
from erclave_common.errors import ErclaveError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-hash")
    parser.add_argument("--operator")
    args = parser.parse_args()
    engine = None
    try:
        url = local_database_url(os.getenv("ERCLAVE_DATABASE_URL", ""), os.getenv("ERCLAVE_ENVIRONMENT", ""), args.tenant_id)
        if args.apply and not (args.expected_hash and args.operator):
            raise OrganizationMigrationError("reviewed_hash_and_operator_required")
        engine = create_engine(url, poolclass=NullPool, connect_args={"connect_timeout": 5, "hostaddr": "::1" if make_url(url).host == "::1" else "127.0.0.1"})
        with engine.begin() as connection:
            connection.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
            if args.apply:
                count = migrate_scopes(connection, AdminRepository(engine), args.tenant_id, args.expected_hash, args.operator)
                result = {"status": "applied", "memberships": count}
            else:
                connection.exec_driver_sql("SET TRANSACTION READ ONLY")
                plan = scope_migration_plan(connection, args.tenant_id)
                result = {"status": "preview", "hash": plan["hash"], "memberships": len(plan["changes"]),
                          "grants": [{"membership_id": item["id"], "scope": item["after"]["scope"]} for item in plan["changes"]]}
        print(json.dumps({"environment": "local", "tenant_id": args.tenant_id, **result}))
        return 0
    except (ErclaveError, OrganizationMigrationError) as exc:
        print(json.dumps({"error": {"code": exc.code}})); return 2
    except (SQLAlchemyError, ValueError, OSError):
        print(json.dumps({"error": {"code": "scope_migration_failed"}})); return 2
    finally:
        if engine:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
