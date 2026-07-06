import { apiRequest } from "./client.js";


function commandHeaders() {
  const commandId =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()}`;
  return {
    "X-Correlation-Id": `backoffice-${commandId}`,
    "Idempotency-Key": `backoffice-${commandId}`
  };
}


export async function onboardTenant(payload) {
  const response = await apiRequest("/v1/provisioning/tenant-onboarding", {
    method: "POST",
    headers: commandHeaders(),
    body: JSON.stringify(payload)
  });

  return response.data;
}
