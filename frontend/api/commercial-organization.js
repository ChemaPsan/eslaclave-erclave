import { apiRequestAt, ErclaveApiError } from "./client.js";
import { getSalesApiBaseUrl, getPurchasingApiBaseUrl, getDemoTenantId } from "./config.js";
const domains = { customer: { module: "sales", base: getSalesApiBaseUrl }, supplier: { module: "purchasing", base: getPurchasingApiBaseUrl } };
async function request(kind, path, options = {}) {
 const domain = domains[kind];
 if (!domain?.base()) throw new ErclaveApiError("Assignment authority unavailable.", 503, null, { code: "assignment_authority_unavailable" });
 return apiRequestAt(domain.base(), `/v1/${domain.module}${path}`, { ...options, headers: { "X-Tenant-Id": getDemoTenantId(), ...options.headers } }, "Organization API");
}
export function findCommercialDivisions(kind, q = "", offset = 0) { return request(kind, `/organization/divisions?${new URLSearchParams({ q, offset, limit: 20 })}`); }
export function getCommercialAssignments(kind, id, offset = 0, division = "") { const params = new URLSearchParams({ limit: 25, offset }); if (division) params.set("division_id", division); return request(kind, `/${kind}s/${encodeURIComponent(id)}/division-assignments?${params}`); }
export async function saveCommercialAssignment(kind, id, division, payload, key) { return (await request(kind, `/${kind}s/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}`, { method: "PUT", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data; }
export async function getCommercialTerms(kind, id, division) { return (await request(kind, `/${kind}s/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}/commercial-terms`)).data; }
export async function saveCommercialTerms(kind, id, division, payload, key) { return (await request(kind, `/${kind}s/${encodeURIComponent(id)}/division-assignments/${encodeURIComponent(division)}/commercial-terms`, { method: "PUT", body: JSON.stringify(payload), headers: { "Idempotency-Key": key, "X-Correlation-Id": key } })).data; }
export async function getCommercialTermReferences(kind) { return (await request(kind, "/reference-data")).data; }
