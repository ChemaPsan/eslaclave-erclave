const { spawnSync } = require("child_process");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const python = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const localTestEnvironment = {
  ...process.env,
  ERCLAVE_ENVIRONMENT: "local",
  ERCLAVE_APP_PUBLIC_BASE_URL: "http://localhost:4173"
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
