from __future__ import annotations

import os
from urllib.parse import urlparse

from seed_admin_qa_demo import (
    ACTIVE_DEMO_MODULES,
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_NAME,
    DEFAULT_TENANT_NAME,
    DEFAULT_TENANT_SLUG,
    apply_demo_seed,
)


LOCAL_RELEASE_MODULES = (*ACTIVE_DEMO_MODULES, "hr")


def require_local_database(database_url: str) -> None:
    parsed = urlparse(database_url.replace("postgresql+psycopg", "postgresql", 1))
    if parsed.hostname != "127.0.0.1" or parsed.port != 5434 or parsed.path != "/erclave_local":
        raise RuntimeError("Local demo seed requires 127.0.0.1:5434/erclave_local.")


def main() -> int:
    database_url = os.getenv("ERCLAVE_DATABASE_URL", "")
    require_local_database(database_url)
    result = apply_demo_seed(
        database_url=database_url,
        tenant_slug=DEFAULT_TENANT_SLUG,
        tenant_name=DEFAULT_TENANT_NAME,
        admin_email=DEFAULT_ADMIN_EMAIL,
        admin_name=DEFAULT_ADMIN_NAME,
        extra_owner_emails=(),
        active_modules=LOCAL_RELEASE_MODULES,
    )
    print(f"Applied isolated local demo seed: tenant={result['tenant_slug']} modules={result['active_modules']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
