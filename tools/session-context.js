const fs = require("fs");
const net = require("net");
const path = require("path");
const { spawnSync } = require("child_process");

const repoRoot = path.resolve(__dirname, "..");
const contextFiles = [
  "docs/contexto/ESTADO_ACTUAL.md",
  "docs/contexto/DECISIONES.md",
  "docs/contexto/TENANTS.md",
  "docs/contexto/PENDIENTES.md"
];

function read(relativePath) {
  return fs.readFileSync(path.join(repoRoot, relativePath), "utf8").trim();
}

function git(...args) {
  const result = spawnSync("git", ["-c", `safe.directory=${repoRoot}`, ...args], {
    cwd: repoRoot,
    encoding: "utf8",
    shell: false
  });
  if (result.status !== 0) return `[no disponible: ${(result.stderr || "error Git").trim()}]`;
  return result.stdout.trim();
}

function latestTraceability() {
  const source = read("TRAZABILIDAD.md");
  const matches = [...source.matchAll(/^### CHG-\d{3}$/gm)];
  if (!matches.length) return "Sin entradas CHG.";
  const start = matches.at(-1).index;
  const nextHeading = source.indexOf("\n## ", start);
  return source.slice(start, nextHeading < 0 ? undefined : nextHeading).trim();
}

function latestMigration() {
  const directory = path.join(repoRoot, "backend", "alembic", "versions");
  if (!fs.existsSync(directory)) return "Sin directorio de migraciones.";
  const files = fs.readdirSync(directory).filter((file) => file.endsWith(".py")).sort();
  return files.at(-1) || "Sin migraciones.";
}

function probe(name, port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port });
    const finish = (status) => {
      socket.destroy();
      resolve(`${name.padEnd(18)} 127.0.0.1:${port} ${status}`);
    };
    socket.setTimeout(500);
    socket.once("connect", () => finish("ACTIVO"));
    socket.once("timeout", () => finish("APAGADO"));
    socket.once("error", () => finish("APAGADO"));
  });
}

function section(title, value) {
  process.stdout.write(`\n=== ${title} ===\n${value}\n`);
}

async function main() {
  const missing = ["AGENTS.md", "AGENTES.md", "TRAZABILIDAD.md", ...contextFiles]
    .filter((file) => !fs.existsSync(path.join(repoRoot, file)));
  if (missing.length) {
    console.error(`[FAIL] Memoria operativa incompleta:\n- ${missing.join("\n- ")}`);
    process.exit(1);
  }

  console.log("ERClave - recuperacion de contexto (solo lectura, sin secretos)");
  console.log(`Fecha local: ${new Intl.DateTimeFormat("es-MX", { dateStyle: "full", timeStyle: "medium", timeZone: "America/Mexico_City" }).format(new Date())}`);
  section("RAMA", git("branch", "--show-current") || "detached");
  section("CAMBIOS LOCALES", git("status", "--short") || "Arbol de trabajo limpio.");
  section("ULTIMA MIGRACION EN REPOSITORIO", latestMigration());
  section("ULTIMA TRAZABILIDAD", latestTraceability());

  for (const file of contextFiles) section(file, read(file));

  const services = await Promise.all([
    probe("Frontend", 4173),
    probe("Admin API", 8010),
    probe("Production API", 8002),
    probe("Inventory API", 8004),
    probe("PostgreSQL local", 5434)
  ]);
  section("SERVICIOS LOCALES", services.join("\n"));
  section("CHECKLIST PARA EL AGENTE", read("docs/contexto/INICIO_SESION.md"));
  console.log("\n[OK] Contexto recuperado. Lee AGENTS.md, AGENTES.md y el documento del modulo antes de modificar.");
}

main().catch((error) => {
  console.error(`[FAIL] No se pudo recuperar contexto: ${error.message}`);
  process.exit(1);
});
