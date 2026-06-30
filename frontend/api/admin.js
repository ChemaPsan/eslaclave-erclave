import { getDemoActorId, getDemoTenantId } from "./config.js";
import { apiRequest } from "./client.js";


export async function getAdminDashboard() {
  const tenantId = getDemoTenantId();
  const actorId = getDemoActorId();

  const [tenant, entitlements, users, roles, policy] = await Promise.all([
    apiRequest(`/v1/tenants/${tenantId}`),
    apiRequest(`/v1/tenants/${tenantId}/entitlements`),
    apiRequest("/v1/users", { headers: { "X-Tenant-Id": tenantId } }),
    apiRequest("/v1/roles", { headers: { "X-Tenant-Id": tenantId } }),
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
    policy: policy.data
  };
}
