const { fail, ok, readText } = require("./shared");

const app = readText("frontend/app.js");
const api = readText("frontend/api/admin.js");
const css = readText("frontend/styles.css");
const translations = readText("frontend/i18n/translations.js");
const errors = [];

const requiredAppMarkers = [
  "permissionEditor: null",
  "function openPermissionEditor",
  "function escapeHtml",
  "original: new Map",
  "draft: new Map",
  "getPermissionEditorDiff",
  "data-permission-search",
  "data-permission-filter",
  "permission-select-visible",
  "permission-clear-visible",
  "data-permission-module-check",
  "data-permission-id",
  "permission-editor-save",
  "permission-editor-reload",
  "rebasePermissionEditor",
  "permission.assignable_to_tenant_role === true",
  "permission.status === \"active\"",
  "error.status === 409"
];

for (const marker of requiredAppMarkers) {
  if (!app.includes(marker)) errors.push(`Permission editor is missing: ${marker}`);
}

if (!api.includes("assignments") || !api.includes("expected_revision")) {
  errors.push("Role permission PUT must send assignments and expected_revision.");
}

if (api.includes('apiRequest("/v1/policy/evaluate"')) {
  errors.push("The tenant frontend must use session/context permissions and must not call the internal policy evaluator.");
}

if (!api.includes('(session?.permissions || []).includes("admin.tenant.read")')) {
  errors.push("The Administration dashboard must derive its read indicator from session/context.");
}

if (!css.includes("container: permission-editor / inline-size") || !css.includes("@container permission-editor")) {
  errors.push("Permission editor must use a named container and container queries.");
}

if (!app.includes('admin-section admin-section-roles admin-detail-panel">${renderPermissionEditor')) {
  errors.push("Permission editor must render inside its named responsive container.");
}

for (const key of ["editRolePermissions", "searchPermissions", "selectVisible", "permissionsAdded", "permissionConflict"]) {
  if ((translations.match(new RegExp(`${key}:`, "g")) || []).length !== 2) {
    errors.push(`Translation key ${key} must exist in ES and EN.`);
  }
}

if (/data-action=["'][^"']*(template|preset)/i.test(app)) {
  errors.push("Templates and presets are forbidden in the permission editor.");
}

if (errors.length) fail("permission editor validation failed", errors);
else ok("permission editor uses an explicit draft, visible bulk actions, diff, revision guard, i18n, accessibility controls, and container queries without templates.");
