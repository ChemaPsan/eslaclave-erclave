import { apiRequest } from "./client.js";
import { getDemoTenantId } from "./config.js";

export function listOrganization(kind, filters = {}, signal) {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value !== "" && value != null));
  return apiRequest(`/v1/organization/${kind}?${query}`, { signal, headers: { "X-Tenant-Id": getDemoTenantId() } });
}

export async function saveOrganization(kind, { id, action, payload = {}, key }) {
  const suffix = id ? `/${encodeURIComponent(id)}${action ? `/${action}` : ""}` : "";
  return (await apiRequest(`/v1/organization/${kind}${suffix}`, {
    method: id && !action ? "PATCH" : "POST",
    headers: { "X-Tenant-Id": getDemoTenantId(), "Idempotency-Key": key, "X-Correlation-Id": key },
    ...(action ? {} : { body: JSON.stringify(payload) })
  })).data;
}
