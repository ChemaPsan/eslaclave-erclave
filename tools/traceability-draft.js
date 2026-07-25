const fs = require("fs");
const { spawnSync } = require("child_process");
const { fromRoot, readText } = require("./validators/shared");

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

const title = argument("--title");
const shouldWrite = process.argv.includes("--write");

if (!title || title.startsWith("--")) {
  console.error('Uso: npm run traceability:draft -- --title "Título" [--write]');
  process.exit(1);
}

const traceability = readText("TRAZABILIDAD.md");
const ids = [...traceability.matchAll(/^### CHG-(\d{3})$/gm)].map((match) => Number(match[1]));
const nextId = String((ids.at(-1) || 0) + 1).padStart(3, "0");
const git = spawnSync(
  "git",
  ["status", "--short"],
  { cwd: fromRoot(), encoding: "utf8", shell: false }
);

if (git.status !== 0) {
  console.error(git.stderr || "No se pudo leer git status.");
  process.exit(git.status || 1);
}

const files = git.stdout
  .split(/\r?\n/)
  .filter(Boolean)
  .map((line) => line.slice(3).trim())
  .filter((file) => file !== "TRAZABILIDAD.md")
  .map((file) => `\`${file}\``);

const date = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/Mexico_City",
  year: "numeric",
  month: "2-digit",
  day: "2-digit"
}).format(new Date());

const draft = `### CHG-${nextId}

| Campo | Contenido |
|---|---|
| Fecha | ${date} |
| Cambio | ${title.replace(/\|/g, "\\|")} |
| Autor | Codex |
| Archivos | ${files.join(", ") || "Por completar"} |
| Secciones | Por completar |
| Descripcion | Por completar con el comportamiento implementado. |
| Motivo | Por completar con el problema resuelto. |
| Impacto | Por completar con consumidores, compatibilidad y riesgos. |
| Validacion | \`npm.cmd run verify\`. |
| Observaciones | Por completar con pendientes reales o indicar que no hay pendientes conocidos. |
`;

if (!shouldWrite) {
  process.stdout.write(`${draft}\n`);
  process.exit(0);
}

const convention = "## Convencion para futuros cambios";
const position = traceability.indexOf(convention);
if (position < 0) {
  console.error(`No se encontró "${convention}" en TRAZABILIDAD.md.`);
  process.exit(1);
}

const updated = `${traceability.slice(0, position).trimEnd()}\n\n${draft}\n${traceability.slice(position)}`;
fs.writeFileSync(fromRoot("TRAZABILIDAD.md"), updated, "utf8");
console.log(`[OK] Se agregó el borrador CHG-${nextId}; completa sus campos antes de verificar.`);
