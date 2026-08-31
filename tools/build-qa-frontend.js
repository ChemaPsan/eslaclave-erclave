const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const source = path.join(repoRoot, "frontend");
const output = path.resolve(repoRoot, process.argv[2] || "dist/qa-frontend");

const required = [
  "QA_ADMIN_API_URL",
  "QA_PRODUCTION_API_URL",
  "QA_INVENTORY_API_URL",
  "QA_HR_API_URL",
  "QA_SALES_API_URL",
  "QA_PURCHASING_API_URL",
  "QA_MAINTENANCE_API_URL",
  "QA_FIREBASE_API_KEY",
  "QA_FIREBASE_AUTH_DOMAIN",
  "QA_FIREBASE_PROJECT_ID",
  "QA_FIREBASE_STORAGE_BUCKET",
  "QA_FIREBASE_MESSAGING_SENDER_ID",
  "QA_FIREBASE_APP_ID"
];

const missing = required.filter((key) => !String(process.env[key] || "").trim());
if (missing.length) throw new Error(`Missing QA frontend variables: ${missing.join(", ")}`);

function requirePublicHttps(name) {
  const value = process.env[name];
  const parsed = new URL(value);
  if (parsed.protocol !== "https:" || ["localhost", "127.0.0.1", "::1"].includes(parsed.hostname)) {
    throw new Error(`${name} must be a public HTTPS URL.`);
  }
  return value.replace(/\/$/, "");
}

const config = {
  apiMode: "api",
  authMode: "firebase",
  inventoryApiMode: "api",
  apiBaseUrl: requirePublicHttps("QA_ADMIN_API_URL"),
  productionApiBaseUrl: requirePublicHttps("QA_PRODUCTION_API_URL"),
  inventoryApiBaseUrl: requirePublicHttps("QA_INVENTORY_API_URL"),
  hrApiBaseUrl: requirePublicHttps("QA_HR_API_URL"),
  salesApiBaseUrl: requirePublicHttps("QA_SALES_API_URL"),
  purchasingApiBaseUrl: requirePublicHttps("QA_PURCHASING_API_URL"),
  maintenanceApiBaseUrl: requirePublicHttps("QA_MAINTENANCE_API_URL"),
  firebaseConfig: {
    apiKey: process.env.QA_FIREBASE_API_KEY,
    authDomain: process.env.QA_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.QA_FIREBASE_PROJECT_ID,
    storageBucket: process.env.QA_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.QA_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.QA_FIREBASE_APP_ID
  }
};

if (config.firebaseConfig.projectId !== "erclave") {
  throw new Error("QA_FIREBASE_PROJECT_ID must be the isolated QA project 'erclave'.");
}

const backofficeConfig = {
  apiMode: "api",
  authMode: "firebase",
  apiBaseUrl: config.apiBaseUrl,
  firebaseConfig: config.firebaseConfig
};

fs.rmSync(output, { recursive: true, force: true });
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.cpSync(source, output, { recursive: true });
fs.writeFileSync(path.join(output, "env.js"), `window.ERCLAVE_CONFIG = ${JSON.stringify(config, null, 2)};\n`);
fs.writeFileSync(path.join(output, "backoffice", "env.js"), `window.ERCLAVE_CONFIG = ${JSON.stringify(backofficeConfig, null, 2)};\n`);

const forbidden = ["localhost", "127.0.0.1", "firebase-emulator", "demo-erclave", "erclave-api-tenant-id"];
for (const relative of ["env.js", path.join("backoffice", "env.js")]) {
  const content = fs.readFileSync(path.join(output, relative), "utf8");
  for (const token of forbidden) {
    if (content.includes(token)) throw new Error(`QA artifact ${relative} contains forbidden token: ${token}`);
  }
}

const manifest = {
  environment: "qa",
  sourceSha: process.env.GITHUB_SHA || "local-validation",
  generatedAt: new Date().toISOString(),
  services: {
    admin: config.apiBaseUrl,
    production: config.productionApiBaseUrl,
    inventory: config.inventoryApiBaseUrl,
    hr: config.hrApiBaseUrl,
    sales: config.salesApiBaseUrl,
    purchasing: config.purchasingApiBaseUrl,
    maintenance: config.maintenanceApiBaseUrl
  },
  firebaseProjectId: config.firebaseConfig.projectId
};
fs.writeFileSync(path.join(output, "release-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`[OK] QA frontend artifact created at ${output}`);
