const { fail, ok, readText } = require("./shared");

const agents = readText("AGENTES.md");
const errors = [];

const requiredTransversalAgents = [
  "### Arquitecto senior de plataforma SaaS",
  "### Arquitecto senior de datos y persistencia",
  "### Custodio tecnico de la base de datos ERClave",
  "### Arquitecto senior de APIs y contratos backend",
  "### Ingeniero senior de QA, validadores y release"
];

const requiredModules = [
  "Sinergia modular",
  "Diseno, experiencia y localizacion",
  "Produccion",
  "Almacenes e inventarios",
  "Compras y abastecimiento",
  "Ventas y clientes",
  "Gastos y cuentas por pagar",
  "Costos y centros de costos",
  "Reportes e inteligencia operativa",
  "Administracion y configuracion",
  "Contabilidad"
];

const requiredCustodianFragments = [
  "migraciones Alembic",
  "drift entre documentacion, modelos, migraciones y base QA/Prod",
  "validadores automatizados para revisar schema, migraciones, ownership, seeds e indices",
  "bloquear FK cruzadas entre schemas de servicios distintos",
  "validar que seeds sean idempotentes"
];

for (const heading of requiredTransversalAgents) {
  if (!agents.includes(heading)) {
    errors.push(`Missing transversal agent heading: ${heading}`);
  }
}

if (!agents.includes("## Matriz general")) {
  errors.push("AGENTES.md is missing the general module matrix.");
}

for (const moduleName of requiredModules) {
  const escapedName = moduleName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matrixRow = new RegExp(`\\| ${escapedName} \\| [^|]+ \\| [^|]+ \\|`);
  if (!matrixRow.test(agents)) {
    errors.push(`Missing module in matrix with business and technical agents: ${moduleName}`);
  }

  const moduleHeading = `### ${moduleName}`;
  if (!agents.includes(moduleHeading)) {
    errors.push(`Missing detailed module section: ${moduleHeading}`);
  }
}

for (const fragment of requiredCustodianFragments) {
  if (!agents.includes(fragment)) {
    errors.push(`Database custodian agent missing required fragment: ${fragment}`);
  }
}

const businessAgentCount = (agents.match(/^#### Agente de negocio:/gm) || []).length;
const technicalAgentCount = (agents.match(/^#### Agente tecnico:/gm) || []).length;
if (businessAgentCount < requiredModules.length) {
  errors.push(`Expected at least ${requiredModules.length} business agent detail sections, found ${businessAgentCount}.`);
}
if (technicalAgentCount < requiredModules.length) {
  errors.push(`Expected at least ${requiredModules.length} technical agent detail sections, found ${technicalAgentCount}.`);
}

if (errors.length) {
  fail("agent validation failed", errors);
} else {
  ok("transversal and module agents are present and current.");
}
