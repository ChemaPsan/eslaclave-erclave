from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine, text


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
ADMIN_SERVICE_DIR = BACKEND_DIR / "services" / "admin-service"


sys.path.insert(0, str(ADMIN_SERVICE_DIR))

from app.seeds.permissions import extract_permission_seeds  # noqa: E402


def stable_permission_id(code: str) -> str:
    return f"per_{uuid5(NAMESPACE_URL, f'erclave.permission:{code}').hex[:26]}"


def upsert_permissions(database_url: str, permissions: tuple[object, ...]) -> int:
    engine = create_engine(database_url)
    statement = text(
        """
        insert into admin.permissions (
            id,
            code,
            module_code,
            resource,
            action,
            description,
            status
        )
        values (
            :id,
            :code,
            :module_code,
            :resource,
            :action,
            :description,
            :status
        )
        on conflict (code) do update set
            module_code = excluded.module_code,
            resource = excluded.resource,
            action = excluded.action,
            description = excluded.description,
            status = excluded.status,
            updated_at = now()
        """
    )

    rows = [
        {
            "id": stable_permission_id(permission.code),
            "code": permission.code,
            "module_code": permission.module_code,
            "resource": permission.resource,
            "action": permission.action,
            "description": permission.description,
            "status": permission.status,
        }
        for permission in permissions
    ]

    with engine.begin() as connection:
        connection.execute(statement, rows)

    return len(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply idempotent admin-service MVP seeds.")
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=REPO_ROOT / "contracts" / "api",
        help="Directory containing OpenAPI contracts.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the permission count without writing to PostgreSQL.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    permissions = extract_permission_seeds(args.contracts_dir)

    if args.dry_run:
        print(f"Found {len(permissions)} permission seeds.")
        return 0

    database_url = os.getenv("ERCLAVE_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ERCLAVE_DATABASE_URL is required to apply admin MVP seeds.")

    count = upsert_permissions(database_url, permissions)
    print(f"Applied {count} permission seeds to admin.permissions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
