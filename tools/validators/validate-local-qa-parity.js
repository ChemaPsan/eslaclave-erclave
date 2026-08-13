const fs = require("fs");
const vm = require("vm");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const requiredFiles = [
  "docs/operaciones/flujo_local_a_qa.md",
  ".agents/skills/erclave-qa-release/SKILL.md",
  "frontend/api/config.js",
  "backend/shared/erclave_common/config.py",
  "tools/verify.js"
];

for (const file of requiredFiles) {
  if (!fs.existsSync(fromRoot(file))) errors.push(`Missing Local-to-QA parity file: ${file}`);
}

if (!errors.length) {
  const config = readText("frontend/api/config.js");
  const executableConfig = `${config.replace(/export function /g, "function ")}\n({ getDemoTenantId, getConfiguredTenantId, setActiveTenantId, getDemoActorId });`;
  const remoteRuntime = vm.runInNewContext(executableConfig, {
    URL,
    window: {
      location: { hostname: "erclave.web.app" },
      ERCLAVE_CONFIG: { apiMode: "api" }
    },
    localStorage: {
      getItem: () => { throw new Error("QA runtime must not read tenant or actor from localStorage."); },
      setItem: () => { throw new Error("QA runtime must not persist tenant or actor to localStorage."); },
      removeItem: () => { throw new Error("QA runtime must not mutate localStorage."); }
    }
  });
  if (remoteRuntime.getDemoTenantId() !== "") errors.push("QA runtime must not fall back to the demo tenant before session resolution.");
  if (remoteRuntime.getConfiguredTenantId() !== "") errors.push("QA artifact must not embed a default tenant.");
  if (remoteRuntime.getDemoActorId() !== "") errors.push("QA runtime must rely on Firebase identity, not a demo actor.");
  remoteRuntime.setActiveTenantId("ten_session_member");
  if (remoteRuntime.getDemoTenantId() !== "ten_session_member") errors.push("QA runtime must retain the tenant selected from session memberships in memory.");

  const backendConfig = readText("backend/shared/erclave_common/config.py");
  for (const token of [
    'parsed.path.rstrip("/") != "/erclave_local"',
    'self.firebase_project_id != "demo-erclave"',
    "must remain on loopback in Local isolated mode"
  ]) {
    if (!backendConfig.includes(token)) errors.push(`Backend Local boundary is missing: ${token}`);
  }
  if (backendConfig.includes('env_file=".env"')) errors.push("Backend settings must not silently load a hybrid backend/.env file.");

  const verify = readText("tools/verify.js");
  for (const token of ["ERCLAVE_TEST_DATABASE_URL", '"/erclave_local"', 'ERCLAVE_DATABASE_URL: ""']) {
    if (!verify.includes(token)) errors.push(`npm verify must protect inherited database configuration: ${token}`);
  }

  const modules = readText("frontend/data/modules.js");
  for (const forbidden of ["$428k", "$96k", 'primary: "Reservar inventario"', '"Reservar insumos"']) {
    if (modules.includes(forbidden)) errors.push(`API-capable modules still expose simulated operational data: ${forbidden}`);
  }

  const currentState = readText("docs/contexto/ESTADO_ACTUAL.md");
  for (const token of ["admin-service-qa-bo-1-1", "inventory-service-qa", "hr-service-qa", "CHG-191"]) {
    if (!currentState.includes(token)) errors.push(`Current state is missing verified QA fact: ${token}`);
  }
  if (currentState.includes("su configuracion y promocion QA permanecen pendientes")) {
    errors.push("Current state still marks the completed Backoffice promotion as pending.");
  }

  const agents = readText("AGENTES.md");
  for (const stale of [
    "arranque canonico con Emulator aun esta pendiente",
    "schema vacio en QA, sin despliegue confirmado del servicio",
    "schema vacio en QA, servicio y entitlement aun no desplegados"
  ]) {
    if (agents.includes(stale)) errors.push(`Agents still contain obsolete environment state: ${stale}`);
  }
}

if (errors.length) fail("Local-to-QA parity validation failed", errors);
else ok("Local isolation, QA tenant resolution, real API data and current release memory are aligned.");
