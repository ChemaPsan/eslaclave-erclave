const { fail, ok, readText } = require("./shared");

const traceability = readText("TRAZABILIDAD.md");
const readme = readText("README.md");
const errors = [];

const matches = [...traceability.matchAll(/^### CHG-(\d{3})$/gm)].map((match) => Number(match[1]));

if (!matches.length) {
  errors.push("No CHG entries found in TRAZABILIDAD.md.");
}

for (let index = 1; index < matches.length; index += 1) {
  const previous = matches[index - 1];
  const current = matches[index];
  if (current !== previous + 1) {
    errors.push(`Traceability IDs are not sequential: CHG-${String(previous).padStart(3, "0")} -> CHG-${String(current).padStart(3, "0")}`);
  }
}

const requiredReadmeRefs = [
  "AGENTES.md",
  "docs/arquitectura/microservicios_microfrontends.md",
  "TRAZABILIDAD.md"
];

for (const ref of requiredReadmeRefs) {
  if (!readme.includes(ref)) errors.push(`README.md does not reference ${ref}.`);
}

const latest = matches[matches.length - 1];
const latestHeading = latest ? `### CHG-${String(latest).padStart(3, "0")}` : "";
const latestStart = latestHeading ? traceability.lastIndexOf(latestHeading) : -1;
const latestEntry = latestStart >= 0 ? traceability.slice(latestStart, traceability.indexOf("\n## ", latestStart) < 0 ? undefined : traceability.indexOf("\n## ", latestStart)) : "";
if (latestEntry && !latestEntry.includes("| Agentes consultados |")) {
  errors.push(`${latestHeading} must record Agentes consultados.`);
}
if (latest && !traceability.includes("## Convencion para futuros cambios")) {
  errors.push("TRAZABILIDAD.md is missing the future changes convention section.");
}

if (errors.length) {
  fail("traceability validation failed", errors);
} else {
  ok(`traceability entries are sequential through CHG-${String(latest).padStart(3, "0")}.`);
}
