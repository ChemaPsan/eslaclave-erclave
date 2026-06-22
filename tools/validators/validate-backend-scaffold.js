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
  "backend/services/admin-service/app/seeds/__init__.py",
  "backend/services/admin-service/app/seeds/catalog.py",
  "backend/services/admin-service/tests/test_health.py",
  "backend/services/admin_service_adapter.py"
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
  ["backend/README.md", "ERCLAVE_API_PUBLIC_BASE_URL"]
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
