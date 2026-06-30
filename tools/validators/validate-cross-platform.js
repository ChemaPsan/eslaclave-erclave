const fs = require("fs");
const path = require("path");
const { fail, fromRoot, listFiles, ok, readText } = require("./shared");

const errors = [];

const packageJson = JSON.parse(readText("package.json"));
for (const [scriptName, command] of Object.entries(packageJson.scripts || {})) {
  if (command.includes("npm.cmd") || command.includes("powershell") || command.includes(".ps1")) {
    errors.push(`package.json script ${scriptName} uses a Windows-specific command: ${command}`);
  }
}

const validatorFiles = listFiles(
  "tools/validators",
  (file) => file.endsWith(".js") && path.basename(file) !== "validate-cross-platform.js"
);
for (const relativePath of validatorFiles) {
  const content = readText(relativePath);
  const blockedFragments = [
    "npm.cmd run",
    "powershell.exe",
    "Start-Process",
    "Get-NetTCPConnection",
    "Read-Host",
    "Activate.ps1"
  ];
  for (const fragment of blockedFragments) {
    if (content.toLowerCase().includes(fragment.toLowerCase())) {
      errors.push(`${relativePath} contains platform-specific fragment: ${fragment}`);
    }
  }
}

const backendScriptFiles = listFiles("backend/scripts", (file) => file.endsWith(".py"));
for (const relativePath of backendScriptFiles) {
  const content = readText(relativePath);
  const blockedFragments = [
    "powershell.exe",
    "cmd.exe",
    "Start-Process",
    "Get-NetTCPConnection",
    "Read-Host",
    "Activate.ps1"
  ];
  for (const fragment of blockedFragments) {
    if (content.toLowerCase().includes(fragment.toLowerCase())) {
      errors.push(`${relativePath} contains platform-specific fragment: ${fragment}`);
    }
  }
}

const operationalGuide = readText("docs/operaciones/cloud_sql_postgres_qa.md");
const requiredGuideFragments = [
  "Windows",
  "Linux",
  "macOS",
  "cloud-sql-proxy.linux.amd64",
  "cloud-sql-proxy.darwin.amd64",
  "cloud-sql-proxy.darwin.arm64",
  "cloud-sql-proxy.x64.exe",
  "source .venv/bin/activate",
  ".\\.venv\\Scripts\\Activate.ps1"
];

for (const fragment of requiredGuideFragments) {
  if (!operationalGuide.includes(fragment)) {
    errors.push(`docs/operaciones/cloud_sql_postgres_qa.md missing cross-platform fragment: ${fragment}`);
  }
}

const workflowPath = fromRoot(".github", "workflows", "validate.yml");
if (fs.existsSync(workflowPath)) {
  const workflow = fs.readFileSync(workflowPath, "utf8");
  if (!workflow.includes("runs-on: ubuntu-latest")) {
    errors.push(".github/workflows/validate.yml should run validators on ubuntu-latest to catch Linux compatibility.");
  }
  if (!workflow.includes("npm run validate")) {
    errors.push(".github/workflows/validate.yml should execute npm run validate.");
  }
}

if (errors.length) {
  fail("cross-platform validation failed", errors);
} else {
  ok("repo automation remains portable across Linux, Windows and macOS conventions.");
}
