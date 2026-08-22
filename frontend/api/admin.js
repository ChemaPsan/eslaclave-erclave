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

  const tenant = await apiRequest(`/v1/tenants/${tenantId}`);
  const entitlements = await apiRequest(`/v1/tenants/${tenantId}/entitlements`);
  const settings = await apiRequest("/v1/settings?module_code=admin", { headers: { "X-Tenant-Id": tenantId } });
  const users = await apiRequest("/v1/users", { headers: { "X-Tenant-Id": tenantId } });
  const roles = await apiRequest("/v1/roles", { headers: { "X-Tenant-Id": tenantId } });
  const permissions = await apiRequest("/v1/permissions", { headers: { "X-Tenant-Id": tenantId } });
  const units = await apiRequest("/v1/catalogs/units-of-measure", { headers: { "X-Tenant-Id": tenantId } });
  const currencies = await apiRequest("/v1/catalogs/commercial/currencies?include_inactive=true", { headers: { "X-Tenant-Id": tenantId } });
  const paymentTerms = await apiRequest("/v1/catalogs/commercial/payment_terms?include_inactive=true", { headers: { "X-Tenant-Id": tenantId } });
  const documentTemplate = await apiRequest("/v1/document-template", { headers: { "X-Tenant-Id": tenantId } });
  const codeSequences = (session?.permissions || []).includes("admin.setting.read")
    ? await apiRequest("/v1/catalogs/code-sequences", { headers: { "X-Tenant-Id": tenantId } })
    : { data: [] };
  const canReadTenant = (session?.permissions || []).includes("admin.tenant.read");

  return {
    tenant: tenant.data,
    session,
    entitlements: entitlements.data,
    settings: settings.data,
    organization: settings.data.find((item) => item.key === "organization.profile")?.value || null,
    users: users.data,
    roles: roles.data,
    permissions: permissions.data,
    units: units.data,
    commercialCatalogs: { currencies: currencies.data, payment_terms: paymentTerms.data },
    documentTemplate: documentTemplate.data,
    codeSequences: codeSequences.data,
    policy: {
      allowed: canReadTenant,
      reason: canReadTenant ? "session_permission" : "permission_not_granted",
      matched_permissions: canReadTenant ? ["admin.tenant.read"] : []
    }
  };
}

export async function getCommercialCatalog(catalogCode, includeInactive = true) {
  const tenantId = getDemoTenantId();
  return (await apiRequest(`/v1/catalogs/commercial/${catalogCode}?include_inactive=${includeInactive}`, { headers: { "X-Tenant-Id": tenantId } })).data;
}

export async function createCommercialCatalogItem(catalogCode, payload) {
  const tenantId = getDemoTenantId();
  return (await apiRequest(`/v1/catalogs/commercial/${catalogCode}`, { method: "POST", headers: commandHeaders({ "X-Tenant-Id": tenantId }), body: JSON.stringify(payload) })).data;
}

export async function updateCommercialCatalogItem(catalogCode, itemId, payload) {
  const tenantId = getDemoTenantId();
  return (await apiRequest(`/v1/catalogs/commercial/${catalogCode}/${itemId}`, { method: "PATCH", headers: commandHeaders({ "X-Tenant-Id": tenantId }), body: JSON.stringify(payload) })).data;
}

export async function getDocumentTemplate() {
  const tenantId = getDemoTenantId();
  return (await apiRequest("/v1/document-template", { headers: { "X-Tenant-Id": tenantId } })).data;
}

export async function updateDocumentTemplate(payload) {
  const tenantId = getDemoTenantId();
  return (await apiRequest("/v1/document-template", { method: "PUT", headers: commandHeaders({ "X-Tenant-Id": tenantId }), body: JSON.stringify(payload) })).data;
}

export async function getCodeSequences() {
  const tenantId = getDemoTenantId();
  return (await apiRequest("/v1/catalogs/code-sequences", { headers: { "X-Tenant-Id": tenantId } })).data;
}

export async function updateCodeSequence(sequenceId, payload) {
  const tenantId = getDemoTenantId();
  return (await apiRequest(`/v1/catalogs/code-sequences/${sequenceId}`, { method: "PATCH", headers: commandHeaders({ "X-Tenant-Id": tenantId }), body: JSON.stringify(payload) })).data;
}

export async function allocateBusinessCode(documentType, manualCode = null, requestKey = null) {
  const tenantId = getDemoTenantId();
  return (await apiRequest(`/v1/catalogs/code-sequences/${encodeURIComponent(documentType)}/next`, { method: "POST", headers: commandHeaders({ "X-Tenant-Id": tenantId, ...(requestKey ? { "Idempotency-Key": requestKey } : {}) }), body: JSON.stringify({ manual_code: manualCode || null }) })).data;
}

export async function getUnitsOfMeasure(includeInactive = false) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/catalogs/units-of-measure?include_inactive=${includeInactive}`, { headers: { "X-Tenant-Id": tenantId } });
  return response.data;
}

export async function createUnitOfMeasure(payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest("/v1/catalogs/units-of-measure", { method: "POST", headers: commandHeaders({ "X-Tenant-Id": tenantId }), body: JSON.stringify(payload) });
  return response.data;
}

export async function updateUnitOfMeasure(unitId, payload) {
  const tenantId = getDemoTenantId();
  const response = await apiRequest(`/v1/catalogs/units-of-measure/${unitId}`, { method: "PATCH", headers: commandHeaders({ "X-Tenant-Id": tenantId }), body: JSON.stringify(payload) });
  return response.data;
}


export async function getSessionContext() {
  const tenantId = getDemoTenantId();
  const actorId = getDemoActorId();
  if (!tenantId) throw new Error("No se ha resuelto un tenant activo para la sesion.");
  const response = await apiRequest("/v1/session/context", {
    headers: {
      "X-Tenant-Id": tenantId,
      ...(actorId ? { "X-Actor-Id": actorId } : {})
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
