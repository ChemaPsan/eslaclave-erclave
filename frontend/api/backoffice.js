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


export async function listBackofficeTenants(search = "", limit = 50) {
  const params = new URLSearchParams();
  if (search.trim()) params.set("search", search.trim());
  params.set("limit", String(limit));
  const query = params.toString();
  const response = await apiRequest(`/v1/backoffice/tenants${query ? `?${query}` : ""}`);
  return response.data;
}


export async function listBackofficeModules() {
  const response = await apiRequest("/v1/backoffice/modules");
  return response.data;
}


export async function updateBackofficeTenant(tenantId, payload) {
  const response = await apiRequest(`/v1/backoffice/tenants/${encodeURIComponent(tenantId)}`, {
    method: "PATCH",
    headers: commandHeaders(),
    body: JSON.stringify(payload)
  });
  return response.data;
}


export async function setBackofficeTenantEntitlement(tenantId, moduleCode, payload) {
  const response = await apiRequest(`/v1/backoffice/tenants/${encodeURIComponent(tenantId)}/entitlements/${encodeURIComponent(moduleCode)}`, {
    method: "PUT",
    headers: commandHeaders(),
    body: JSON.stringify(payload)
  });
  return response.data;
}


export async function listBackofficeUsage({ fromDate = "", toDate = "", tenantId = "", limit = 200 } = {}) {
  const params = new URLSearchParams();
  if (fromDate) params.set("from_date", fromDate);
  if (toDate) params.set("to_date", toDate);
  if (tenantId) params.set("tenant_id", tenantId);
  params.set("limit", String(limit));
  const response = await apiRequest(`/v1/backoffice/usage?${params.toString()}`);
  return response;
}


export async function setBackofficeTenantStatus(tenantId, status) {
  const response = await apiRequest(`/v1/backoffice/tenants/${encodeURIComponent(tenantId)}/status`, {
    method: "PATCH",
    headers: commandHeaders(),
    body: JSON.stringify({ status })
  });

  return response.data;
}


export async function deleteBackofficeTenant(tenantId) {
  const response = await apiRequest(`/v1/backoffice/tenants/${encodeURIComponent(tenantId)}`, {
    method: "DELETE",
    headers: commandHeaders()
  });

  return response.data;
}
