const fs = require("fs");
const { fail, fromRoot, ok } = require("./shared");

const requiredPaths = [
  "backend/README.md",
  "backend/pyproject.toml",
  "backend/.env.example",
  "backend/alembic.ini",
  "backend/alembic/env.py",
  "backend/alembic/versions/.gitkeep",
  "backend/alembic/versions/20260617_0001_admin_service_initial.py",
  "backend/shared/erclave_common/config.py",
  "backend/shared/erclave_common/db.py",
  "backend/shared/erclave_common/errors.py",
  "backend/shared/erclave_common/health.py",
  "backend/shared/erclave_common/middleware.py",
  "backend/services/admin-service/app/main.py",
  "backend/services/admin-service/app/models.py",
  "backend/services/admin-service/app/api.py",
  "backend/services/admin-service/app/repositories.py",
  "backend/services/admin-service/app/schemas.py",
  "backend/services/admin-service/app/seeds/__init__.py",
  "backend/services/admin-service/app/seeds/catalog.py",
  "backend/services/admin-service/app/seeds/permissions.py",
  "backend/scripts/seed_admin_mvp.py",
  "backend/scripts/seed_admin_qa_demo.py",
  "backend/services/admin-service/tests/test_health.py",
  "backend/services/admin-service/tests/test_permission_seeds.py",
  "backend/services/admin-service/tests/test_qa_demo_seed.py",
  "backend/services/admin-service/tests/test_admin_api.py",
  "backend/services/admin_service_adapter.py",
  "backend/alembic/versions/20260701_0002_production_service_initial.py",
  "backend/services/production-service/app/main.py",
  "backend/services/production-service/app/api.py",
  "backend/services/production-service/app/authorization.py",
  "backend/services/production-service/app/repositories.py",
  "backend/services/production-service/app/schemas.py",
  "backend/services/production-service/tests/test_production_api.py",
  "backend/services/production_service_adapter.py"
];

const requiredFragments = [
  ["backend/alembic/env.py", "target_metadata = load_admin_metadata()"],
  ["backend/alembic/versions/20260617_0001_admin_service_initial.py", "op.execute(\"CREATE SCHEMA IF NOT EXISTS admin\")"],
  ["backend/alembic/versions/20260617_0001_admin_service_initial.py", "\"tenant_modules\""],
  ["backend/alembic/versions/20260617_0001_admin_service_initial.py", "\"memberships\""],
  ["backend/alembic/versions/20260617_0001_admin_service_initial.py", "\"audit_events\""],
  ["backend/shared/erclave_common/config.py", "api_public_base_url"],
  ["backend/shared/erclave_common/middleware.py", "CorrelationIdMiddleware"],
  ["backend/shared/erclave_common/middleware.py", "TenantContextMiddleware"],
  ["backend/shared/erclave_common/health.py", "@router.get(\"/health\")"],
  ["backend/services/admin-service/app/main.py", "FastAPI"],
  ["backend/services/admin-service/app/main.py", "include_router(health_router)"],
  ["backend/services/admin-service/app/main.py", "include_router(admin_router)"],
  ["backend/services/admin-service/app/api.py", "@router.get(\"/tenants/{tenant_id}\""],
  ["backend/services/admin-service/app/api.py", "@router.get(\"/tenants/{tenant_id}/entitlements\""],
  ["backend/services/admin-service/app/api.py", "@router.post(\"/policy/evaluate\""],
  ["backend/services/admin-service/app/repositories.py", "class AdminRepository"],
  ["backend/services/admin-service/app/repositories.py", "def evaluate_policy"],
  ["backend/services/admin-service/app/models.py", "class Tenant"],
  ["backend/services/admin-service/app/models.py", "class Membership"],
  ["backend/services/admin-service/app/models.py", "class AuditEvent"],
  ["backend/services/admin-service/app/seeds/catalog.py", "MVP_MODULE_SEEDS"],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"admin\""],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"production\""],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"inventory\""],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"sales\""],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"billing\""],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"provisioning\""],
  ["backend/services/admin-service/app/seeds/catalog.py", "code=\"integrations\""],
  ["backend/services/admin-service/app/seeds/permissions.py", "extract_permission_seeds"],
  ["backend/scripts/seed_admin_mvp.py", "on conflict (code) do update"],
  ["backend/scripts/seed_admin_qa_demo.py", "ACTIVE_DEMO_MODULES"],
  ["backend/scripts/seed_admin_qa_demo.py", "on conflict (tenant_id, role_id, permission_id) do nothing"],
  ["backend/README.md", "ERCLAVE_API_PUBLIC_BASE_URL"],
  ["backend/alembic/versions/20260701_0002_production_service_initial.py", "CREATE SCHEMA IF NOT EXISTS production"],
  ["backend/alembic/versions/20260701_0002_production_service_initial.py", "\"product_services\""],
  ["backend/services/production-service/app/main.py", "include_router(production_router)"],
  ["backend/services/production-service/app/api.py", "@router.get(\"/product-services\""],
  ["backend/services/production-service/app/api.py", "@router.post(\"/product-services\""],
  ["backend/services/production-service/app/authorization.py", "require_production_access"],
  ["backend/services/production-service/app/repositories.py", "class ProductionRepository"],
  ["backend/services/production-service/app/repositories.py", "def create_product_service"],
  ["backend/services/production_service_adapter.py", "production-service"]
];

const errors = [];

for (const relativePath of requiredPaths) {
  if (!fs.existsSync(fromRoot(relativePath))) {
    errors.push(`Missing backend scaffold file: ${relativePath}`);
  }
}

for (const [relativePath, fragment] of requiredFragments) {
  const fullPath = fromRoot(relativePath);
  if (!fs.existsSync(fullPath)) continue;

  const content = fs.readFileSync(fullPath, "utf8");
  if (!content.includes(fragment)) {
    errors.push(`${relativePath} missing required fragment: ${fragment}`);
  }
}

if (errors.length) {
  fail("backend scaffold is incomplete", errors);
} else {
  ok("backend FastAPI scaffold is present.");
}
