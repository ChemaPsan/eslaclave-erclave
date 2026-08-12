const fs = require("fs");
const path = require("path");
const { fail, fromRoot, ok } = require("./shared");

const requiredContracts = [
  "admin-service.openapi.yaml",
  "production-service.openapi.yaml",
  "hr-service.openapi.yaml",
  "inventory-service.openapi.yaml",
  "sales-service.openapi.yaml",
  "billing-service.openapi.yaml",
  "provisioning-service.openapi.yaml",
  "integration-service.openapi.yaml"
];

const requiredFragments = [
  "openapi: 3.1.0",
  "info:",
  "paths:",
  "components:",
  "operationId:",
  "x-required-module:",
  "x-permissions:"
];

const errors = [];
const apiDir = fromRoot("contracts", "api");

for (const fileName of requiredContracts) {
  const fullPath = path.join(apiDir, fileName);
  const relativePath = path.relative(fromRoot(), fullPath);

  if (!fs.existsSync(fullPath)) {
    errors.push(`Missing OpenAPI contract: ${relativePath}`);
    continue;
  }

  const content = fs.readFileSync(fullPath, "utf8");

  for (const fragment of requiredFragments) {
    if (!content.includes(fragment)) {
      errors.push(`${relativePath} missing required fragment: ${fragment}`);
    }
  }

  const operationIds = content.match(/^\s+operationId:\s+[A-Za-z0-9_]+/gm) || [];
  if (operationIds.length === 0) {
    errors.push(`${relativePath} must define at least one operationId.`);
  }

  const idempotentOperations = content.match(/Idempotency-Key/g) || [];
  if (idempotentOperations.length === 0) {
    errors.push(`${relativePath} must reference Idempotency-Key for command operations.`);
  }
}

if (errors.length) {
  fail("OpenAPI contracts are incomplete", errors);
} else {
  ok("OpenAPI MVP contracts exist and include required metadata.");
}
