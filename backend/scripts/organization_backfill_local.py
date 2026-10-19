"""Preview by default; import (CONT-01) or activate (CONT-02) the reviewed Local organization."""
import argparse
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "admin-service"))
from app.organization_migration import (  # noqa: E402
    OrganizationMigrationError, apply_import, build_plan, read_profile,
)

LOCAL_TENANT = "ten_739ee59d765d5e14818674800d"


def local_database_url(value: str, environment: str, tenant_id: str) -> str:
    try:
        parsed = make_url(value)
    except Exception:
        raise OrganizationMigrationError("local_database_required") from None
    if (environment != "local" or tenant_id != LOCAL_TENANT
            or parsed.host not in {"127.0.0.1", "localhost", "::1"}
            or parsed.port != 5434 or parsed.database != "erclave_local"
            or parsed.drivername not in {"postgresql", "postgresql+psycopg"}
            or parsed.query):
        # Query-string host/service overrides must not bypass the URL check.
        raise OrganizationMigrationError("local_database_required")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise OrganizationMigrationError("duplicate_resolution_key")
        result[key] = value
    return result


def preview_report(plan):
    return {
        "status": "preview", "source_hash": plan["source_hash"], "plan_hash": plan["plan_hash"],
        "counts": {name: len(rows) for name, rows in plan["rows"].items()},
        "targets": {name: [{key: row[key] for key in
                            ("id", "code", "status", "issuer_id", "society_id", "base_currency") if key in row}
                           for row in plan["rows"][name]] for name in ("fiscal_issuers", "societies", "divisions")},
        "equivalences": [{key: row[key] for key in ("collection", "legacy_id", "society_id", "issuer_id", "division_id")}
                         for row in plan["rows"]["organization_legacy_mappings"]],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--resolutions", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--activate", action="store_true", help="Activate the reviewed normalized structure; archive/reconcile an unchanged shadow if needed.")
    parser.add_argument("--expected-source-hash")
    parser.add_argument("--expected-plan-hash")
    parser.add_argument("--operator")
    args = parser.parse_args(argv)
    engine = None
    try:
        url = local_database_url(os.getenv("ERCLAVE_DATABASE_URL", ""), os.getenv("ERCLAVE_ENVIRONMENT", ""), args.tenant_id)
        if args.apply and args.activate:
            raise OrganizationMigrationError("choose_apply_or_activate")
        if (args.apply or args.activate) and not all((args.expected_source_hash, args.expected_plan_hash, args.operator)):
            raise OrganizationMigrationError("reviewed_hashes_and_operator_required")
        resolutions = json.loads(args.resolutions.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object) if args.resolutions else {}
        hostaddr = "::1" if make_url(url).host == "::1" else "127.0.0.1"
        engine = create_engine(url, poolclass=NullPool, connect_args={"connect_timeout": 5, "hostaddr": hostaddr})
        with engine.begin() as connection:
            connection.exec_driver_sql("SET LOCAL lock_timeout = '5s'")
            if args.activate:
                from app.organization_store import activate_organization, OrganizationStore
                from app.repositories import AdminRepository
                from erclave_common.errors import ErclaveError
                try:
                    result = activate_organization(connection, args.tenant_id, args.expected_source_hash, args.expected_plan_hash,
                        args.operator, f"cont02-{uuid4().hex}", resolutions)
                    OrganizationStore(AdminRepository(engine)).project(connection, args.tenant_id)
                except ErclaveError as exc:
                    raise OrganizationMigrationError(exc.code) from None
            elif args.apply:
                result = apply_import(connection, args.tenant_id,
                    expected_source_hash=args.expected_source_hash, expected_plan_hash=args.expected_plan_hash,
                    operator=args.operator, correlation_id=f"cont01-{uuid4().hex}", resolutions=resolutions)
            else:
                # SET TRANSACTION READ ONLY prevents a future accidental write in preview.
                connection.exec_driver_sql("SET TRANSACTION READ ONLY")
                plan = build_plan(args.tenant_id, read_profile(connection, args.tenant_id), resolutions)
                result = preview_report(plan)
        print(json.dumps({"environment": "local", "tenant_id": args.tenant_id, **result}, ensure_ascii=True, indent=2))
        return 0
    except OrganizationMigrationError as error:
        print(json.dumps({"error": {"code": error.code, "issues": error.issues}}))
        return 2
    except (OSError, ValueError, SQLAlchemyError):
        # No URL, credentials, parameters, profile contents or DB diagnostics in logs.
        print(json.dumps({"error": {"code": "organization_import_failed"}}))
        return 2
    finally:
        if engine:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
