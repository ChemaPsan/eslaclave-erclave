const { fail, ok, readText } = require("./shared");

const errors = [];
const catalogSource = readText("frontend/i18n/api-errors.js");
const clientSource = readText("frontend/api/client.js");
const appSource = readText("frontend/app.js");
const backofficeSource = readText("frontend/backoffice/app.js");
const backofficeMarkup = readText("frontend/backoffice/index.html");
const stylesSource = readText("frontend/styles.css");

const requiredCodes = [
  "network_unavailable",
  "request_timeout",
  "permission_denied",
  "invalid_order_transition",
  "invalid_quote_transition",
  "invalid_requisition_transition",
  "invalid_maintenance_transition",
  "insufficient_stock",
  "validation_failed",
  "service_unavailable"
];

for (const code of requiredCodes) {
  const block = catalogSource.match(new RegExp(`${code}:\\s*\\{([\\s\\S]*?)\\n\\s*\\}`))?.[1] || "";
  if (!/\bes:\s*"[^"\n]+"/.test(block) || !/\ben:\s*"[^"\n]+"/.test(block)) {
    errors.push(`frontend/i18n/api-errors.js: ${code} must define actionable es/en copy.`);
  }
}

const requiredClientTokens = [
  "getLocalizedErrorMessage",
  "this.serverMessage",
  "this.correlationId",
  "X-Correlation-Id",
  "network_unavailable",
  "request_timeout",
  "Array.isArray(payload?.detail)"
];
for (const token of requiredClientTokens) {
  if (!clientSource.includes(token)) errors.push(`frontend/api/client.js: missing normalized error behavior '${token}'.`);
}
if (clientSource.includes('payload?.error?.message || `API request failed')) {
  errors.push("frontend/api/client.js: backend diagnostic message must not be the user-facing fallback.");
}

const requiredAppTokens = [
  "function showApiError(",
  "getApiErrorTone(error)",
  'toast.dataset.tone = tone',
  'tone === "danger" ? "alert" : "status"',
  "function renderModuleLoadError(",
  "escapeHtml(String(error || \"\"))",
  "box.setAttribute(\"role\", \"alert\")",
  "showApiError(error,messages[code]||t(\"orderInvalidTransition\"))"
];
for (const token of requiredAppTokens) {
  if (!appSource.includes(token)) errors.push(`frontend/app.js: missing semantic feedback behavior '${token}'.`);
}
if (!/change-product-service-status[\s\S]{0,1600}catch\(error\)[\s\S]{0,300}showApiError\([\s\S]{0,300}render\(\)/.test(appSource)) {
  errors.push("frontend/app.js: a rejected product status change must restore the authoritative UI state.");
}
if (!/changeOrderStatus[\s\S]{0,1800}catch\(error\)[\s\S]{0,500}showApiError\([\s\S]{0,300}render\(\)/.test(appSource)) {
  errors.push("frontend/app.js: a rejected production-order transition must restore the authoritative UI state.");
}
if (/state\.(productionApi|hrApi|salesApi|inventoryApi)\.error}<\/p>/.test(appSource)) {
  errors.push("frontend/app.js: module load errors must be escaped before insertion into HTML.");
}
if (/error\.message\s*\|\|/.test(backofficeSource)) {
  errors.push("frontend/backoffice/app.js: raw runtime/backend messages must use the localized resolver.");
}
if (!backofficeMarkup.includes("app.js?v=20260827-chg251-error-feedback")) {
  errors.push("frontend/backoffice/index.html: the cachebuster must expose CHG-251 error localization.");
}

for (const tone of ["success", "warning", "danger"]) {
  if (!stylesSource.includes(`.toast[data-tone="${tone}"]`)) errors.push(`frontend/styles.css: missing ${tone} toast treatment.`);
}

if (errors.length) fail("semantic and localized error feedback validation failed", errors);
else ok("Error feedback is localized by stable code, semantic, accessible and state-safe.");
