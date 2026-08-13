const { fail, ok, readText } = require("./shared");

const agents = readText("AGENTES.md");
const errors = [];

const requiredTransversalAgents = [
  "### Arquitecto senior de plataforma SaaS",
  "### Arquitecto senior de datos y persistencia",
  "### Custodio tecnico de la base de datos ERClave",
  "### Arquitecto senior de APIs y contratos backend",
  "### Ingeniero senior de QA, validadores y release",
  "### Ingeniero senior de seguridad, IAM y supply chain"
];

const requiredModules = [
  "Sinergia modular",
  "Diseno, experiencia y localizacion",
  "Produccion",
  "Recursos Humanos",
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

const requiredCurrentStateFragments = [
  "### Estado operativo vigente",
  "local conectado a QA",
  "Firebase Emulator",
  "`ESTADO_ACTUAL.md` es la unica fuente para el inventario operativo mutable"
];

const staleAgentFragments = [
  "Vigilar compatibilidad entre frontend mock, API futura y persistencia.",
  "Detectar que falta conectar en API futura, persistencia, permisos, reportes e integraciones.",
  "Que datos mock deben convertirse en entidades reales?",
  "Documentacion de catalogos base, permisos, roles y configuracion transversal; implementacion UI pendiente.",
  "arranque canonico con Emulator aun esta pendiente",
  "schema vacio en QA, sin despliegue confirmado del servicio",
  "schema vacio en QA, servicio y entitlement aun no desplegados"
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

for (const fragment of requiredCurrentStateFragments) {
  if (!agents.includes(fragment)) {
    errors.push(`Agents are missing current operational state: ${fragment}`);
  }
}

for (const fragment of staleAgentFragments) {
  if (agents.includes(fragment)) {
    errors.push(`Agents still contain stale guidance: ${fragment}`);
  }
}

const moduleIndex = readText("modulos/README.md");
for (const fragment of [
  "UI y `admin-service` reales en QA",
  "Inventory y RH reales en QA",
  "Reservas permanece fuera del alcance"
]) {
  if (!moduleIndex.includes(fragment)) {
    errors.push(`Module index is missing current state: ${fragment}`);
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
