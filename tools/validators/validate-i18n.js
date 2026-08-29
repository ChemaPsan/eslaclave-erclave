const vm = require("vm");
const { fail, ok, readText, unique } = require("./shared");

function loadTranslations() {
  const source = readText("frontend/i18n/translations.js");
  const transformed = `${source.replace("export const translations =", "const translations =")}\ntranslations;`;
  return vm.runInNewContext(transformed, {}, { filename: "frontend/i18n/translations.js" });
}

function placeholders(value) {
  if (typeof value !== "string") return [];
  return unique([...value.matchAll(/\{([a-zA-Z0-9_]+)\}/g)].map((match) => match[1])).sort();
}

function sameList(a, b) {
  return a.length === b.length && a.every((item, index) => item === b[index]);
}

const translations = loadTranslations();
const errors = [];

if (!translations.es) errors.push("Missing translations.es.");
if (!translations.en) errors.push("Missing translations.en.");

if (!errors.length) {
  const esKeys = Object.keys(translations.es).sort();
  const enKeys = Object.keys(translations.en).sort();

  for (const key of esKeys) {
    if (!(key in translations.en)) errors.push(`Missing English key: ${key}`);
  }

  for (const key of enKeys) {
    if (!(key in translations.es)) errors.push(`Missing Spanish key: ${key}`);
  }

  for (const key of esKeys.filter((key) => key in translations.en)) {
    const esVars = placeholders(translations.es[key]);
    const enVars = placeholders(translations.en[key]);
    if (!sameList(esVars, enVars)) {
      errors.push(`Placeholder mismatch for ${key}: es {${esVars.join(", ")}} vs en {${enVars.join(", ")}}`);
    }
  }
}

const shellMarkup = readText("frontend/index.html");
for (const token of [
  'data-i18n="skipToMain"',
  'data-i18n-aria-label="mainNavigation"',
  'data-i18n-aria-label="changeTheme"',
  'data-i18n-aria-label="changeLanguage"',
  'data-i18n-aria-label="administration"',
  'data-i18n-aria-label="mainIndicators"',
  'data-i18n="userLabel"',
  'data-i18n="branchLabel"'
]) {
  if (!shellMarkup.includes(token)) errors.push(`Shell localization guardrail missing ${token}.`);
}
const appSource = readText("frontend/app.js");
for (const token of ['authButton.textContent = t("signOut")', 't("signOutUser", { email: state.auth.user.email })', 'document.documentElement.lang = state.lang', 'active: { es: "Activo", en: "Active" }', 'terminated: { es: "Baja", en: "Terminated" }', 't("submodulesOf", { module: moduleLabel })', 't("activeOrdersInFlow", { count: activeOrders })', 'renderFlowGuide(t("laborConfigurationFlow")', 't("laborAreaSummary", { positions: areaRoles.length', '${translateStatus(area.status)}', '${translateStatus(role.status)}']) {
  if (!appSource.includes(token)) errors.push(`Runtime localization guardrail missing ${token}.`);
}
const laborScreen = appSource.slice(appSource.indexOf("function renderLaborRolesScreen"), appSource.indexOf("function renderWorkersScreen"));
if (appSource.includes("Submodulos de ${module.title}")) errors.push("Visible shell copy must not bypass i18n: submodule navigation label.");
for (const forbidden of ['"Flujo de configuracion de mano de obra"', '>Area operativa<', '${area.status}</span>', '${role.status}</span>']) {
  if (laborScreen.includes(forbidden)) errors.push(`Visible RH copy must not bypass i18n: ${forbidden}.`);
}

if (errors.length) {
  fail("i18n validation failed", errors);
} else {
  ok("i18n keys and placeholders match for es/en.");
}
