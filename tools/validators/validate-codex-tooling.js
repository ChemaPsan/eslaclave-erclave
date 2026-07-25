const fs = require("fs");
const path = require("path");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const requiredFiles = [
  "AGENTS.md",
  ".agents/skills/erclave-feature/SKILL.md",
  ".agents/skills/erclave-feature/agents/openai.yaml",
  ".agents/skills/erclave-db-migration/SKILL.md",
  ".agents/skills/erclave-db-migration/agents/openai.yaml",
  "tools/verify.js",
  "tools/traceability-draft.js"
];

for (const file of requiredFiles) {
  if (!fs.existsSync(fromRoot(file))) errors.push(`Missing Codex tooling file: ${file}`);
}

if (!errors.length) {
  const agents = readText("AGENTS.md");
  for (const token of ["AGENTES.md", "tenant_id", "npm run verify", "TRAZABILIDAD.md"]) {
    if (!agents.includes(token)) errors.push(`AGENTS.md must reference ${token}.`);
  }

  for (const name of ["erclave-feature", "erclave-db-migration"]) {
    const skill = readText(path.join(".agents", "skills", name, "SKILL.md"));
    if (!skill.startsWith(`---\nname: ${name}\n`)) {
      errors.push(`${name}/SKILL.md has invalid frontmatter or name.`);
    }
    if (skill.includes("TODO")) errors.push(`${name}/SKILL.md still contains TODO placeholders.`);

    const yaml = readText(path.join(".agents", "skills", name, "agents", "openai.yaml"));
    if (!yaml.includes(`$${name}`)) errors.push(`${name}/agents/openai.yaml must invoke $${name}.`);
  }

  const packageJson = JSON.parse(readText("package.json"));
  for (const script of ["validate:codex-tooling", "verify", "traceability:draft"]) {
    if (!packageJson.scripts?.[script]) errors.push(`package.json is missing script ${script}.`);
  }
}

if (errors.length) fail("Codex tooling validation failed", errors);
else ok("Codex instructions, project skills and workflow commands are present.");
