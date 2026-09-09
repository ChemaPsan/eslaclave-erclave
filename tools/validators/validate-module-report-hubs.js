const { fail, ok, readText } = require("./shared");

const frontend = readText("frontend/app.js");
const markup = readText("frontend/index.html");
const translations = readText("frontend/i18n/translations.js");
const architecture = readText("docs/arquitectura/reportes_estandar_por_modulo.md");
const errors = [];

if (!markup.includes("chg252-maintenance-load-chg257-report-filters")) {
  errors.push("frontend/index.html must publish the CHG-257 report-filter UI while preserving the CHG-252 loading fix.");
}

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

for (const token of ["standardReportRuntime", "openStandardReportModal", "saveReportBlob", "data-standard-report-index", "reportStatusOptions", "reportFilterOptions", "data-entity-selector", 'en?"Generate":"Generar"']) {
  if (!frontend.includes(token)) errors.push(`Standard report export workflow missing ${token}.`);
}

for (const obsoleteCopy of ["Filter and generate CSV", "Filtrar y generar CSV", "Generate CSV", "Generar CSV", "Standard CSV report", "Reporte CSV estándar", "CSV report generated.", "Reporte CSV generado."]) {
  if (frontend.includes(obsoleteCopy)) errors.push(`Standard report UI still exposes its file format: ${obsoleteCopy}.`);
}

for (const token of ['type="date"', 'type="search"', "production_machine", "facility", "critical", "normal", "urgent"]) {
  if (!frontend.includes(token)) errors.push(`Standard report filters missing ${token}.`);
}

const runtimeReportCodes = [
  "product-services", "recipe-versions", "orders", "deliverables-by-area", "machines",
  "warehouses", "items", "balances", "kardex", "critical-reservations",
  "areas-positions", "workers", "production-capacity", "eligibility",
  "customers", "quotes", "deliveries", "commercial-margin", "service-orders",
  "suppliers", "requisitions", "receipts", "downtime", "spare-parts", "labor-times",
];
for (const code of runtimeReportCodes) {
  if (!frontend.includes(`"${code}"`)) errors.push(`Standard report runtime missing code ${code}.`);
}

for (const [moduleName, clientFile, backendFile] of [
  ["Production", "frontend/api/production.js", "backend/services/production-service/app/reports.py"],
  ["Inventory", "frontend/api/inventory.js", "backend/services/inventory-service/app/reports.py"],
  ["HR", "frontend/api/hr.js", "backend/services/hr-service/app/reports.py"],
  ["Sales", "frontend/api/sales.js", "backend/services/sales-service/app/reports.py"],
  ["Purchasing", "frontend/api/purchasing.js", "backend/services/purchasing-service/app/reports.py"],
  ["Maintenance", "frontend/api/maintenance.js", "backend/services/maintenance-service/app/reports.py"],
]) {
  const client = readText(clientFile);
  const backend = readText(backendFile);
  if (!client.includes("apiDownloadAt") || !client.includes("/reports/")) errors.push(`${moduleName} API client lacks CSV report download support.`);
  if (!backend.includes("REPORT_PERMISSIONS") || !backend.includes("ReportResult")) errors.push(`${moduleName} backend lacks fixed report definitions.`);
}

const csvInfrastructure = readText("backend/shared/erclave_common/csv_reports.py");
for (const token of ["REPORT_MAX_ROWS = 50_000", "\\ufeff", "_UNSAFE_SPREADSHEET_PREFIX", "status_code=204"]) {
  if (!csvInfrastructure.includes(token)) errors.push(`CSV report infrastructure missing ${token}.`);
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
