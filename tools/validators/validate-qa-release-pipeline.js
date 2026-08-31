const fs = require("fs");
const vm = require("vm");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const requiredFiles = [
  ".github/workflows/qa-candidate.yml",
  ".github/workflows/qa-release.yml",
  ".github/workflows/qa-admin-backoffice-config.yml",
  "backend/scripts/smoke_qa.ps1",
  "backend/scripts/promote_qa_traffic.ps1",
  "backend/scripts/configure_qa_backoffice.ps1",
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
  const backofficeConfigWorkflow = readText(requiredFiles[2]);
  const pages = readText(".github/workflows/pages.yml");
  const builder = readText("tools/build-qa-frontend.js");
  const frontendConfig = readText("frontend/api/config.js");
  const mockDb = readText("frontend/data/mockDb.js");
  const smokeQa = readText("backend/scripts/smoke_qa.ps1");
  const promoteQaTraffic = readText("backend/scripts/promote_qa_traffic.ps1");
  const configureQaBackoffice = readText("backend/scripts/configure_qa_backoffice.ps1");
  const qaSeed = readText("backend/scripts/seed_admin_qa_demo.py");
  const dockerfile = readText("backend/Dockerfile");
  const identityPlan = JSON.parse(readText("infra/qa/identity-plan.json"));
  const firebaseQa = JSON.parse(readText("firebase.qa.json"));
  const deployCandidateJob = release.slice(
    release.indexOf("  deploy_candidate:"),
    release.indexOf("  promote_traffic:")
  );
  const promoteTrafficJob = release.slice(
    release.indexOf("  promote_traffic:"),
    release.indexOf("  frontend:")
  );

  if (!candidate.includes("workflow_dispatch:") || /\n\s+push:/.test(candidate)) {
    errors.push("QA candidate workflow must be manual-only.");
  }
  if (!release.includes("workflow_dispatch:") || /\n\s+push:/.test(release)) {
    errors.push("QA release workflow must be manual-only.");
  }
  if (!backofficeConfigWorkflow.includes("workflow_dispatch:") || /\n\s+push:/.test(backofficeConfigWorkflow)) {
    errors.push("QA backoffice configuration workflow must be manual-only.");
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
    if (![release, candidate, promoteQaTraffic].some((content) => content.includes(token))) {
      errors.push(`QA pipeline must include: ${token}`);
    }
  }
  for (const token of [
    "BACKOFFICE_ADMIN_EMAILS: ${{ vars.QA_BACKOFFICE_ADMIN_EMAILS }}",
    'test -n "$BACKOFFICE_ADMIN_EMAILS"',
    "ERCLAVE_BACKOFFICE_ADMIN_EMAILS=$BACKOFFICE_ADMIN_EMAILS",
    'admin_env="^|^'
  ]) {
    if (!release.includes(token)) errors.push(`QA release must preserve Backoffice access configuration: ${token}`);
  }
  for (const token of [
    "environment: qa-services",
    "environment: qa-traffic",
    "CONFIGURE_BACKOFFICE_QA",
    "configure_qa_backoffice.ps1",
    "-Mode Stage",
    "-Mode Promote",
    "QA_BACKOFFICE_ADMIN_EMAILS"
  ]) {
    if (!backofficeConfigWorkflow.includes(token)) {
      errors.push(`QA backoffice correction must include: ${token}`);
    }
  }
  for (const token of [
    '$revisionTag = "backoffice-config"',
    '--update-env-vars "^|^ERCLAVE_BACKOFFICE_ADMIN_EMAILS=$normalizedEmails"',
    "--no-traffic",
    'Where-Object { $_.percent -eq 100 -and $_.revisionName }',
    'if ($currentStable.Count -ne 1 -or $currentStable[0].revisionName -ne $state.rollback_revision)',
    '--to-revisions "$($state.candidate_revision)=100"',
    "Test-Revision"
  ]) {
    if (!configureQaBackoffice.includes(token)) {
      errors.push(`QA backoffice configuration must stage, preflight and verify safely: ${token}`);
    }
  }
  if ([release, backofficeConfigWorkflow, qaSeed].some((content) => content.includes("eslaclavecaf@gmail.com"))) {
    errors.push("QA workflows and seeds must not hardcode the Backoffice administrator email.");
  }
  if (!qaSeed.includes("DEFAULT_EXTRA_OWNER_EMAILS: tuple[str, ...] = ()")) {
    errors.push("QA demo seed must not grant tenant ownership to Backoffice administrators implicitly.");
  }

  const validationWorkflow = readText(".github/workflows/validate.yml");
  for (const workflowPath of ["qa-candidate.yml", "qa-release.yml", "qa-admin-backoffice-config.yml"]) {
    if (!validationWorkflow.includes(`.github/workflows/${workflowPath}`)) {
      errors.push(`Repository verification must run when ${workflowPath} changes.`);
    }
  }
  for (const token of [
    "deploy_candidate()",
    'gcloud run services describe "$service"',
    "local traffic_args=(--no-traffic)",
    "traffic_args=()",
    '"${traffic_args[@]}"',
    "Cloud Run QA bootstrap"
  ]) {
    if (!release.includes(token)) errors.push(`QA service deployment must handle first-service bootstrap: ${token}`);
  }
  for (const token of ["actions/checkout@v4", "ref: ${{ github.sha }}", "backend/scripts/smoke_qa.ps1"]) {
    if (!deployCandidateJob.includes(token)) errors.push(`QA candidate job must check out its immutable workflow smoke source: ${token}`);
  }
  for (const token of ["--format json", "$LASTEXITCODE -ne 0", "ConvertFrom-Json", "$_.tag -eq $RevisionTag"]) {
    if (!smokeQa.includes(token)) errors.push(`QA smoke must resolve the tagged revision from Cloud Run JSON: ${token}`);
  }
  for (const token of ["actions/checkout@v4", "ref: ${{ github.sha }}", "backend/scripts/promote_qa_traffic.ps1"]) {
    if (!promoteTrafficJob.includes(token)) errors.push(`QA traffic job must use its immutable promotion source: ${token}`);
  }
  for (const token of [
    "$targets = @()",
    "$candidates.Count -ne 1",
    "$targets.Count -ne $services.Count",
    "services update-traffic",
    '--to-revisions "$($target.Revision)=100"',
    "$_.revisionName -eq $target.Revision -and $_.percent -eq 100"
  ]) {
    if (!promoteQaTraffic.includes(token)) errors.push(`QA traffic promotion must preflight and verify every revision: ${token}`);
  }
  for (const token of [
    "configure_qa_tenant:",
    'test "${{ inputs.configure_qa_tenant }}" = "true"',
    "scripts/configure_qa_tenant.py"
  ]) {
    if (!release.includes(token)) errors.push(`QA release must explicitly reconcile the QA tenant: ${token}`);
  }
  for (const service of ["admin", "production", "inventory", "hr", "sales", "purchasing", "maintenance"]) {
    if (!candidate.includes(`${service}_service_adapter`)) errors.push(`Candidate workflow must build ${service}-service.`);
    if (!identityPlan.serviceAccounts.some((account) => account.accountId === `erclave-${service}-qa`)) {
      errors.push(`Identity plan must include erclave-${service}-qa.`);
    }
  }
  for (const token of [
    'test "$(wc -l < candidate/qa-images.env)" -eq 7',
    "SALES_IMAGE",
    "QA_SALES_RUNTIME_SERVICE_ACCOUNT",
    "QA_SALES_API_URL",
    "PURCHASING_IMAGE",
    "MAINTENANCE_IMAGE",
    "QA_PURCHASING_RUNTIME_SERVICE_ACCOUNT",
    "QA_MAINTENANCE_RUNTIME_SERVICE_ACCOUNT",
    "QA_PURCHASING_API_URL",
    "QA_MAINTENANCE_API_URL",
    "deploy_candidate sales-service-qa",
    "deploy_candidate purchasing-service-qa",
    "deploy_candidate maintenance-service-qa",
    "ERCLAVE_PRODUCTION_SERVICE_URL=${{ vars.QA_PRODUCTION_API_URL }}"
  ]) {
    if (!release.includes(token)) errors.push(`QA release must include the seven-service runtime: ${token}`);
  }
  const deployerIdentity = identityPlan.serviceAccounts.find(
    (account) => account.accountId === "erclave-github-deployer-qa"
  );
  const adminIdentity = identityPlan.serviceAccounts.find(
    (account) => account.accountId === "erclave-admin-qa"
  );
  if (!adminIdentity?.projectRoles?.includes("roles/firebaseauth.admin")) {
    errors.push("QA Admin runtime identity must include roles/firebaseauth.admin for Backoffice identity lifecycle.");
  }
  const releaseWorkflow = readText(".github/workflows/qa-release.yml");
  if (!releaseWorkflow.includes("ERCLAVE_FIREBASE_WEB_API_KEY=${{ vars.QA_FIREBASE_API_KEY }}")) {
    errors.push("QA Admin runtime must receive the public Firebase Web API key so tenant invitations send email.");
  }
  if (!deployerIdentity?.projectRoles?.includes("roles/firebasehosting.admin")) {
    errors.push("QA deployer identity must include roles/firebasehosting.admin for the gated frontend release.");
  }
  for (const forbidden of ["credentials_json", "service_account_key", "localhost", "firebase-emulator", "demo-erclave"]) {
    if ([candidate, release].some((content) => content.includes(forbidden))) {
      errors.push(`QA workflows contain forbidden token: ${forbidden}`);
    }
  }
  if (/\n\s+push:/.test(pages)) errors.push("GitHub Pages mock must not autodeploy from push.");
  for (const token of [
    "QA_ADMIN_API_URL",
    "QA_PRODUCTION_API_URL",
    "QA_INVENTORY_API_URL",
    "QA_HR_API_URL",
    "QA_SALES_API_URL",
    "QA_PURCHASING_API_URL",
    "QA_MAINTENANCE_API_URL",
    "authMode: \"firebase\""
  ]) {
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
  if (!qaSeed.includes('ACTIVE_DEMO_MODULES = ("admin", "production", "inventory", "hr", "sales", "purchasing", "maintenance")')) {
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
