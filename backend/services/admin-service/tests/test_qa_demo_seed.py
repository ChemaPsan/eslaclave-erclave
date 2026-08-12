from pathlib import Path
import importlib.util


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "seed_admin_qa_demo.py"


def load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_admin_qa_demo", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_demo_seed_ids_are_deterministic():
    module = load_seed_module()

    first = module.demo_ids("demo-qa", "ADMIN.QA@ERCLAVE.LOCAL")
    second = module.demo_ids("demo-qa", "admin.qa@erclave.local")

    assert first == second
    assert first["tenant_id"].startswith("ten_")
    assert first["user_id"].startswith("usr_")
    assert first["role_id"].startswith("rol_")
    assert first["membership_id"].startswith("mem_")


def test_demo_modules_are_intentional_for_qa():
    module = load_seed_module()

    assert module.ACTIVE_DEMO_MODULES == ("admin", "production", "inventory", "hr")


def test_demo_seed_default_organization_profile_matches_admin_structure():
    module = load_seed_module()

    profile = module.default_organization_profile("ERClave Demo QA")

    assert profile["corporate"]["commercial_name"] == "ERClave Demo QA"
    assert profile["corporate"]["contact_email"] == ""
    assert profile["legal_entities"] == []
    assert profile["branches"] == []
