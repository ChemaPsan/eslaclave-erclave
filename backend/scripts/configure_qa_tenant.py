from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


APP_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS_DIR = APP_ROOT / "contracts" / "api"


def main() -> int:
    if os.getenv("ERCLAVE_ENVIRONMENT") != "qa":
        raise RuntimeError("QA tenant configuration only runs with ERCLAVE_ENVIRONMENT=qa.")
    if os.getenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION") != "CONFIGURE_ERCLAVE_QA":
        raise RuntimeError("Missing explicit QA tenant configuration confirmation.")
    if not os.getenv("ERCLAVE_DATABASE_URL"):
        raise RuntimeError("ERCLAVE_DATABASE_URL is required.")
    if not CONTRACTS_DIR.is_dir():
        raise RuntimeError(f"OpenAPI contracts are missing at {CONTRACTS_DIR}.")

    subprocess.run(
        [
            sys.executable,
            str(APP_ROOT / "scripts" / "seed_admin_mvp.py"),
            "--contracts-dir",
            str(CONTRACTS_DIR),
        ],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(APP_ROOT / "scripts" / "seed_admin_qa_demo.py")],
        check=True,
    )
    print("Configured the QA demo tenant with real-service entitlements and permission catalog.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
