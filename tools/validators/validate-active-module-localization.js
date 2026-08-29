const vm = require("vm");
const { fail, ok, readText } = require("./shared");

const activeModuleIds = ["produccion", "almacenes", "ventas", "compras", "mantenimiento", "recursos-humanos", "administracion"];

function loadModules() {
  const source = readText("frontend/data/modules.js");
  const transformed = `${source
    .replace("export const modules =", "const modules =")
    .replace("export const erpSubmoduleCatalog =", "const erpSubmoduleCatalog =")}\n({ modules, erpSubmoduleCatalog });`;
  return vm.runInNewContext(transformed, {}, { filename: "frontend/data/modules.js" });
}

function slugify(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function isBlank(value) {
  return typeof value !== "string" || !value.trim();
}

function sameLength(module, field, englishField, errors) {
  const base = module[field] || [];
  const english = module[englishField] || [];
  if (!Array.isArray(base) || !Array.isArray(english)) {
    errors.push(`${module.id}: ${field}/${englishField} must both be arrays.`);
    return;
  }
  if (base.length !== english.length) {
    errors.push(`${module.id}: ${englishField} must mirror ${field} length (${english.length}/${base.length}).`);
  }
}

function validateNestedRows(module, field, englishField, errors) {
  sameLength(module, field, englishField, errors);
  const base = module[field] || [];
  const english = module[englishField] || [];
  for (let index = 0; index < Math.min(base.length, english.length); index += 1) {
    if (Array.isArray(base[index]) && Array.isArray(english[index]) && base[index].length !== english[index].length) {
      errors.push(`${module.id}: ${englishField}[${index}] must mirror ${field}[${index}] column count.`);
    }
  }
}

function validateTable(module, errors) {
  if (!module.tableEn) {
    errors.push(`${module.id}: missing tableEn.`);
    return;
  }
  if ((module.table.columns || []).length !== (module.tableEn.columns || []).length) {
    errors.push(`${module.id}: tableEn.columns must mirror table.columns length.`);
  }
  if ((module.table.rows || []).length !== (module.tableEn.rows || []).length) {
    errors.push(`${module.id}: tableEn.rows must mirror table.rows length.`);
  }
}

const { modules, erpSubmoduleCatalog } = loadModules();
const errors = [];

for (const id of activeModuleIds) {
  const module = modules.find((item) => item.id === id);
  if (!module) {
    errors.push(`Missing active module: ${id}`);
    continue;
  }

  for (const field of ["title", "eyebrow", "summary", "primary", "status"]) {
    const englishField = `${field}En`;
    if (isBlank(module[englishField])) {
      errors.push(`${id}: missing ${englishField}.`);
    }
  }

  validateNestedRows(module, "kpis", "kpisEn", errors);
  sameLength(module, "workflow", "workflowEn", errors);
  validateNestedRows(module, "validations", "validationsEn", errors);
  validateNestedRows(module, "form", "formEn", errors);
  validateNestedRows(module, "records", "recordsEn", errors);
  validateTable(module, errors);
  for (const [name, detail, explicitId] of module.submodules || []) {
    const submoduleId = explicitId || slugify(name);
    const localized = erpSubmoduleCatalog[module.id]?.[submoduleId];
    if (!localized) {
      errors.push(`${id}: missing bilingual submodule catalog entry for ${submoduleId}.`);
      continue;
    }
    if (isBlank(localized.enName) || isBlank(localized.enDetail)) {
      errors.push(`${id}/${submoduleId}: enName and enDetail are required.`);
    }
    if (!Array.isArray(localized.focus?.es) || !Array.isArray(localized.focus?.en) || localized.focus.es.length !== localized.focus.en.length) {
      errors.push(`${id}/${submoduleId}: focus.es/focus.en must be mirrored arrays.`);
    }
    if (isBlank(name) || isBlank(detail)) {
      errors.push(`${id}/${submoduleId}: Spanish name and detail are required in module metadata.`);
    }
  }
}

if (errors.length) {
  fail("active module localization validation failed", errors);
} else {
  ok("active MVP module metadata has ES/EN visible-copy parity.");
}
