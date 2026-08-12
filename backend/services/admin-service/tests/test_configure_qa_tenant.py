from pathlib import Path
import importlib.util

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "configure_qa_tenant.py"


def load_module():
    spec = importlib.util.spec_from_file_location("configure_qa_tenant", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_configuration_refuses_non_qa_environment(monkeypatch):
    module = load_module()
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "local")

    with pytest.raises(RuntimeError, match="ERCLAVE_ENVIRONMENT=qa"):
        module.main()


def test_configuration_requires_explicit_confirmation(monkeypatch):
    module = load_module()
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "qa")
    monkeypatch.delenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION", raising=False)

    with pytest.raises(RuntimeError, match="explicit QA tenant configuration confirmation"):
        module.main()


def test_configuration_runs_structural_seeds_only(monkeypatch, tmp_path):
    module = load_module()
    contracts = tmp_path / "contracts" / "api"
    contracts.mkdir(parents=True)
    calls = []

    monkeypatch.setattr(module, "CONTRACTS_DIR", contracts)
    monkeypatch.setenv("ERCLAVE_ENVIRONMENT", "qa")
    monkeypatch.setenv("ERCLAVE_QA_CONFIGURATION_CONFIRMATION", "CONFIGURE_ERCLAVE_QA")
    monkeypatch.setenv("ERCLAVE_DATABASE_URL", "postgresql://configured-by-secret-manager")
    monkeypatch.setattr(module.subprocess, "run", lambda command, check: calls.append((command, check)))

    assert module.main() == 0
    assert len(calls) == 2
    assert calls[0][0][-2:] == ["--contracts-dir", str(contracts)]
    assert calls[1][0][-1].endswith("seed_admin_qa_demo.py")
    assert all(check is True for _, check in calls)
