const { spawnSync } = require("child_process");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const python = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const inheritedTestDatabaseUrl = process.env.ERCLAVE_TEST_DATABASE_URL || "";
if (inheritedTestDatabaseUrl) {
  let parsed;
  try {
    parsed = new URL(inheritedTestDatabaseUrl);
  } catch {
    console.error("[FAIL] ERCLAVE_TEST_DATABASE_URL is not a valid database URL; refusing to run tests.");
    process.exit(1);
  }
  const localHosts = new Set(["localhost", "127.0.0.1", "[::1]"]);
  if (!localHosts.has(parsed.hostname) || parsed.pathname.replace(/\/$/, "") !== "/erclave_local") {
    console.error("[FAIL] ERCLAVE_TEST_DATABASE_URL must target erclave_local on loopback; refusing to run tests.");
    process.exit(1);
  }
}
const localTestEnvironment = {
  ...process.env,
  ERCLAVE_ENVIRONMENT: "local",
  ERCLAVE_API_PUBLIC_BASE_URL: "http://127.0.0.1:8000",
  ERCLAVE_APP_PUBLIC_BASE_URL: "http://127.0.0.1:4173",
  ERCLAVE_ADMIN_SERVICE_URL: "http://127.0.0.1:8000",
  ERCLAVE_AUTH_MODE: "demo",
  ERCLAVE_FIREBASE_PROJECT_ID: "demo-erclave",
  ERCLAVE_DATABASE_URL: "",
  ERCLAVE_INVENTORY_DATABASE_URL: "",
  ERCLAVE_HR_DATABASE_URL: ""
};
const steps = [
  {
    name: "Reglas y contratos del repositorio",
    command: process.execPath,
    args: [path.join("tools", "validators", "validate-all.js")],
    cwd: repoRoot
  },
  {
    name: "Compilación del backend",
    command: python,
    args: ["-m", "compileall", "-q", "shared", "services", "alembic"],
    cwd: path.join(repoRoot, "backend"),
    env: localTestEnvironment
  },
  {
    name: "Pruebas backend",
    command: python,
    args: ["-m", "pytest", "-q"],
    cwd: path.join(repoRoot, "backend"),
    env: localTestEnvironment
  }
];

for (const step of steps) {
  console.log(`\n[VERIFY] ${step.name}`);
  const result = spawnSync(step.command, step.args, {
    cwd: step.cwd,
    env: step.env || process.env,
    stdio: "inherit",
    shell: false
  });

  if (result.error) {
    console.error(`[FAIL] No se pudo ejecutar ${step.command}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.status !== 0) process.exit(result.status || 1);
}

console.log("\n[OK] Verificación completa: validadores, compilación y pruebas aprobados.");
