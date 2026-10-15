import { apiRequestAt, ErclaveApiError } from "./client.js";
import { getProductionApiBaseUrl, getCostingApiBaseUrl, getDemoTenantId, getDemoActorId } from "./config.js";
async function request(path, options = {}, costing = false) {
 const base = costing ? getCostingApiBaseUrl() : getProductionApiBaseUrl();
 if (!base) throw new ErclaveApiError("Assignment authority unavailable.", 503, null, { code: "assignment_authority_unavailable" });
 return apiRequestAt(base, path, { ...options, headers: { "X-Tenant-Id": getDemoTenantId(), "X-Actor-Id": getDemoActorId(), ...options.headers } }, costing ? "Costing API" : "Production API");
}
export function findAssignmentDivisions(q = "", offset = 0) { return request(`/v1/production/organization/divisions?${new URLSearchParams({ q, offset, limit: 20 })}`); }
export function findAssignmentCenters(division, q = "", offset = 0) { return request(`/v1/cost-centers/eligible?${new URLSearchParams({ division_id: division, q, offset, limit: 20 })}`, {}, true); }
export async function getMachineDivision(id) { return (await request(`/v1/production/machines/${encodeURIComponent(id)}/division`)).data; }
export function getProductServiceDivisions(id, offset = 0, division = "") { const params = new URLSearchParams({ limit: 25, offset }); if (division) params.set("division_id", division); return request(`/v1/production/product-services/${encodeURIComponent(id)}/division-assignments?${params}`); }
export async function saveProductionAssignment(kind, id, division, payload, key) {
 const path = kind === "machine" ? `/v1/production/machines/${encodeURIComponent(id)}/division` : `/v1/production/product-services/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}`;
 return (await request(path, { method: kind === "machine" ? "PATCH" : "PUT", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data;
}
export async function saveProductEstimatedCost(id, division, payload, key) {
 return (await request(`/v1/production/product-services/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}/estimated-unit-cost`, { method: "PUT", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data;
}

export async function getMachineRate(id) { return (await request(`/v1/production/machines/${encodeURIComponent(id)}`)).data; }
export async function saveMachineRate(id, payload, key) { return (await request(`/v1/production/machines/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data; }

export function getDivisionMachineCapacity(division, date) { return request(`/v1/production/division-machines?${new URLSearchParams({ division_id: division, planned_date: date, limit: 25 })}`); }
