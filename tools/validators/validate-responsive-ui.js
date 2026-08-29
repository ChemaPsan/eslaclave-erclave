const { fail, ok, readText } = require("./shared");

const checks = [
  ["frontend/styles.css", [
    "container-name: module-panel",
    "@container module-panel",
    "container-name: modal-sheet",
    "@container modal-sheet",
    "@media (prefers-reduced-motion: reduce)",
    ".skip-link"
  ]],
  ["frontend/backoffice/styles.css", [
    "container-name: tenant-admin-panel",
    "@container tenant-admin-panel"
  ]],
  ["frontend/index.html", [
    'class="skip-link"',
    'id="mainWorkspace"',
    'aria-label="Modulos y submodulos"',
    'aria-live="polite"'
  ]],
  ["AGENTES.md", ["docs/arquitectura/estandar_responsive_transversal.md"]],
  ["docs/qa/guia_pruebas_qa_mvp.md", ["Checklist responsive transversal"]]
];

const errors = [];

for (const [file, fragments] of checks) {
  const source = readText(file);
  for (const fragment of fragments) {
    if (!source.includes(fragment)) {
      errors.push(`${file}: missing responsive guardrail ${JSON.stringify(fragment)}.`);
    }
  }
}

const mainStyles = readText("frontend/styles.css");
const mainMarkup = readText("frontend/index.html");
const mainApp = readText("frontend/app.js");
if (mainStyles.includes(".flow-guide-card[open] .flow-guide-steps")) {
  errors.push("frontend/styles.css: open flow guides must keep the standard vertical rail; scope layout exceptions to an explicit screen class.");
}
if (!mainStyles.includes("grid-template-columns: minmax(220px, 280px) minmax(0, 1fr)")) {
  errors.push("frontend/styles.css: missing the standard vertical flow rail layout.");
}
if (!mainApp.includes('renderFlowGuide(getPurchasingFlowTitle(title),getPurchasingFlowSteps(id))') || !mainApp.includes('renderFlowGuide(getMaintenanceFlowTitle(id),getMaintenanceFlowSteps(id))')) {
  errors.push("Purchasing and Maintenance must reuse the standard responsive flow rail.");
}
if (!mainStyles.includes("content: attr(data-open-label)") || !mainApp.includes('data-open-label="${escapeAttribute(openCopy)}"')) {
  errors.push("Collapsed flow guides must expose their localized open label.");
}
if (!mainMarkup.includes("app.js?v=20260828-chg252-maintenance-load")) {
  errors.push("frontend/index.html: the main app cachebuster must expose CHG-252 while preserving localized error feedback.");
}
if (!mainMarkup.includes("styles.css?v=20260827-chg251-error-feedback")) {
  errors.push("frontend/index.html: the main stylesheet cachebuster must expose CHG-251 semantic feedback styling to open sessions.");
}
if (!mainStyles.includes("CHG-249: jerarquia sobria y reversible") || !mainStyles.includes(".catalog-card-actions .small-action") || !mainStyles.includes('[data-theme="dark"] .chip.active')) {
  errors.push("frontend/styles.css: sober action/status styling must remain isolated, readable and dark-theme aware.");
}

const insightStart = mainMarkup.indexOf('<aside class="insight-panel">');
const insightEnd = mainMarkup.indexOf("</aside>", insightStart);
const statusPosition = mainMarkup.indexOf('<section class="status-strip"', insightStart);
const alertsPosition = mainMarkup.indexOf('data-i18n="alertsTitle"', insightStart);
if (insightStart < 0 || insightEnd < 0 || statusPosition < insightStart || statusPosition > insightEnd || alertsPosition < statusPosition || alertsPosition > insightEnd) {
  errors.push("frontend/index.html: operational indicators must live inside insight-panel immediately before operational alerts.");
}

if (!mainStyles.includes("container: insight-panel / inline-size") || !mainStyles.includes("@container insight-panel")) {
  errors.push("frontend/styles.css: the relocated KPI strip must respond to the real insight-panel width.");
}
const topbarStart = mainMarkup.indexOf('<header class="topbar">');
const topbarEnd = mainMarkup.indexOf("</header>", topbarStart);
const contextPosition = mainMarkup.indexOf('<section class="context-bar"', topbarStart);
if (topbarStart < 0 || topbarEnd < 0 || contextPosition < topbarStart || contextPosition > topbarEnd) {
  errors.push("frontend/index.html: session context and contextual actions must share the compact topbar.");
}
if (!/\.main-panel\s*>\s*\.panel-head h2\s*\{[^}]*display:\s*none/s.test(mainStyles) || !/\.submodule-screen-head\s*\{[^}]*min-height:\s*88px/s.test(mainStyles)) {
  errors.push("frontend/styles.css: submodules must not repeat the primary title in an oversized pre-hero header.");
}
if (!mainStyles.includes("container: maintenance-order-card / inline-size") || !mainApp.includes('class="catalog-card maintenance-order-card"')) {
  errors.push("Maintenance orders must use their dedicated responsive card container.");
}
if (/\.resource-check\s+p\s*\{[^}]*white-space:\s*nowrap/s.test(mainStyles)) {
  errors.push("frontend/styles.css: resource validation results must wrap instead of forcing modal overflow.");
}
if (!/@container modal-sheet \(max-width: 680px\)[\s\S]*?\.resource-check-grid[\s\S]*?\.purchasing-requisition-line/.test(mainStyles)) {
  errors.push("frontend/styles.css: modal container rules must compact resource checks and purchasing lines.");
}
if (!/\.small-action\s*\{[^}]*min-height:\s*44px/s.test(mainStyles)) {
  errors.push("frontend/styles.css: small operational actions must preserve the 44px touch target.");
}
if (mainApp.includes('<span class="chip active">${moduleStatus}</span>')) {
  errors.push("frontend/app.js: internal module persistence status must not be exposed as a user-facing badge.");
}

if (errors.length) {
  fail("responsive UI validation failed", errors);
} else {
  ok("responsive containers, accessibility hooks and agent documentation are present.");
}
