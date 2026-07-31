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
  const session = await getSessionContext();
  const actorId = session?.user?.id || getDemoActorId();

  const tenant = await apiRequest(`/v1/tenants/${tenantId}`);
  const entitlements = await apiRequest(`/v1/tenants/${tenantId}/entitlements`);
  const settings = await apiRequest("/v1/settings?module_code=admin", { headers: { "X-Tenant-Id": tenantId } });
  const users = await apiRequest("/v1/users", { headers: { "X-Tenant-Id": tenantId } });
  const roles = await apiRequest("/v1/roles", { headers: { "X-Tenant-Id": tenantId } });
  const permissions = await apiRequest("/v1/permissions", { headers: { "X-Tenant-Id": tenantId } });
  const policy = await apiRequest("/v1/policy/evaluate", {
    method: "POST",
    body: JSON.stringify({
      tenant_id: tenantId,
      actor_id: actorId,
      module: "admin",
      resource: "tenant",
      action: "read",
      scope: {}
    })
  });

  return {
    tenant: tenant.data,
    session,
    entitlements: entitlements.data,
    settings: settings.data,
    organization: settings.data.find((item) => item.key === "organization.profile")?.value || null,
    users: users.data,
    roles: roles.data,
    permissions: permissions.data,
    policy: policy.data
  };
}


export async function getSessionContext() {
  const tenantId = getDemoTenantId();
  const actorId = getDemoActorId();
  const response = await apiRequest("/v1/session/context", {
    headers: {
      "X-Tenant-Id": tenantId,
      "X-Actor-Id": actorId
    }
  });

  return response.data;
}


export async function getSessionTenants() {
  const response = await apiRequest("/v1/session/tenants");
  return response.data;
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


export async function updateTenantSetting(key, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/settings/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function createTenantLegalEntity(payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest("/v1/organization/legal-entities", {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function updateTenantLegalEntity(legalEntityId, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/organization/legal-entities/${legalEntityId}`, {
    method: "PATCH",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function setTenantLegalEntityStatus(legalEntityId, status) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/organization/legal-entities/${legalEntityId}/${status === "active" ? "activate" : "deactivate"}`, {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId })
  });

  return response.data;
}


export async function createTenantBranch(payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest("/v1/organization/branches", {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function updateTenantBranch(branchId, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/organization/branches/${branchId}`, {
    method: "PATCH",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify(payload)
  });

  return response.data;
}


export async function setTenantBranchStatus(branchId, status) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/organization/branches/${branchId}/${status === "active" ? "activate" : "deactivate"}`, {
    method: "POST",
    headers: commandHeaders({ "X-Tenant-Id": tenantId })
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

export async function deleteTenantUser(userId) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/users/${userId}`, {
    method: "DELETE",
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


export async function replaceTenantRolePermissions(roleId, assignments, expectedRevision) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/roles/${roleId}/permissions`, {
    method: "PUT",
    headers: commandHeaders({ "X-Tenant-Id": tenantId }),
    body: JSON.stringify({
      assignments,
      expected_revision: expectedRevision
    })
  });

  return response.data;
}
