const vm = require("vm");
const { fail, ok, readText } = require("./shared");

const activeModuleIds = ["produccion", "almacenes", "ventas", "compras", "mantenimiento", "recursos-humanos", "administracion"];

function loadModules() {
  const source = readText("frontend/data/modules.js");
  const transformed = `${source
    .replace("export const modules =", "const modules =")
    .replace("export const erpSubmoduleCatalog =", "const erpSubmoduleCatalog =")}\nmodules;`;
  return vm.runInNewContext(transformed, {}, { filename: "frontend/data/modules.js" });
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

const modules = loadModules();
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
}

if (errors.length) {
  fail("active module localization validation failed", errors);
} else {
  ok("active MVP module metadata has ES/EN visible-copy parity.");
}
