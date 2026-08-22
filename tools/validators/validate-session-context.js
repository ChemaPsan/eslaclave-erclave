const fs = require("fs");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const required = [
  "docs/contexto/INICIO_SESION.md",
  "docs/contexto/ESTADO_ACTUAL.md",
  "docs/contexto/DECISIONES.md",
  "docs/contexto/TENANTS.md",
  "docs/contexto/PENDIENTES.md",
  "docs/arquitectura/gobierno_documentacion_viva.md",
  "tools/session-context.js"
];

for (const file of required) {
  if (!fs.existsSync(fromRoot(file))) errors.push(`Missing session context file: ${file}`);
}

if (!errors.length) {
  const tenants = readText("docs/contexto/TENANTS.md");
  if (!tenants.includes("ten_739ee59d765d5e14818674800d")) errors.push("TENANTS.md must name the authorized demo tenant ID.");
  for (const token of ["QA", "Produccion", "autorizacion explicita"]) {
    if (!tenants.includes(token)) errors.push(`TENANTS.md must preserve guardrail: ${token}.`);
  }

  const startup = readText("docs/contexto/INICIO_SESION.md");
  for (const token of ["session:context", "AGENTS.md", "AGENTES.md", "git status", "Agentes consultados", "run verify", "TRAZABILIDAD.md", "gobierno_documentacion_viva.md", "validate:documentation"]) {
    if (!startup.includes(token)) errors.push(`INICIO_SESION.md must reference ${token}.`);
  }

  const packageJson = JSON.parse(readText("package.json"));
  if (!packageJson.scripts?.["session:context"]) errors.push("package.json is missing script session:context.");
  if (!packageJson.scripts?.["validate:documentation"]) errors.push("package.json is missing script validate:documentation.");
  const contextScript = readText("tools/session-context.js");
  if (!contextScript.includes('probe("Sales API", 8008)')) errors.push("session:context must report the Local Sales API.");
}

if (errors.length) fail("Session context validation failed", errors);
else ok("Persistent session context, tenant guardrails, and bootstrap command are present.");
