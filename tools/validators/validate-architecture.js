const fs = require("fs");
const path = require("path");
const { fail, fromRoot, listFiles, ok, readText } = require("./shared");

const microfrontendsDir = fromRoot("frontend/microfrontends");
const servicesDir = fromRoot("backend/services");
const errors = [];

function getImplementedModulePermissions(openApiSource, moduleCode) {
  const pathsIndex = openApiSource.indexOf("\npaths:");
  const header = pathsIndex >= 0 ? openApiSource.slice(0, pathsIndex) : openApiSource;
  if (/^x-implementation-status:\s*planned\s*$/m.test(header)) return [];

  const lines = openApiSource.split(/\r?\n/);
  const permissions = new Set();
  const methodPattern = /^    (get|post|put|patch|delete):/;
  for (let index = 0; index < lines.length; index += 1) {
    if (!methodPattern.test(lines[index])) continue;
    const block = [lines[index]];
    let next = index + 1;
    while (
      next < lines.length
      && !methodPattern.test(lines[next])
      && !/^  \//.test(lines[next])
      && !/^components:/.test(lines[next])
    ) {
      block.push(lines[next]);
      next += 1;
    }
    index = next - 1;
    const operation = block.join("\n");
    if (/x-implementation-status:\s*planned/.test(operation)) continue;
    const requiredModule = operation.match(/x-required-module:\s*([a-z][a-z0-9_]*)/)?.[1];
    if (requiredModule !== moduleCode) continue;
    const permissionPattern = new RegExp(`${moduleCode}\\.[a-z0-9_]+(?:\\.[a-z0-9_]+)+`, "g");
    for (const permission of operation.match(permissionPattern) || []) permissions.add(permission);
  }
  return [...permissions].sort();
}

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
  const service = source.match(/service:\s*["']([^"']+)["']/)?.[1];
  if (!service) {
    errors.push(`${relativePath} must declare its owning service.`);
  } else if (statusMatch?.[1] === "implemented") {
    const moduleCode = service.replace(/-service$/, "");
    const contractPath = `contracts/api/${service}.openapi.yaml`;
    const contractFullPath = fromRoot(...contractPath.split("/"));
    if (!fs.existsSync(contractFullPath)) {
      errors.push(`${relativePath} references ${service} without ${contractPath}.`);
    } else {
      const expectedPermissions = getImplementedModulePermissions(readText(contractPath), moduleCode);
      const declaredPermissions = [...new Set(permissionCodes)].sort();
      const missingPermissions = expectedPermissions.filter((code) => !declaredPermissions.includes(code));
      const extraPermissions = declaredPermissions.filter((code) => !expectedPermissions.includes(code));
      if (missingPermissions.length) {
        errors.push(`${relativePath} omits implemented ${moduleCode} permissions: ${missingPermissions.join(", ")}.`);
      }
      if (extraPermissions.length) {
        errors.push(`${relativePath} declares permissions without an implemented ${moduleCode} operation: ${extraPermissions.join(", ")}.`);
      }
    }
  } else if (statusMatch?.[1] === "planned" && permissionCodes.length) {
    errors.push(`${relativePath} is planned and must not advertise runtime permissions.`);
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
