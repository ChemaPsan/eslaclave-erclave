const fs = require("fs");
const path = require("path");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const requiredFiles = [
  "docs/contexto/CONTROL_CONTABLE.md",
  "AGENTS.md",
  ".agents/skills/erclave-accounting/SKILL.md",
  ".agents/skills/erclave-module-boundaries/SKILL.md",
  "docs/arquitectura/cobertura_agentes_modulos.md",
  ".agents/skills/erclave-feature/SKILL.md",
  ".agents/skills/erclave-feature/agents/openai.yaml",
  ".agents/skills/erclave-db-migration/SKILL.md",
  ".agents/skills/erclave-db-migration/agents/openai.yaml",
  ".agents/skills/erclave-environment-boundaries/SKILL.md",
  ".agents/skills/erclave-environment-boundaries/agents/openai.yaml",
  ".agents/skills/erclave-qa-release/SKILL.md",
  ".agents/skills/erclave-qa-release/agents/openai.yaml",
  ".agents/skills/erclave-form-contract/SKILL.md",
  ".agents/skills/erclave-context-reconcile/SKILL.md",
  ".agents/skills/erclave-qa-evidence/SKILL.md",
  "tools/verify.js",
  "tools/traceability-draft.js",
  "tools/session-context.js",
  "tools/context_brief.py",
  "docs/contexto/INICIO_SESION.md"
];

for (const file of requiredFiles) {
  if (!fs.existsSync(fromRoot(file))) errors.push(`Missing Codex tooling file: ${file}`);
}

if (!errors.length) {
  const agents = readText("AGENTS.md");
  for (const token of ["AGENTES.md", "tenant_id", "npm run verify", "TRAZABILIDAD.md"]) {
    if (!agents.includes(token)) errors.push(`AGENTS.md must reference ${token}.`);
  }
  if (!agents.includes("APIs afectadas") || !agents.includes("endpoints consumidos sin cambio")) {
    errors.push("AGENTS.md must require the API impact inventory in every delivery.");
  }

  const agentCatalog = readText("AGENTES.md");
  if (!agentCatalog.includes("APIs afectadas") || !agentCatalog.includes("metodo, ruta, servicio, permiso")) {
    errors.push("AGENTES.md must require API impact reporting from transversal and technical agents.");
  }

  const traceabilityDraft = readText("tools/traceability-draft.js");
  if (!traceabilityDraft.includes("| APIs afectadas |")) {
    errors.push("Traceability drafts must include an APIs afectadas field.");
  }

  for (const name of ["erclave-feature", "erclave-db-migration", "erclave-environment-boundaries", "erclave-qa-release"]) {
    const skill = readText(path.join(".agents", "skills", name, "SKILL.md"));
    const normalizedSkill = skill.replace(/\r\n/g, "\n");
    if (!normalizedSkill.startsWith(`---\nname: ${name}\n`)) {
      errors.push(`${name}/SKILL.md has invalid frontmatter or name.`);
    }
    if (skill.includes("TODO")) errors.push(`${name}/SKILL.md still contains TODO placeholders.`);
    if (name === "erclave-feature" && (!skill.includes("APIs afectadas") || !skill.includes("metodo, ruta, servicio, permiso"))) {
      errors.push("erclave-feature/SKILL.md must require API impact reporting.");
    }

    const yaml = readText(path.join(".agents", "skills", name, "agents", "openai.yaml"));
    if (!yaml.includes(`$${name}`)) errors.push(`${name}/agents/openai.yaml must invoke $${name}.`);
    if (yaml.includes("�")) errors.push(`${name}/agents/openai.yaml contains invalid replacement characters.`);
  }

  for (const name of ["erclave-form-contract", "erclave-context-reconcile", "erclave-qa-evidence", "erclave-accounting", "erclave-module-boundaries"]) {
    const skill = readText(path.join(".agents", "skills", name, "SKILL.md")).replace(/\r\n/g, "\n");
    if (!skill.startsWith(`---\nname: ${name}\n`) || !skill.includes("description:")) {
      errors.push(`${name}/SKILL.md has invalid frontmatter or name.`);
    }
  }

  const packageJson = JSON.parse(readText("package.json"));
  for (const script of ["validate:codex-tooling", "validate:environment-boundaries", "validate:local-qa-parity", "validate:session-context", "verify", "traceability:draft", "session:context", "session:brief"]) {
    if (!packageJson.scripts?.[script]) errors.push(`package.json is missing script ${script}.`);
  }
}

if (errors.length) fail("Codex tooling validation failed", errors);
else ok("Codex instructions, project skills and workflow commands are present.");
