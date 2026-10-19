import { apiRequest } from "./client.js";
import { getDemoTenantId } from "./config.js";
export async function scopedTemplate(kind, id, payload, key) {
  return (await apiRequest(`/v1/configuration/document-template/${encodeURIComponent(kind)}/${encodeURIComponent(id)}`, {
    method: payload ? "PUT" : "GET", ...(payload ? { body: JSON.stringify(payload) } : {}),
    headers: { "X-Tenant-Id": getDemoTenantId(), ...(key ? { "Idempotency-Key": key, "X-Correlation-Id": key } : {}) }
  })).data;
}
