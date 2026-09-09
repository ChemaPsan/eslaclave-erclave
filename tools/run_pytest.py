"""Run pytest with an isolated base directory and remove it in the creator process."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

import pytest


class NoSkippedTestsPlugin:
    """Turn every skipped test into a failing PostgreSQL verification."""

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        skipped = terminal.stats.get("skipped", []) if terminal else []
        if skipped:
            if terminal:
                terminal.write_line(
                    f"[FAIL] Strict integration mode forbids skipped tests: {len(skipped)} skipped."
                )
            session.exitstatus = pytest.ExitCode.TESTS_FAILED


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    base_temp = repo_root / f".pytest-tmp-{os.getpid()}"
    try:
        requested = sys.argv[1:] or ["-q"]
        plugins = [NoSkippedTestsPlugin()] if os.getenv("ERCLAVE_REQUIRE_NO_SKIPS") == "1" else []
        return pytest.main([*requested, f"--basetemp={base_temp}"], plugins=plugins)
    finally:
        if base_temp.exists():
            shutil.rmtree(base_temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
