import { apiRequestAt, ErclaveApiError } from "./client.js";
import { getInventoryApiBaseUrl, getCostingApiBaseUrl, getDemoTenantId, getDemoActorId } from "./config.js";
async function request(path, options = {}, costing = false) {
 const base = costing ? getCostingApiBaseUrl() : getInventoryApiBaseUrl();
 if (!base) throw new ErclaveApiError("Assignment authority unavailable.", 503, null, { code: "assignment_authority_unavailable" });
 return apiRequestAt(base, path, { ...options, headers: { "X-Tenant-Id": getDemoTenantId(), "X-Actor-Id": getDemoActorId(), ...options.headers } }, costing ? "Costing API" : "Inventory API");
}
export function findAssignmentDivisions(q = "", offset = 0) { return request(`/v1/inventory/organization/divisions?${new URLSearchParams({ q, offset, limit: 20 })}`); }
export function findAssignmentCenters(division, q = "", offset = 0) { return request(`/v1/cost-centers/eligible?${new URLSearchParams({ division_id: division, q, offset, limit: 20 })}`, {}, true); }
export async function getWarehouseDivision(id) { return (await request(`/v1/inventory/warehouses/${encodeURIComponent(id)}/division`)).data; }
export function getItemDivisions(id, offset = 0, division = "") { const params = new URLSearchParams({ limit: 25, offset }); if (division) params.set("division_id", division); return request(`/v1/inventory/items/${encodeURIComponent(id)}/division-assignments?${params}`); }
export async function saveInventoryAssignment(kind, id, division, payload, key) {
 const path = kind === "warehouse" ? `/v1/inventory/warehouses/${encodeURIComponent(id)}/division` : `/v1/inventory/items/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}`;
 return (await request(path, { method: kind === "warehouse" ? "PATCH" : "PUT", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data;
}
