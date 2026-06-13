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

if (errors.length) {
  fail("i18n validation failed", errors);
} else {
  ok("i18n keys and placeholders match for es/en.");
}
