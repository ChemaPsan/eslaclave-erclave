import { getDemoActorId, getDemoTenantId } from "./config.js";
import { apiRequest } from "./client.js";


function commandHeaders(extraHeaders = {}) {
  const commandId =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random()}`;
  return {
    "X-Correlation-Id": `web-${commandId}`,
    "Idempotency-Key": `web-${commandId}`,
    ...extraHeaders
  };
}


export async function getAdminDashboard() {
  const tenantId = getDemoTenantId();
  const actorId = getDemoActorId();

  const [tenant, entitlements, users, roles, permissions, policy] = await Promise.all([
    apiRequest(`/v1/tenants/${tenantId}`),
    apiRequest(`/v1/tenants/${tenantId}/entitlements`),
    apiRequest("/v1/users", { headers: { "X-Tenant-Id": tenantId } }),
    apiRequest("/v1/roles", { headers: { "X-Tenant-Id": tenantId } }),
    apiRequest("/v1/permissions"),
    apiRequest("/v1/policy/evaluate", {
      method: "POST",
      body: JSON.stringify({
        tenant_id: tenantId,
        actor_id: actorId,
        module: "admin",
        resource: "tenant",
        action: "read",
        scope: {}
      })
    })
  ]);

  return {
    tenant: tenant.data,
    entitlements: entitlements.data,
    users: users.data,
    roles: roles.data,
    permissions: permissions.data,
    policy: policy.data
  };
}


export async function updateTenantEntitlement(moduleCode, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/tenants/${tenantId}/entitlements/${moduleCode}`, {
    method: "PUT",
    headers: commandHeaders(),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function inviteTenantUser(payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest("/v1/users/invitations", {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function updateTenantUser(userId, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/users/${userId}`, {
    method: "PATCH",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function disableTenantUser(userId) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/users/${userId}/disable`, {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId })
  });

  return response.data;
}


export async function createTenantRole(payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest("/v1/roles", {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function updateTenantRole(roleId, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/roles/${roleId}`, {
    method: "PATCH",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function replaceTenantRolePermissions(roleId, permissionIds) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/roles/${roleId}/permissions`, {
    method: "PUT",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify({ permission_ids: permissionIds, scope: {} })
  });

  return response.data;
}
