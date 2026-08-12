const fs = require("fs");
const { fail, fromRoot, ok, readText } = require("./shared");

const errors = [];
const requiredFiles = [
  "docs/arquitectura/fronteras_ambientes_local_qa_produccion.md",
  ".agents/skills/erclave-environment-boundaries/SKILL.md",
  ".agents/skills/erclave-environment-boundaries/agents/openai.yaml"
];

for (const file of requiredFiles) {
  if (!fs.existsSync(fromRoot(file))) errors.push(`Missing environment boundary file: ${file}`);
}

if (!errors.length) {
  const boundaries = readText(requiredFiles[0]);
  for (const token of [
    "Firebase Emulator",
    "local conectado a QA",
    "RPO",
    "15 minutos",
    "RTO",
    "2 horas",
    "Almacenes e Inventario",
    "Recursos Humanos",
    "Ventas"
  ]) {
    if (!boundaries.includes(token)) errors.push(`Environment boundaries must include: ${token}`);
  }

  const agents = readText("AGENTS.md");
  for (const token of ["$erclave-environment-boundaries", "Firebase Emulator", "Local conectado a QA"]) {
    if (!agents.includes(token)) errors.push(`AGENTS.md must include: ${token}`);
  }

  const skill = readText(requiredFiles[1]);
  if (!skill.startsWith("---\nname: erclave-environment-boundaries\n")) {
    errors.push("Environment boundary skill has invalid frontmatter or name.");
  }
  if (skill.includes("TODO")) errors.push("Environment boundary skill contains TODO placeholders.");

  const yaml = readText(requiredFiles[2]);
  if (!yaml.includes("$erclave-environment-boundaries")) {
    errors.push("Environment boundary skill UI metadata must invoke the skill.");
  }

  const firebaseConfig = JSON.parse(readText("firebase.json"));
  if (firebaseConfig.emulators?.auth?.host !== "127.0.0.1" || firebaseConfig.emulators?.auth?.port !== 9099) {
    errors.push("firebase.json must bind Auth Emulator to 127.0.0.1:9099.");
  }

  const frontendConfig = readText("frontend/api/config.js");
  const frontendAuth = readText("frontend/auth.js");
  const frontendEnv = readText("frontend/env.js");
  const backofficeEnv = readText("frontend/backoffice/env.js");
  for (const [file, content] of [
    ["frontend/env.js", frontendEnv],
    ["frontend/backoffice/env.js", backofficeEnv]
  ]) {
    for (const token of ["firebase-emulator", "demo-erclave", "http://127.0.0.1:9099"]) {
      if (!content.includes(token)) errors.push(`${file} must include local emulator token: ${token}`);
    }
  }
  if (!frontendConfig.includes("getFirebaseAuthEmulatorUrl")) {
    errors.push("Frontend config must expose the Firebase Auth Emulator URL.");
  }
  if (!frontendAuth.includes("connectAuthEmulator")) {
    errors.push("Frontend auth must connect to Firebase Auth Emulator in Local.");
  }

  const localScript = readText("backend/scripts/start_local.ps1");
  for (const token of ["FIREBASE_AUTH_EMULATOR_HOST", "demo-erclave", "erclave_local", "127.0.0.1:8000"]) {
    if (!localScript.includes(token)) errors.push(`Canonical local startup must include: ${token}`);
  }
}

if (errors.length) fail("Environment boundary validation failed", errors);
else ok("Local, QA and Production boundaries are documented and protected.");
