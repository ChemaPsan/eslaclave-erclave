const vm = require("vm");
const { fail, ok, readText } = require("./shared");

const checks = [
  ["frontend/data/resources.js", ["defaultLaborAreas", 'areaId: "area_preparacion"']],
  ["frontend/data/mockDb.js", ["loadLaborAreas()", "addLaborArea(item)", "updateLaborArea(item)", "role.areaId === item.id"]],
  ["frontend/app.js", [
    'name="areaId"',
    "mockDb.findLaborArea(areaId)",
    'hr.area.create',
    'hr.area.update',
    'hr.position.create',
    'hr.position.update',
    'hr: { es: "Recursos Humanos", en: "Human Resources", order: 25 }',
    "groupAdminPermissions(permissions = [])",
    'data-permission-module="${moduleCode}"',
    '<strong>${group.label}</strong>'
  ]],
  ["backend/services/admin-service/tests/test_permission_seeds.py", [
    "test_hr_contract_seeds_its_own_permission_group_without_production_legacy_codes",
    '"hr.area.read"',
    'startswith("production.labor")'
  ]],
  ["contracts/api/hr-service.openapi.yaml", [
    "/v1/hr/areas/{id}:",
    "hr.area.read",
    "hr.area.create",
    "hr.area.update",
    "hr.position.read",
    "hr.position.create",
    "hr.position.update",
    "AreaUpdate"
  ]],
  ["modulos/10_recursos_humanos.md", ["No se crean áreas desde texto libre", "permisos"]]
];

const errors = [];
for (const [file, fragments] of checks) {
  const source = readText(file);
  for (const fragment of fragments) {
    if (!source.includes(fragment)) errors.push(`${file}: missing ${JSON.stringify(fragment)}.`);
  }
}

const roleModal = readText("frontend/app.js").split("function openLaborRoleModal", 2)[1]?.split("function saveLaborRoleForm", 1)[0] || "";
const workerModal = readText("frontend/app.js").split("function openWorkerModal", 2)[1]?.split("async function saveWorkerForm", 1)[0] || "";
for (const token of ['name="curp" minlength="18" maxlength="18"', 'name="rfc" minlength="13" maxlength="13"', 'name="nss" inputmode="numeric" minlength="11" maxlength="11"']) {
  if (!workerModal.includes(token)) errors.push(`frontend/app.js: worker identity guardrail is missing ${token}.`);
}
if (/name=["']area["']/.test(roleModal)) {
  errors.push("frontend/app.js: labor role form must not accept a free-text area.");
}

const areaSaveFlow = readText("frontend/app.js").split("async function saveLaborAreaForm", 2)[1]?.split("function openLaborRoleModal", 1)[0] || "";
if (areaSaveFlow.includes("createProductionProductService") || areaSaveFlow.includes("updateProductionProductService")) {
  errors.push("frontend/app.js: labor area save flow must not call Production product APIs.");
}
if (areaSaveFlow.indexOf("const item =") > areaSaveFlow.indexOf("await createHrArea")) {
  errors.push("frontend/app.js: labor area item must be initialized before the HR API flow.");
}

try {
  const resourcesSource = `${readText("frontend/data/resources.js").replaceAll("export const ", "const ")}\n({ defaultLaborAreas, defaultLaborRoles, defaultProductsServices, defaultMachines, defaultRecipes, defaultOrders });`;
  const defaults = vm.runInNewContext(resourcesSource, {});
  const storage = new Map();
  const localStorage = {
    getItem: (key) => storage.has(key) ? storage.get(key) : null,
    setItem: (key, value) => storage.set(key, String(value))
  };
  const mockDbSource = `${readText("frontend/data/mockDb.js")
    .replace(/^import .*;\r?\n/gm, "")
    .replace("export const mockDb =", "const mockDb =")}\nmockDb;`;
  const mockDb = vm.runInNewContext(mockDbSource, {
    ...defaults,
    getApiMode: () => "mock",
    getConfiguredTenantId: () => "local",
    getDemoTenantId: () => "local",
    localStorage,
    JSON,
    Error
  });
  const area = { id: "area_test", code: "TEST", name: "Test", description: "", status: "Activo" };
  mockDb.addLaborArea(area);
  mockDb.addLaborRole({ id: "role_test", areaId: area.id, area: "texto incorrecto", name: "Operador", position: "Operador", quantity: 1 });
  if (mockDb.findLaborRole("role_test").area !== area.name) errors.push("mockDb must resolve the area name from areaId.");
  let rejected = false;
  try {
    mockDb.addLaborRole({ id: "role_invalid", areaId: "area_missing", name: "Invalid", position: "Invalid" });
  } catch (error) {
    rejected = error.message === "labor_area_not_found";
  }
  if (!rejected) errors.push("mockDb must reject positions linked to missing areas.");
  mockDb.updateLaborArea({ ...area, name: "Test actualizado" });
  if (mockDb.findLaborRole("role_test").area !== "Test actualizado") errors.push("renaming an area must update the local role display snapshot.");
} catch (error) {
  errors.push(`labor catalog behavior test could not run: ${error.message}`);
}

if (errors.length) fail("labor area/position separation validation failed", errors);
else ok("labor areas and positions are independent catalogs with granular permissions.");
