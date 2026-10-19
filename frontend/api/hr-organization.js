import { apiRequestAt, ErclaveApiError } from "./client.js";
import { getHrApiBaseUrl, getCostingApiBaseUrl, getDemoTenantId } from "./config.js";
async function request(path, options = {}, costing = false) {
 const base = costing ? getCostingApiBaseUrl() : getHrApiBaseUrl();
 if (!base) throw new ErclaveApiError("Assignment authority unavailable.", 503, null, { code: "assignment_authority_unavailable" });
 try {
  return await apiRequestAt(base, path, { ...options, headers: { "X-Tenant-Id": getDemoTenantId(), ...options.headers } }, costing ? "Costing API" : "HR API");
 } catch (error) {
  // HR's existing error envelope names fields instead of FastAPI loc paths.
  const fields = new Set(["hourly_cost", "hourly_cost_currency_code", "status", "expected_revision", "cost_center_ref_id"]);
  if (!costing && Array.isArray(error.details?.issues)) error.details = { ...error.details, issues: error.details.issues.map(issue => fields.has(issue.field) ? { ...issue, loc: ["body", issue.field] } : issue) };
  throw error;
 }
}
export function findAssignmentDivisions(q = "", offset = 0) { return request(`/v1/hr/organization/divisions?${new URLSearchParams({ q, offset, limit: 20 })}`); }
export function findAssignmentCenters(division, q = "", offset = 0) { return request(`/v1/cost-centers/eligible?${new URLSearchParams({ division_id: division, q, offset, limit: 20 })}`, {}, true); }
export function getHrDivisions(kind, id, offset = 0, division = "") { const params = new URLSearchParams({ limit: 25, offset }); if (division) params.set("division_id", division); return request(`/v1/hr/${kind}s/${encodeURIComponent(id)}/division-assignments?${params}`); }
export async function saveHrAssignment(kind, id, division, payload, key) {
 return (await request(`/v1/hr/${kind}s/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}`, { method: "PUT", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data;
}

export function getDivisionProductionCapacity(division) { return request(`/v1/hr/division-production-capacity?${new URLSearchParams({ division_id: division })}`); }

export function getDivisionProductionWorkers(division,q="",offset=0){return request(`/v1/hr/division-workers?${new URLSearchParams({division_id:division,purpose:"production",q,offset,limit:20})}`);}
