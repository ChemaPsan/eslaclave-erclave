const { fail, ok, readText } = require("./shared");

const agents = readText("AGENTES.md");
const errors = [];

const requiredTransversalAgents = [
  "### Arquitecto senior de plataforma SaaS",
  "### Arquitecto senior de datos y persistencia",
  "### Custodio tecnico de la base de datos ERClave",
  "### Arquitecto senior de APIs y contratos backend",
  "### Ingeniero senior de QA, validadores y release",
  "### Ingeniero senior de seguridad, IAM y supply chain",
  "### Custodio de manuales funcionales de la solucion"
];

for (const skillPath of [
  ".agents/skills/erclave-solution-manuals/SKILL.md",
  ".agents/skills/erclave-solution-manuals/agents/openai.yaml",
  ".agents/skills/erclave-solution-manuals/scripts/build_manual_docx.py",
  "docs/manuales_solucion/REGISTRO.md"
]) {
  if (!readText(skillPath).trim()) errors.push(`Missing solution manual capability: ${skillPath}`);
}

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
  "`ESTADO_ACTUAL.md` es la unica fuente para el inventario operativo mutable",
  "Tratar `hr` y `production` como dependencias efectivas de `sales`"
];

const staleAgentFragments = [
  "Vigilar compatibilidad entre frontend mock, API futura y persistencia.",
  "Detectar que falta conectar en API futura, persistencia, permisos, reportes e integraciones.",
  "Que datos mock deben convertirse en entidades reales?",
  "Documentacion de catalogos base, permisos, roles y configuracion transversal; implementacion UI pendiente.",
  "arranque canonico con Emulator aun esta pendiente",
  "schema vacio en QA, sin despliegue confirmado del servicio",
  "schema vacio en QA, servicio y entitlement aun no desplegados",
  "Reservas no son reales"
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
  "El codigo Local posterior agrega reservas/consumo para Produccion",
  "Ventas | Backend y UI Local para Clientes, Cotizaciones, Pedidos y Entregas",
  "Expedientes y capacidad autoritativa existen solo en codigo Local"
]) {
  if (!moduleIndex.includes(fragment)) {
    errors.push(`Module index is missing current state: ${fragment}`);
  }
}

const documentationChecks = [
  {
    path: "modulos/01_produccion.md",
    required: [
      "## 2. Alcance por ambiente",
      "Trabajadores activos por minutos disponibles, descontando compromisos de la fecha",
      "Una orden **Terminada** queda disponible para recepcion en Almacenes"
    ],
    forbidden: [
      "## 2. Alcance actual de la maqueta",
      "Definir consumo real de recursos",
      "Definir integracion con almacenes reales"
    ]
  },
  {
    path: "modulos/02_almacenes_inventarios.md",
    required: [
      "### Reservas por ambiente",
      "Las reservas de pedidos de Ventas estan implementadas en Local",
      "Inventory conserva ownership de reservas"
    ],
    forbidden: [
      "El submodulo Reservas queda documentado como flujo futuro",
      "Fuera del MVP funcional inicial",
      "Definir metodo de costeo inicial"
    ]
  },
  {
    path: "modulos/04_ventas_clientes.md",
    required: [
      "## Sinergia y habilitacion modular",
      "Ventas depende de `hr` y `production` efectivos",
      "la UI usa resultados parciales"
    ],
    forbidden: ["Ventas planned/mock"]
  },
  {
    path: "modulos/10_recursos_humanos.md",
    required: ["corte acumulado Local `20260818_0017`"],
    forbidden: ["La migracion `20260730_0010` y el seed de permisos deben ejecutarse primero"]
  },
  {
    path: "docs/arquitectura/ownership_datos_mvp.md",
    required: [
      "Reservas para ordenes de Produccion y Pedidos de Ventas estan implementadas en codigo Local",
      "POST /v1/inventory/reservations/{id}/consume"
    ],
    forbidden: ["Reservas quedan como contrato futuro si el MVP inicial no las ejecuta todavia"]
  },
  {
    path: "docs/arquitectura/modelo_datos_mvp.md",
    required: [
      "Es un contrato tecnico vivo",
      "se materializo para ordenes de Produccion en la revision Local `20260818_0017`"
    ],
    forbidden: ["Reserva de inventario. Puede quedar fase futura"]
  },
  {
    path: "docs/arquitectura/diagramas/estado_actual_backend_mvp.drawio",
    required: ["Local head 20260821_0023", "QA head 20260805_0013"],
    forbidden: ["Local head 20260817_0015", "Alembic head 20260817_0015", "Ventas planned/mock"]
  },
  {
    path: "docs/arquitectura/diagramas/apis_mvp_relaciones.drawio",
    required: [
      "SOLO LOCAL: reservas/consumos de Produccion, valuacion y concurrencia",
      "LOCAL: availability / reserve / release / consume; planned: finished goods"
    ],
    forbidden: ["reservas/consumos planned", "OBJETIVO: availability / consumption / receipts"]
  }
];

for (const check of documentationChecks) {
  const source = readText(check.path);
  for (const fragment of check.required) {
    if (!source.includes(fragment)) {
      errors.push(`${check.path} is missing current documentation fragment: ${fragment}`);
    }
  }
  for (const fragment of check.forbidden) {
    if (source.includes(fragment)) {
      errors.push(`${check.path} still contains stale documentation fragment: ${fragment}`);
    }
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
