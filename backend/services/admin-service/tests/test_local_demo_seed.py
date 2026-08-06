from pathlib import Path
import importlib.util
import sys

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "seed_local_demo.py"


def load_seed_module():
    scripts_path = str(SCRIPT_PATH.parent)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    spec = importlib.util.spec_from_file_location("seed_local_demo", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_local_release_modules_include_hr_without_changing_qa_defaults():
    module = load_seed_module()
    assert module.LOCAL_RELEASE_MODULES == (
        "admin", "production", "inventory", "sales", "integrations", "hr"
    )


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql+psycopg://user:password@127.0.0.1:5432/erclave_qa",
        "postgresql+psycopg://user:password@cloud.example/erclave_local",
        "postgresql+psycopg://user:password@127.0.0.1:5434/erclave_qa",
    ],
)
def test_local_seed_rejects_non_local_database(database_url):
    module = load_seed_module()
    with pytest.raises(RuntimeError, match="127.0.0.1:5434/erclave_local"):
        module.require_local_database(database_url)


def test_local_seed_accepts_isolated_database():
    module = load_seed_module()
    module.require_local_database(
        "postgresql+psycopg://user:password@127.0.0.1:5434/erclave_local"
    )
