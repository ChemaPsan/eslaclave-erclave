const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const repoRoot = path.resolve(__dirname, "..");

function localDatabaseUrl() {
  if (process.env.ERCLAVE_TEST_DATABASE_URL) return process.env.ERCLAVE_TEST_DATABASE_URL;
  const envPath = path.join(repoRoot, "backend", ".env");
  if (!fs.existsSync(envPath)) return "";
  const line = fs.readFileSync(envPath, "utf8")
    .split(/\r?\n/)
    .find((entry) => entry.startsWith("ERCLAVE_INVENTORY_DATABASE_URL="));
  return line ? line.slice(line.indexOf("=") + 1).trim() : "";
}

const databaseUrl = localDatabaseUrl();
if (!databaseUrl) {
  console.error("[FAIL] ERCLAVE_TEST_DATABASE_URL is required for strict PostgreSQL integration.");
  process.exit(1);
}

let parsed;
try {
  parsed = new URL(databaseUrl);
} catch {
  console.error("[FAIL] The Local PostgreSQL URL is invalid.");
  process.exit(1);
}
if (!["127.0.0.1", "localhost", "[::1]"].includes(parsed.hostname)
    || parsed.port !== "5434"
    || parsed.pathname.replace(/\/$/, "") !== "/erclave_local") {
  console.error("[FAIL] Strict PostgreSQL integration only accepts loopback:5434/erclave_local.");
  process.exit(1);
}

const venvPython = process.platform === "win32"
  ? path.join(repoRoot, "backend", ".venv", "Scripts", "python.exe")
  : path.join(repoRoot, "backend", ".venv", "bin", "python");
const environment = {
  ...process.env,
  ERCLAVE_TEST_DATABASE_URL: databaseUrl,
  ERCLAVE_TEST_TENANT_ID: "ten_739ee59d765d5e14818674800d",
  ERCLAVE_REQUIRE_NO_SKIPS: "1",
  PYTHON: process.env.PYTHON || (fs.existsSync(venvPython) ? venvPython : undefined)
};
if (!environment.PYTHON) delete environment.PYTHON;

const result = spawnSync(process.execPath, [path.join("tools", "verify.js")], {
  cwd: repoRoot,
  env: environment,
  stdio: "inherit",
  shell: false
});
if (result.error) {
  console.error(`[FAIL] PostgreSQL verification could not start: ${result.error.message}`);
  process.exit(1);
}
process.exit(result.status || 0);
