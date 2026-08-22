const { fail, ok, readText } = require("./shared");

const frontend = readText("frontend/app.js");
const translations = readText("frontend/i18n/translations.js");
const architecture = readText("docs/arquitectura/reportes_estandar_por_modulo.md");
const errors = [];

for (const moduleId of ["produccion", "almacenes", "recursos-humanos", "ventas", "administracion", "compras", "gastos", "costos", "contabilidad", "reportes"]) {
  if (!new RegExp(`["']?${moduleId}["']?\\s*:\\s*\\[`).test(frontend)) errors.push(`Standard report catalog missing module ${moduleId}.`);
  if (!architecture.includes(`| ${moduleId === "recursos-humanos" ? "Recursos Humanos" : moduleId[0].toUpperCase()+moduleId.slice(1)}`)) errors.push(`Report architecture matrix missing module ${moduleId}.`);
}

if (!frontend.includes('} else if (module.id === "administracion") {') || !frontend.includes("renderAdminApiPanel(module);")) {
  errors.push("Administration must keep its configuration hub exception.");
}

for (const token of ["function getStandardReports", "standard-report-grid", "standardReportNoData", "topbarPrimary.hidden = !state.activeSubmodule"]) {
  if (!frontend.includes(token)) errors.push(`Module report hub missing ${token}.`);
}

const rootStart = frontend.indexOf('const standardReports = getStandardReports(module);');
const rootEnd = frontend.indexOf("function renderStatusStrip", rootStart);
const rootView = frontend.slice(rootStart, rootEnd);
for (const forbidden of ["hero-action", "quickCapture", "open-recipe", "open-order", 'data-action="module-primary"']) {
  if (rootView.includes(forbidden)) errors.push(`Module root contains an operational action: ${forbidden}.`);
}

for (const token of ["standardReportsTitle", "standardReportsIntro", "specializedReportsDetail", "standardReportNoData"]) {
  if (translations.split(token).length - 1 < 2) errors.push(`Module report translation ${token} is not bilingual.`);
}

for (const token of ["primera vista", "solo lectura", "modulos futuros", "permanece inactivo", "administracion es la excepcion", "validate:module-reports"]) {
  if (!architecture.toLowerCase().includes(token)) errors.push(`Module report policy missing ${token}.`);
}

if (errors.length) fail("module report hub validation failed", errors);
else ok("module roots are read-only standard report hubs and specialized Reports remains planned.");
