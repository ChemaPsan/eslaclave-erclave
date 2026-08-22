"""Run pytest with an isolated base directory and remove it in the creator process."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

import pytest


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    base_temp = repo_root / f".pytest-tmp-{os.getpid()}"
    try:
        requested = sys.argv[1:] or ["-q"]
        return pytest.main([*requested, f"--basetemp={base_temp}"])
    finally:
        if base_temp.exists():
            shutil.rmtree(base_temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
