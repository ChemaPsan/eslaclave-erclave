const fs = require("fs");
const vm = require("vm");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const requiredFiles = [
  ".github/workflows/qa-candidate.yml",
  ".github/workflows/qa-release.yml",
  "backend/scripts/smoke_qa.ps1",
  "firebase.qa.json",
  "infra/qa/identity-plan.json",
  "infra/qa/README.md",
  "tools/build-qa-frontend.js",
  "backend/scripts/configure_qa_tenant.py",
  ".dockerignore"
];

for (const file of requiredFiles) {
  if (!fs.existsSync(fromRoot(file))) errors.push(`Missing QA release file: ${file}`);
}

if (!errors.length) {
  const candidate = readText(requiredFiles[0]);
  const release = readText(requiredFiles[1]);
  const pages = readText(".github/workflows/pages.yml");
  const builder = readText("tools/build-qa-frontend.js");
  const frontendConfig = readText("frontend/api/config.js");
  const mockDb = readText("frontend/data/mockDb.js");
  const qaSeed = readText("backend/scripts/seed_admin_qa_demo.py");
  const dockerfile = readText("backend/Dockerfile");
  const identityPlan = JSON.parse(readText("infra/qa/identity-plan.json"));
  const firebaseQa = JSON.parse(readText("firebase.qa.json"));

  if (!candidate.includes("workflow_dispatch:") || /\n\s+push:/.test(candidate)) {
    errors.push("QA candidate workflow must be manual-only.");
  }
  if (!release.includes("workflow_dispatch:") || /\n\s+push:/.test(release)) {
    errors.push("QA release workflow must be manual-only.");
  }
  for (const environment of ["qa-build", "qa-database", "qa-services", "qa-traffic", "qa-frontend"]) {
    const source = environment === "qa-build" ? candidate : release;
    if (!source.includes(`environment: ${environment}`)) errors.push(`Missing protected environment: ${environment}`);
  }
  for (const token of [
    "google-github-actions/auth@v2",
    "workload_identity_provider",
    "--no-traffic",
    "smoke_qa.ps1",
    "update-traffic",
    "firebase-tools@15.1.0",
    "ERCLAVE_API_PUBLIC_BASE_URL"
  ]) {
    if (!release.includes(token) && !candidate.includes(token)) errors.push(`QA pipeline must include: ${token}`);
  }
  for (const token of [
    "configure_qa_tenant:",
    'test "${{ inputs.configure_qa_tenant }}" = "true"',
    "scripts/configure_qa_tenant.py"
  ]) {
    if (!release.includes(token)) errors.push(`QA release must explicitly reconcile the QA tenant: ${token}`);
  }
  for (const service of ["admin", "production", "inventory", "hr"]) {
    if (!candidate.includes(`${service}_service_adapter`)) errors.push(`Candidate workflow must build ${service}-service.`);
    if (!identityPlan.serviceAccounts.some((account) => account.accountId === `erclave-${service}-qa`)) {
      errors.push(`Identity plan must include erclave-${service}-qa.`);
    }
  }
  for (const forbidden of ["credentials_json", "service_account_key", "localhost", "firebase-emulator", "demo-erclave"]) {
    if ([candidate, release].some((content) => content.includes(forbidden))) {
      errors.push(`QA workflows contain forbidden token: ${forbidden}`);
    }
  }
  if (/\n\s+push:/.test(pages)) errors.push("GitHub Pages mock must not autodeploy from push.");
  for (const token of ["QA_ADMIN_API_URL", "QA_INVENTORY_API_URL", "QA_HR_API_URL", "authMode: \"firebase\""]) {
    if (!builder.includes(token)) errors.push(`QA frontend builder must include: ${token}`);
  }
  if (!builder.includes('const forbidden = ["localhost", "127.0.0.1", "firebase-emulator", "demo-erclave"')) {
    errors.push("QA frontend builder must reject local and emulator tokens.");
  }
  for (const token of [
    'if (!isLocalPreviewHost()) return getRuntimeConfigValue("apiMode") || "api";',
    'if (!isLocalPreviewHost()) return getRuntimeConfigValue("inventoryApiMode") === "api";',
    "return runtimeBaseUrl;"
  ]) {
    if (!frontendConfig.includes(token)) errors.push(`QA frontend runtime must ignore local overrides: ${token}`);
  }
  for (const token of ["const apiMemoryStore = new Map()", "readStoredValue", "writeStoredValue"]) {
    if (!mockDb.includes(token)) errors.push(`API-mode frontend cache must be memory-only: ${token}`);
  }
  const mockDbForApi = vm.runInNewContext(
    `${mockDb
      .replace(/^import .*resources\.js";\r?\n/m, "")
      .replace(/^import .*config\.js";\r?\n/m, "")
      .replace("export const mockDb =", "const mockDb =")}\nmockDb;`,
    {
      defaultProductsServices: [],
      defaultLaborAreas: [],
      defaultLaborRoles: [],
      defaultMachines: [],
      defaultRecipes: [],
      defaultOrders: [],
      getApiMode: () => "api",
      getDemoTenantId: () => "ten_qa",
      localStorage: {
        getItem: () => JSON.stringify([{ id: "stale-browser-record" }]),
        setItem: () => { throw new Error("API mode must not write operational data to localStorage."); }
      }
    }
  );
  if (mockDbForApi.loadProductsServices().length !== 0) {
    errors.push("API-mode frontend cache must ignore stale operational localStorage records.");
  }
  mockDbForApi.saveProductsServices([{ id: "api-record" }]);
  if (mockDbForApi.loadProductsServices()[0]?.id !== "api-record") {
    errors.push("API-mode frontend cache must retain freshly loaded API data in memory.");
  }
  if (!qaSeed.includes('ACTIVE_DEMO_MODULES = ("admin", "production", "inventory", "hr")')) {
    errors.push("QA seed must enable only modules backed by deployed real services.");
  }
  if (!qaSeed.includes("module_code not in ({active_module_codes})")) {
    errors.push("QA seed must deactivate entitlements for modules without real services.");
  }
  for (const token of ["COPY backend/scripts ./scripts", "COPY contracts ./contracts"]) {
    if (!dockerfile.includes(token)) errors.push(`QA image must package release configuration inputs: ${token}`);
  }
  if (!candidate.includes("docker build --file backend/Dockerfile") || !candidate.includes('--tag "$image" .')) {
    errors.push("QA candidate must build from repository root so contracts are packaged.");
  }
  if (firebaseQa.hosting?.site !== "erclave" || firebaseQa.hosting?.public !== "dist/qa-frontend") {
    errors.push("firebase.qa.json must deploy the sanitized artifact to the erclave QA site.");
  }
}

if (errors.length) fail("QA release pipeline validation failed", errors);
else ok("QA release pipeline is manual, immutable, federated, gated and free of local runtime configuration.");
