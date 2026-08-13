const { spawnSync } = require("child_process");
const path = require("path");
const { fail, ok } = require("./shared");

const validators = [
  "validate-codex-tooling.js",
  "validate-environment-boundaries.js",
  "validate-qa-release-pipeline.js",
  "validate-local-qa-parity.js",
  "validate-session-context.js",
  "validate-i18n.js",
  "validate-active-module-localization.js",
  "validate-responsive-ui.js",
  "validate-permission-editor.js",
  "validate-labor-catalog.js",
  "validate-inventory-movement-flow.js",
  "validate-production-cycle.js",
  "validate-agents.js",
  "validate-architecture.js",
  "validate-backend-scaffold.js",
  "validate-cross-platform.js",
  "validate-db-guardrails.js",
  "validate-tenant-isolation.js",
  "validate-openapi-contracts.js",
  "validate-traceability.js",
  "validate-syntax.js"
];

const errors = [];

for (const validator of validators) {
  const script = path.join("tools", "validators", validator);
  console.log(`\n[RUN] ${validator}`);
  const result = spawnSync(process.execPath, [script], { stdio: "inherit" });

  if (result.status !== 0) {
    errors.push(`${validator} failed.`);
  }
}

if (errors.length) {
  fail("validation suite failed", errors);
} else {
  ok("all validators passed.");
}
