const vm = require("vm");
const { fail, ok, readText } = require("./shared");
const errors = [];
const bindings = readText("frontend/features/form-bindings.js");
const coverage = vm.runInNewContext(bindings.replace(/export /g, "") + ";FORM_BINDING_COVERAGE;");
for (const filename of ["frontend/app.js", "frontend/backoffice/app.js"]) {
  const source = readText(filename);
  if (!source.includes("installFormFeedback({")) errors.push(`${filename}: missing shared form feedback installation.`);
  for (const match of source.matchAll(/<form\b([^>]+)>/g)) {
    const attributes = match[1];
    const id = attributes.match(/\b(?:id|data-form)=["']([^"']+)["']/)?.[1];
    if (id && !id.includes("${") && !coverage.includes(id)) errors.push(`${filename}: unreviewed form ${id}; add explicit request bindings and behavioral coverage.`);
    if (!id && !attributes.includes("operational-handoff-dialog")) errors.push(`${filename}: anonymous form must declare a stable ID/data-form for error ownership.`);
  }
  if (/renderFormErrors\(\[userFacingError\(/.test(source)) errors.push(`${filename}: form errors must retain the structured API error.`);
}
const catalog = vm.runInNewContext(readText("frontend/i18n/form-business-errors.js").replace(/export /g, "") + ";({messages: FORM_BUSINESS_ERRORS, rules: VALIDATION_RULES});");
const allMessages = vm.runInNewContext(readText("frontend/i18n/api-errors.js").replace(/^import .*;$/m, "").replace(/export /g, "") + ";API_ERROR_MESSAGES;", { FORM_BUSINESS_ERRORS: catalog.messages });
for (const [code, message] of Object.entries(allMessages)) {
  if (!message.es?.trim() || !message.en?.trim()) errors.push(`Error ${code}: missing ES/EN copy.`);
  const placeholders = value => [...value.matchAll(/\{([^}]+)\}/g)].map(match => match[1]).sort().join(",");
  if (message.es && message.en && placeholders(message.es) !== placeholders(message.en)) errors.push(`Error ${code}: mismatched ES/EN placeholders.`);
}
for (const [literal, rule] of Object.entries(catalog.rules)) {
  if (!Object.hasOwn(allMessages, rule.code)) errors.push(`Validation rule ${literal}: missing translated stable code ${rule.code}.`);
  if (!Array.isArray(rule.fields)) errors.push(`Validation rule ${literal}: explicit field list required.`);
}
const helper = readText("frontend/features/form-feedback.js");
for (const token of ["aria-invalid", "aria-describedby", "textContent", "captureFormBindings", "FORM_ERROR_EVENT", "renderFormFeedback", 'addEventListener("invalid"']) {
  if (!helper.includes(token)) errors.push(`Shared feedback missing ${token}.`);
}
const client = readText("frontend/api/client.js");
for (const token of ["erclave:form-request", "erclave:form-error", "error.formContext = formRequest.context"]) if(!client.includes(token)) errors.push(`API client missing ${token}.`);
if (/campos marcados|marked fields/.test(readText("frontend/i18n/api-errors.js"))) errors.push("Generic API copy cannot promise marked fields.");
if (!readText("AGENTS.md").includes("erclave-form-feedback")) errors.push("Project instructions must require the form-feedback skill.");
if (!readText(".agents/skills/erclave-form-feedback/SKILL.md").includes("aria-invalid")) errors.push("Form skill must cover accessible field errors.");
if (!readText("frontend/features/form-feedback.css").includes("[hidden]")) errors.push("Shared CSS must preserve hidden fields.");
for (const filename of ["frontend/index.html", "frontend/backoffice/index.html"]) if (!readText(filename).includes("form-feedback.css")) errors.push(`${filename}: missing shared error styles.`);
if(errors.length)fail("Form feedback guardrails failed",errors);
else ok(`Form feedback wiring and ${coverage.length} registered form variants validated; behavioral tests run separately.`);
