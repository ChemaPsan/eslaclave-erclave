const { spawnSync } = require("child_process");
const path = require("path");
const { fail, ok } = require("./shared");

const validators = [
  "validate-i18n.js",
  "validate-active-module-localization.js",
  "validate-architecture.js",
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
