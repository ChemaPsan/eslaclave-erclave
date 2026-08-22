const fs = require("fs");
const path = require("path");
const { fail, fromRoot, listFiles, ok, readText } = require("./shared");

const errors = [];

const livingDocuments = [
  "AGENTS.md",
  "AGENTES.md",
  "TRAZABILIDAD.md",
  "docs/arquitectura/gobierno_documentacion_viva.md",
  "docs/arquitectura/modelo_datos_mvp.md",
  "docs/arquitectura/ownership_datos_mvp.md",
  "docs/arquitectura/apis_mvp.md",
  "docs/arquitectura/fronteras_ambientes_local_qa_produccion.md",
  "docs/arquitectura/diagramas/estado_actual_backend_mvp.drawio",
  "docs/contexto/INICIO_SESION.md",
  "docs/contexto/ESTADO_ACTUAL.md",
  "docs/contexto/DECISIONES.md",
  "docs/contexto/PENDIENTES.md",
  "docs/contexto/TENANTS.md",
  "modulos/README.md"
];

for (const relativePath of livingDocuments) {
  if (!fs.existsSync(fromRoot(relativePath))) {
    errors.push(`Missing living documentation source: ${relativePath}`);
  }
}

const migrationFiles = listFiles("backend/alembic/versions", (file) => file.endsWith(".py"));
const revisions = new Map();
const referencedParents = new Set();

for (const relativePath of migrationFiles) {
  const source = readText(relativePath);
  const revision = source.match(/^revision(?:\s*:[^=]+)?\s*=\s*["']([^"']+)["']/m)?.[1];
  const parentMatch = source.match(/^down_revision(?:\s*:[^=]+)?\s*=\s*(?:["']([^"']+)["']|None)/m);
  if (!revision) {
    errors.push(`Migration does not declare a parseable revision: ${relativePath}`);
    continue;
  }
  if (revisions.has(revision)) {
    errors.push(`Duplicate Alembic revision ${revision}: ${relativePath} and ${revisions.get(revision)}`);
  }
  revisions.set(revision, relativePath);
  if (parentMatch?.[1]) referencedParents.add(parentMatch[1]);
}

const migrationHeads = [...revisions.keys()].filter((revision) => !referencedParents.has(revision));
if (migrationHeads.length !== 1) {
  errors.push(`Expected exactly one Alembic head, found: ${migrationHeads.join(", ") || "none"}`);
}

const localHead = migrationHeads[0];
const currentState = readText("docs/contexto/ESTADO_ACTUAL.md");
const backendDiagram = readText("docs/arquitectura/diagramas/estado_actual_backend_mvp.drawio");
if (localHead) {
  if (!currentState.includes(`\`${localHead}\``)) {
    errors.push(`ESTADO_ACTUAL.md does not mention the repository Alembic head ${localHead}.`);
  }
  if (!backendDiagram.includes(`Local head ${localHead}`)) {
    errors.push(`Backend state diagram does not declare Local head ${localHead}.`);
  }
}

const environmentBoundaries = readText("docs/arquitectura/fronteras_ambientes_local_qa_produccion.md");
const qaHead = currentState.match(/QA permanece en `([^`]+)`/)?.[1];
if (!qaHead) {
  errors.push("ESTADO_ACTUAL.md must declare the current QA Alembic revision with 'QA permanece en'.");
} else {
  if (!environmentBoundaries.includes(`Revision documentada \`${qaHead}\``)) {
    errors.push(`Environment boundaries do not match QA revision ${qaHead}.`);
  }
  if (!backendDiagram.includes(`QA head ${qaHead}`)) {
    errors.push(`Backend state diagram does not declare QA head ${qaHead}.`);
  }
}

const traceability = readText("TRAZABILIDAD.md");
const changeIds = [...traceability.matchAll(/^### CHG-(\d{3})$/gm)].map((match) => Number(match[1]));
const latestChange = changeIds.at(-1);
if (!latestChange) {
  errors.push("TRAZABILIDAD.md does not contain CHG entries.");
} else {
  const latestHeading = `### CHG-${String(latestChange).padStart(3, "0")}`;
  const start = traceability.lastIndexOf(latestHeading);
  const convention = traceability.indexOf("\n## Convencion para futuros cambios", start);
  const latestEntry = traceability.slice(start, convention < 0 ? undefined : convention);
  for (const field of ["Fecha", "Cambio", "Archivos", "Agentes consultados", "APIs afectadas", "Validacion", "Observaciones"]) {
    if (!latestEntry.includes(`| ${field} |`)) {
      errors.push(`${latestHeading} is missing required field: ${field}`);
    }
  }
  if (!currentState.includes(`CHG-${String(latestChange).padStart(3, "0")}`)) {
    errors.push(`ESTADO_ACTUAL.md does not reference the latest traceability entry ${latestHeading.replace("### ", "")}.`);
  }
}

const moduleIndex = readText("modulos/README.md");
const moduleDocuments = listFiles("modulos", (file) => /[\\/]\d{2}_[^\\/]+\.md$/.test(file));
for (const relativePath of moduleDocuments) {
  const filename = path.basename(relativePath);
  if (!moduleIndex.includes(`](${filename})`)) {
    errors.push(`modulos/README.md does not index ${filename}.`);
  }
}

const markdownFiles = [
  "README.md",
  "AGENTS.md",
  "AGENTES.md",
  "TRAZABILIDAD.md",
  ...listFiles("docs", (file) => file.endsWith(".md")),
  ...listFiles("modulos", (file) => file.endsWith(".md")),
  ...listFiles("contracts", (file) => file.endsWith(".md"))
];

for (const relativePath of markdownFiles) {
  const source = readText(relativePath);
  const links = [...source.matchAll(/\[[^\]]+\]\(([^)\n]+)\)/g)].map((match) => match[1].trim());
  for (let target of links) {
    if (/^(https?:\/\/|mailto:|#|app:\/\/|data:|\/v1\/|[A-Za-z]:\\)/.test(target)) continue;
    target = target.replace(/^<|>$/g, "").split("#")[0].trim();
    if (!target) continue;
    try {
      target = decodeURIComponent(target);
    } catch {
      errors.push(`${relativePath} contains an invalid encoded link: ${target}`);
      continue;
    }
    const resolved = path.resolve(path.dirname(fromRoot(relativePath)), target);
    if (!fs.existsSync(resolved)) {
      errors.push(`${relativePath} contains a broken local link: ${target}`);
    }
  }
}

const governanceReferences = [
  ["AGENTS.md", ["gobierno_documentacion_viva.md", "validate:documentation"]],
  ["AGENTES.md", ["documentacion viva", "validate:documentation"]],
  ["docs/contexto/INICIO_SESION.md", ["gobierno_documentacion_viva.md", "validate:documentation"]],
  ["docs/contexto/DECISIONES.md", ["gobierno_documentacion_viva.md"]]
];

for (const [relativePath, fragments] of governanceReferences) {
  const source = readText(relativePath);
  for (const fragment of fragments) {
    if (!source.includes(fragment)) {
      errors.push(`${relativePath} does not reference documentation governance fragment: ${fragment}`);
    }
  }
}

const packageJson = JSON.parse(readText("package.json"));
if (packageJson.scripts?.["validate:documentation"] !== "node tools/validators/validate-documentation-freshness.js") {
  errors.push("package.json must expose validate:documentation.");
}
if (!readText("tools/validators/validate-all.js").includes('"validate-documentation-freshness.js"')) {
  errors.push("validate-all.js must run validate-documentation-freshness.js.");
}

if (errors.length) {
  fail("documentation freshness validation failed", errors);
} else {
  ok(`living documentation is coherent with Alembic ${localHead}, QA ${qaHead}, and CHG-${String(latestChange).padStart(3, "0")}.`);
}
