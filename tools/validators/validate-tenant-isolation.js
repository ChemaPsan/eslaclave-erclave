const fs = require("fs");
const path = require("path");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];

const policyPath = "docs/arquitectura/politica_aislamiento_tenant.md";
if (!fs.existsSync(fromRoot(policyPath))) {
  errors.push(`${policyPath} is required.`);
} else {
  const policy = readText(policyPath);
  const requiredFragments = [
    "Ningun dato operativo puede existir sin `tenant_id`",
    "Pruebas obligatorias anti-fuga",
    "Row-Level Security",
    "`admin.audit_events.tenant_id` puede ser nulo solo para eventos transversales reales",
    "on conflict (tenant_id, ...)"
  ];
  for (const fragment of requiredFragments) {
    if (!policy.includes(fragment)) {
      errors.push(`${policyPath} is missing required tenant-isolation fragment: ${fragment}`);
    }
  }
}

const modelPath = "docs/arquitectura/modelo_multitenant.md";
if (!readText(modelPath).includes(policyPath)) {
  errors.push(`${modelPath} must link to ${policyPath}.`);
}

const globalTables = new Set([
  "admin.tenants",
  "admin.users",
  "admin.permissions"
]);

const nullableTenantTables = new Set([
  "admin.audit_events"
]);

function getCreateTableBlocks(content) {
  const blocks = [];
  const marker = "op.create_table(";
  let start = content.indexOf(marker);
  while (start !== -1) {
    const next = content.indexOf(marker, start + marker.length);
    const downgrade = content.indexOf("\ndef downgrade", start + marker.length);
    const endCandidates = [next, downgrade].filter((index) => index !== -1);
    const end = endCandidates.length ? Math.min(...endCandidates) : content.length;
    blocks.push(content.slice(start, end));
    start = next;
  }
  return blocks;
}

function extractTableName(block) {
  return block.match(/op\.create_table\(\s*\n\s*"([^"]+)"/)?.[1] || "";
}

function extractSchema(block) {
  return block.match(/schema="([^"]+)"/)?.[1] || "";
}

function hasTenantIdColumn(block) {
  return block.includes('sa.Column("tenant_id"');
}

function tenantIdIsNotNull(block) {
  return block
    .split("\n")
    .some((line) => line.includes('sa.Column("tenant_id"') && line.includes("nullable=False"));
}

function uniqueConstraints(block) {
  return [...block.matchAll(/sa\.UniqueConstraint\(([^)]*)\)/g)].map((match) => match[1]);
}

const versionsDir = fromRoot("backend", "alembic", "versions");
if (fs.existsSync(versionsDir)) {
  for (const fileName of fs.readdirSync(versionsDir).filter((file) => file.endsWith(".py"))) {
    const relativePath = path.join("backend", "alembic", "versions", fileName);
    const content = readText(relativePath);
    for (const block of getCreateTableBlocks(content)) {
      const tableName = extractTableName(block);
      const schema = extractSchema(block);
      if (!tableName || !schema) continue;

      const qualifiedName = `${schema}.${tableName}`;
      if (globalTables.has(qualifiedName)) continue;

      if (!hasTenantIdColumn(block)) {
        errors.push(`${relativePath}: ${qualifiedName} must include tenant_id unless explicitly global.`);
        continue;
      }

      if (!nullableTenantTables.has(qualifiedName) && !tenantIdIsNotNull(block)) {
        errors.push(`${relativePath}: ${qualifiedName}.tenant_id must be nullable=False.`);
      }

      for (const constraint of uniqueConstraints(block)) {
        const lowerConstraint = constraint.toLowerCase();
        const isNamedOnly = !lowerConstraint.includes('"');
        if (!isNamedOnly && !lowerConstraint.includes('"tenant_id"') && !lowerConstraint.includes("'tenant_id'")) {
          errors.push(`${relativePath}: unique constraint on ${qualifiedName} must include tenant_id: ${constraint.trim()}`);
        }
      }
    }
  }
}

const productionApi = readText("backend/services/production-service/app/api.py");
const productionRepository = readText("backend/services/production-service/app/repositories.py");
const productionAuthorization = readText("backend/services/production-service/app/authorization.py");

if (!productionApi.includes("def require_tenant_id(")) {
  errors.push("production-service API must define require_tenant_id.");
}

const routeMatches = [...productionApi.matchAll(/@router\.(get|post|patch|put|delete)\(/g)];
const requireTenantCalls = [...productionApi.matchAll(/require_tenant_id\(x_tenant_id\)/g)];
if (requireTenantCalls.length < routeMatches.length) {
  errors.push(`production-service routes must call require_tenant_id; found ${requireTenantCalls.length} calls for ${routeMatches.length} routes.`);
}

const authorizationGuards = [...productionApi.matchAll(/Depends\(require_production_access\(/g)];
if (authorizationGuards.length < routeMatches.length) {
  errors.push(`production-service routes must enforce production access; found ${authorizationGuards.length} guards for ${routeMatches.length} routes.`);
}
for (const fragment of ["/v1/session/context", "module_not_enabled", "permission_denied", "tenant_access_denied"]) {
  if (!productionAuthorization.includes(fragment)) {
    errors.push(`production-service authorization is missing required fragment: ${fragment}`);
  }
}
for (const fragment of ["production.idempotency_records", "request_hash", "idempotency_key_reused", "for update"]) {
  if (!productionRepository.toLowerCase().includes(fragment.toLowerCase())) {
    errors.push(`production-service idempotency is missing required fragment: ${fragment}`);
  }
}

const productServiceMutations = [...productionRepository.matchAll(/(update|delete from) production\.product_services[\s\S]*?(?="""|\n\s*""")/g)].map((match) => match[0]);
for (const block of productServiceMutations) {
  if (!block.includes("tenant_id = :tenant_id")) {
    errors.push("production-service repository mutation against production.product_services is missing tenant_id = :tenant_id.");
  }
}

if (!productionRepository.includes('filters = ["tenant_id = :tenant_id"]')) {
  errors.push("production-service list query must start from tenant_id = :tenant_id filter.");
}

if (!productionRepository.includes("where tenant_id = :tenant_id and id = :id")) {
  errors.push("production-service direct lookup must scope by tenant_id and id.");
}

if (!productionRepository.includes("on conflict (tenant_id, code)")) {
  errors.push("production-service product_services upsert/conflict logic must scope conflicts by tenant_id.");
}

const productionTests = readText("backend/services/production-service/tests/test_production_api.py");
const antiLeakFragments = [
  "other_tenant",
  "X-Tenant-Id",
  "assert response.status_code == 404"
];
for (const fragment of antiLeakFragments) {
  if (!productionTests.includes(fragment)) {
    errors.push(`production-service tests must include anti-leak coverage fragment: ${fragment}`);
  }
}

if (errors.length) {
  fail("tenant isolation validation failed", errors);
} else {
  ok("tenant isolation policy and guardrails are valid.");
}
