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
if (mainStyles.includes(".flow-guide-card[open] .flow-guide-steps")) {
  errors.push("frontend/styles.css: open flow guides must keep the standard vertical rail; scope layout exceptions to an explicit screen class.");
}
if (!mainStyles.includes("grid-template-columns: minmax(220px, 280px) minmax(0, 1fr)")) {
  errors.push("frontend/styles.css: missing the standard vertical flow rail layout.");
}

if (errors.length) {
  fail("responsive UI validation failed", errors);
} else {
  ok("responsive containers, accessibility hooks and agent documentation are present.");
}
