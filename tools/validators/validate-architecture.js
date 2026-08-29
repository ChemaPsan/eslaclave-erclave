const fs = require("fs");
const path = require("path");
const { fail, fromRoot, listFiles, ok, readText } = require("./shared");

const microfrontendsDir = fromRoot("frontend/microfrontends");
const servicesDir = fromRoot("backend/services");
const errors = [];

const expectedMicrofrontends = [
  "produccion",
  "almacenes",
  "compras",
  "ventas",
  "gastos",
  "costos",
  "reportes",
  "administracion",
  "contabilidad",
  "recursos-humanos",
  "mantenimiento"
];

const expectedServices = [
  "production-service",
  "inventory-service",
  "purchasing-service",
  "sales-service",
  "expenses-service",
  "costing-service",
  "reporting-service",
  "admin-service",
  "accounting-service",
  "hr-service",
  "maintenance-service"
];

for (const id of expectedMicrofrontends) {
  const manifestPath = path.join(microfrontendsDir, id, "manifest.js");
  if (!fs.existsSync(manifestPath)) errors.push(`Missing microfrontend manifest: frontend/microfrontends/${id}/manifest.js`);
}

for (const id of expectedServices) {
  const readmePath = path.join(servicesDir, id, "README.md");
  if (!fs.existsSync(readmePath)) errors.push(`Missing service README: backend/services/${id}/README.md`);
}

const registry = readText("frontend/microfrontends/registry.js");
for (const id of expectedMicrofrontends) {
  if (!registry.includes(`./${id}/manifest.js`)) {
    errors.push(`Microfrontend registry does not include ${id}.`);
  }
}

const microfrontendFiles = listFiles("frontend/microfrontends", (file) => file.endsWith(".js"));
for (const relativePath of microfrontendFiles) {
  const normalizedRelativePath = relativePath.replace(/\\/g, "/");
  if (normalizedRelativePath === "frontend/microfrontends/registry.js") continue;

  const parts = relativePath.split(path.sep);
  const owner = parts[2];
  const source = readText(relativePath);
  const statusMatch = source.match(/implementationStatus:\s*["'](implemented|planned)["']/);
  if (!statusMatch) {
    errors.push(`${relativePath} must declare implementationStatus as implemented or planned.`);
  }
  const permissionArray = source.match(/permissions:\s*\[([^\]]*)\]/s)?.[1] || "";
  const permissionCodes = [...permissionArray.matchAll(/["']([^"']+)["']/g)].map((match) => match[1]);
  for (const code of permissionCodes) {
    if (code.includes(":") || !/^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$/.test(code)) {
      errors.push(`${relativePath} contains obsolete or invalid permission code ${code}.`);
    }
  }
  if (statusMatch?.[1] === "implemented" && permissionCodes.length === 0) {
    errors.push(`${relativePath} is implemented but declares no permissions.`);
  }
  const importMatches = [...source.matchAll(/from\s+["']([^"']+)["']/g)];

  for (const match of importMatches) {
    const target = match[1];
    if (!target.startsWith(".")) continue;
    const resolved = path.normalize(path.join(path.dirname(relativePath), target));
    const resolvedParts = resolved.split(path.sep);
    const isMicrofrontendImport = resolvedParts[0] === "frontend" && resolvedParts[1] === "microfrontends";
    const targetOwner = resolvedParts[2];

    if (isMicrofrontendImport && targetOwner && targetOwner !== owner) {
      errors.push(`${relativePath} imports another microfrontend (${target}). Use a contract instead.`);
    }
  }
}

const frontendJsFiles = listFiles("frontend", (file) => file.endsWith(".js"));
for (const relativePath of frontendJsFiles) {
  const normalizedRelativePath = relativePath.replace(/\\/g, "/");
  const source = readText(relativePath);
  if (source.includes("fetch(") && !normalizedRelativePath.startsWith("frontend/api/")) {
    errors.push(`${relativePath} calls fetch outside frontend/api/. Use the API client boundary.`);
  }
}

const appSource = readText("frontend/app.js");
if (!appSource.includes("getAdminDashboard")) {
  errors.push("frontend/app.js must consume admin-service through frontend/api/admin.js.");
}

if (errors.length) {
  fail("architecture validation failed", errors);
} else {
  ok("microfrontend manifests, service folders, registry, and cross-import boundaries are valid.");
}
