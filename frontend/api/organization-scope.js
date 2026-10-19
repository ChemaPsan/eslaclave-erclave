import { apiRequest } from "./client.js";
import { getDemoTenantId } from "./config.js";

export async function getMembershipScope(userId) {
  return (await apiRequest(`/v1/users/${encodeURIComponent(userId)}/organization-scope`, {
    headers: { "X-Tenant-Id": getDemoTenantId() }
  })).data;
}

export async function saveMembershipScope(userId, payload, key) {
  return (await apiRequest(`/v1/users/${encodeURIComponent(userId)}/organization-scope`, {
    method: "PUT", body: JSON.stringify(payload),
    headers: { "X-Tenant-Id": getDemoTenantId(), "Idempotency-Key": key, "X-Correlation-Id": key }
  })).data;
}
