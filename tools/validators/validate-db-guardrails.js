const fs = require("fs");
const path = require("path");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];

const versionsDir = fromRoot("backend", "alembic", "versions");
const migrationFiles = fs.existsSync(versionsDir)
  ? fs.readdirSync(versionsDir).filter((file) => file.endsWith(".py")).sort()
  : [];

const tenantScopedAdminTables = [
  "roles",
  "tenant_modules",
  "memberships",
  "role_permissions",
  "membership_roles"
];

function extractCreateTableBlock(content, tableName) {
  const marker = `op.create_table(\n        "${tableName}"`;
  const start = content.indexOf(marker);
  if (start === -1) return "";

  const next = content.indexOf("\n    op.create_table(", start + marker.length);
  const downgrade = content.indexOf("\ndef downgrade", start + marker.length);
  const endCandidates = [next, downgrade].filter((index) => index !== -1);
  const end = endCandidates.length ? Math.min(...endCandidates) : content.length;
  return content.slice(start, end);
}

if (!migrationFiles.length) {
  errors.push("No Alembic migration files found in backend/alembic/versions.");
}

const revisions = [];
const downRevisions = [];

for (const fileName of migrationFiles) {
  const relativePath = path.join("backend", "alembic", "versions", fileName);
  const content = readText(relativePath);
  const upgradeBlock = content.split("\ndef downgrade")[0];

  const revisionMatch = content.match(/^revision:\s*str\s*=\s*"([^"]+)"/m);
  if (!revisionMatch) {
    errors.push(`${relativePath} is missing a typed revision string.`);
  } else {
    revisions.push(revisionMatch[1]);
    if (!fileName.includes(revisionMatch[1])) {
      errors.push(`${relativePath} file name should include revision ${revisionMatch[1]}.`);
    }
  }

  const downRevisionMatch = content.match(/^down_revision:\s*str\s*\|\s*None\s*=\s*(.+)$/m);
  if (!downRevisionMatch) {
    errors.push(`${relativePath} is missing a typed down_revision.`);
  } else {
    downRevisions.push(downRevisionMatch[1].trim());
  }

  const destructiveUpgradePatterns = [
    "op.drop_table(",
    "op.drop_column(",
    "op.execute(\"DROP ",
    "op.execute('DROP ",
    "truncate table",
    "delete from "
  ];
  for (const pattern of destructiveUpgradePatterns) {
    if (upgradeBlock.toLowerCase().includes(pattern.toLowerCase())) {
      errors.push(`${relativePath} contains destructive operation in upgrade: ${pattern}`);
    }
  }

  const foreignKeyTargets = [...upgradeBlock.matchAll(/ForeignKeyConstraint\(\[[^\]]+\],\s*\["([^"]+)"\]/g)];
  for (const match of foreignKeyTargets) {
    const target = match[1];
    const [schema] = target.split(".");
    const blockStart = upgradeBlock.lastIndexOf("op.create_table(", match.index);
    const blockEndCandidate = upgradeBlock.indexOf("op.create_table(", match.index);
    const blockEnd = blockEndCandidate === -1 ? upgradeBlock.length : blockEndCandidate;
    const sourceBlock = upgradeBlock.slice(blockStart, blockEnd);
    const sourceSchema = sourceBlock.match(/schema="([^"]+)"/)?.[1];
    if (schema && sourceSchema && schema !== sourceSchema) {
      errors.push(`${relativePath} contains cross-schema FK target ${target}; use contract references unless explicitly approved.`);
    }
  }
}

const duplicateRevisions = revisions.filter((revision, index) => revisions.indexOf(revision) !== index);
for (const revision of duplicateRevisions) {
  errors.push(`Duplicate Alembic revision found: ${revision}`);
}

if (downRevisions.length) {
  const rootCount = downRevisions.filter((value) => value === "None").length;
  if (rootCount !== 1) {
    errors.push(`Expected exactly one Alembic root migration, found ${rootCount}.`);
  }
}

const initialMigration = "backend/alembic/versions/20260617_0001_admin_service_initial.py";
if (fs.existsSync(fromRoot(initialMigration))) {
  const initialContent = readText(initialMigration);
  if (!initialContent.includes('op.execute("CREATE SCHEMA IF NOT EXISTS admin")')) {
    errors.push(`${initialMigration} must create admin schema explicitly.`);
  }

  for (const tableName of tenantScopedAdminTables) {
    const block = extractCreateTableBlock(initialContent, tableName);
    if (!block) {
      errors.push(`${initialMigration} is missing admin.${tableName}.`);
    } else if (!block.includes('sa.Column("tenant_id"')) {
      errors.push(`admin.${tableName} must include tenant_id.`);
    }
  }
}

const seedScript = readText("backend/scripts/seed_admin_mvp.py").toLowerCase();
if (!seedScript.includes("on conflict (code) do update")) {
  errors.push("backend/scripts/seed_admin_mvp.py must upsert permissions with ON CONFLICT (code) DO UPDATE.");
}
if (!seedScript.includes("--dry-run")) {
  errors.push("backend/scripts/seed_admin_mvp.py must support --dry-run.");
}

const qaDemoSeedScript = readText("backend/scripts/seed_admin_qa_demo.py").toLowerCase();
const requiredQaDemoFragments = [
  "on conflict (slug) do update",
  "on conflict (email) do update",
  "on conflict (tenant_id, code) do update",
  "on conflict (tenant_id, user_id) do update",
  "on conflict (tenant_id, module_code) do update",
  "on conflict (tenant_id, role_id, permission_id) do nothing",
  "on conflict (tenant_id, membership_id, role_id) do nothing",
  "--dry-run"
];
for (const fragment of requiredQaDemoFragments) {
  if (!qaDemoSeedScript.includes(fragment)) {
    errors.push(`backend/scripts/seed_admin_qa_demo.py missing idempotency fragment: ${fragment}`);
  }
}

const permissionSeed = readText("backend/services/admin-service/app/seeds/permissions.py");
if (!permissionSeed.includes("extract_permission_seeds")) {
  errors.push("Permission seed extractor must expose extract_permission_seeds.");
}

const apiDir = fromRoot("contracts", "api");
const permissionCodes = new Set();
if (fs.existsSync(apiDir)) {
  for (const fileName of fs.readdirSync(apiDir).filter((file) => file.endsWith(".openapi.yaml"))) {
    const content = fs.readFileSync(path.join(apiDir, fileName), "utf8");
    for (const match of content.matchAll(/x-permissions:\s*\[([^\]]+)\]/g)) {
      for (const code of match[1].split(",")) {
        const normalized = code.trim().replace(/^["']|["']$/g, "");
        if (normalized) permissionCodes.add(normalized);
      }
    }
  }
}

if (permissionCodes.size < 50) {
  errors.push(`Expected at least 50 OpenAPI permission seeds, found ${permissionCodes.size}.`);
}

if (errors.length) {
  fail("database guardrail validation failed", errors);
} else {
  ok("database migration and seed guardrails are valid.");
}
