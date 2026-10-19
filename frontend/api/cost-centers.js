import { apiRequestAt, ErclaveApiError } from "./client.js";
import { getCostingApiBaseUrl, getDemoTenantId, getDemoActorId } from "./config.js";
async function request(path, options = {}) {
  const base = getCostingApiBaseUrl();
  if (!base) throw new ErclaveApiError("Service unavailable", 503, null, { code: "cost_center_storage_unavailable" });
  return apiRequestAt(base, path, { ...options, headers: { "X-Tenant-Id": getDemoTenantId(), "X-Actor-Id": getDemoActorId(), ...options.headers } }, "Costing API");
}
export function listCostCenters(divisionId, { q = "", status = "", offset = 0 } = {}) {
  const params = new URLSearchParams({ division_id: divisionId, q, offset: String(offset), limit: "25" });
  if (status) params.set("status", status);
  return request(`/v1/cost-centers?${params}`);
}
export async function saveCostCenter({ id, action, payload, key }) {
  const path = `/v1/cost-centers${id ? `/${encodeURIComponent(id)}` : ""}${action ? `/${action}` : ""}`;
  return (await request(path, { method: id && !action ? "PATCH" : "POST", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data;
}
