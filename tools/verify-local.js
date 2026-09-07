const path = require("path");
const { spawnSync } = require("child_process");

const repoRoot = path.resolve(__dirname, "..");
const steps = [
  ["verify:postgres", path.join(repoRoot, "tools", "verify-postgres.js"), []],
  ["test:e2e:local", path.join(repoRoot, "node_modules", "@playwright", "test", "cli.js"), ["test"]]
];
for (const [name, entrypoint, args] of steps) {
  console.log(`\n[LOCAL] ${name}`);
  const result = spawnSync(process.execPath, [entrypoint, ...args], { cwd: repoRoot, env: process.env, stdio: "inherit", shell: false });
  if (result.error) {
    console.error(`[FAIL] ${name} could not start: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) process.exit(result.status || 1);
}
console.log("\n[OK] Local verification passed PostgreSQL integration and browser E2E regression.");
