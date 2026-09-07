const REQUIRED_LOCAL_ENDPOINTS = [
  ["frontend", "http://127.0.0.1:4173/"],
  ["admin-service", "http://127.0.0.1:8000/health"],
  ["production-service", "http://127.0.0.1:8002/health"],
  ["inventory-service", "http://127.0.0.1:8004/health"],
  ["hr-service", "http://127.0.0.1:8006/health"],
  ["sales-service", "http://127.0.0.1:8008/health"],
  ["purchasing-service", "http://127.0.0.1:8010/health"],
  ["maintenance-service", "http://127.0.0.1:8012/health"],
  ["firebase-auth-emulator", "http://127.0.0.1:9099/"]
];

function assertLoopback(rawUrl, label) {
  const parsed = new URL(rawUrl);
  if (!["127.0.0.1", "localhost", "[::1]"].includes(parsed.hostname)) {
    throw new Error(`Guardrail E2E: ${label} debe apuntar a loopback, no a ${parsed.hostname}.`);
  }
}

module.exports = async () => {
  const baseUrl = process.env.ERCLAVE_E2E_BASE_URL || "http://127.0.0.1:4173";
  assertLoopback(baseUrl, "ERCLAVE_E2E_BASE_URL");

  const failures = [];
  for (const [name, url] of REQUIRED_LOCAL_ENDPOINTS) {
    assertLoopback(url, name);
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(3_000) });
      if (!response.ok) failures.push(`${name}: HTTP ${response.status}`);
    } catch (error) {
      failures.push(`${name}: ${error.message}`);
    }
  }
  if (failures.length) {
    throw new Error(`El stack Local no esta completo. Ejecuta backend/scripts/start_local.ps1.\n${failures.join("\n")}`);
  }
};
