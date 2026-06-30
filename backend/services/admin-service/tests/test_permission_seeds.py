from app.seeds.permissions import extract_permission_seeds_from_text


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
