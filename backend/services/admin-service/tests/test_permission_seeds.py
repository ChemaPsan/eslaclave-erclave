from pathlib import Path

from app.seeds.permissions import extract_permission_seeds, extract_permission_seeds_from_text


def test_extract_permission_seeds_from_inline_openapi_permissions():
    content = """
paths:
  /v1/tenants:
    post:
      x-required-module: admin
      x-permissions: [internal.provisioning.tenant.create]
  /v1/production/orders:
    get:
      x-required-module: production
      x-permissions: [production.order.read, sales.order.fulfill]
  /v1/policy/evaluate:
    post:
      x-required-module: admin
      x-permissions: [internal.policy.evaluate]
"""

    seeds = extract_permission_seeds_from_text(content, "contracts/api/example.openapi.yaml")
    by_code = {seed.code: seed for seed in seeds}

    assert by_code["internal.provisioning.tenant.create"].module_code == "provisioning"
    assert by_code["internal.provisioning.tenant.create"].resource == "tenant"
    assert by_code["production.order.read"].module_code == "production"
    assert by_code["sales.order.fulfill"].module_code == "sales"
    assert by_code["internal.policy.evaluate"].module_code == "admin"
    assert by_code["internal.policy.evaluate"].resource == "policy"
    assert by_code["internal.policy.evaluate"].classification == "internal"
    assert by_code["internal.policy.evaluate"].assignable_to_tenant_role is False
    assert by_code["production.order.read"].classification == "tenant"
    assert by_code["production.order.read"].assignable_to_tenant_role is True
    assert by_code["production.order.read"].risk_level == "low"
    assert by_code["production.order.read"].display_name_es
    assert by_code["production.order.read"].display_name_en


def test_hr_contract_seeds_its_own_permission_group_without_production_legacy_codes():
    contracts_dir = Path(__file__).resolve().parents[4] / "contracts" / "api"
    permissions = extract_permission_seeds(contracts_dir)
    hr_permissions = {permission.code for permission in permissions if permission.module_code == "hr"}

    assert hr_permissions == {
        "hr.area.create",
        "hr.area.read",
        "hr.area.update",
        "hr.position.create",
        "hr.position.read",
        "hr.position.update",
        "hr.worker.create",
        "hr.worker.read",
        "hr.worker.update",
    }
    assert not any(permission.code.startswith("production.labor") for permission in permissions)


def test_permission_editor_seed_is_human_readable_and_tenant_assignable():
    contracts_dir = Path(__file__).resolve().parents[4] / "contracts" / "api"
    by_code = {permission.code: permission for permission in extract_permission_seeds(contracts_dir)}

    permission = by_code["admin.role.permissions.manage"]
    assert permission.display_name_es == "Administrar permisos de roles"
    assert permission.display_name_en == "Manage role permissions"
    assert permission.classification == "tenant"
    assert permission.assignable_to_tenant_role is True
    assert permission.risk_level == "high"


def test_demo_seed_never_grants_internal_or_unentitled_permissions_to_owner():
    seed_path = Path(__file__).resolve().parents[3] / "scripts" / "seed_admin_qa_demo.py"
    source = seed_path.read_text(encoding="utf-8")

    assert "permissions.classification = 'tenant'" in source
    assert "permissions.assignable_to_tenant_role = true" in source
    assert "tenant_modules.status = 'active'" in source
