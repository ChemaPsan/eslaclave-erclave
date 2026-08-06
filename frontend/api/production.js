import { apiRequestAt } from "./client.js";
import { getDemoTenantId, getProductionApiBaseUrl } from "./config.js";

function commandHeaders() {
  const id = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  return { "X-Tenant-Id": getDemoTenantId(), "X-Correlation-Id": `web-${id}`, "Idempotency-Key": `web-${id}` };
}

function productionRequest(path, options = {}) {
  return apiRequestAt(getProductionApiBaseUrl(), path, {
    ...options,
    headers: { "X-Tenant-Id": getDemoTenantId(), ...(options.headers || {}) }
  }, "Production API");
}

export async function getProductionCatalog() {
  const [products, recipes, machines, orders] = await Promise.all([
    productionRequest("/v1/production/product-services?limit=200"),
    productionRequest("/v1/production/recipes?limit=200"),
    productionRequest("/v1/production/machines"),
    productionRequest("/v1/production/orders?limit=200")
  ]);
  return { products: products.data, recipes: recipes.data, machines: machines.data, orders: orders.data };
}

export async function createProductionProductService(payload){return (await productionRequest("/v1/production/product-services",{method:"POST",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function updateProductionProductService(id,payload){return (await productionRequest(`/v1/production/product-services/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function updateProductionProductServiceStatus(id,payload){return (await productionRequest(`/v1/production/product-services/${id}/status`,{method:"PATCH",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}

export async function createProductionRecipe(payload) {
  return (await productionRequest("/v1/production/recipes", { method: "POST", headers: commandHeaders(), body: JSON.stringify(payload) })).data;
}

export async function updateProductionRecipeVersion(versionId, payload) {
  return (await productionRequest(`/v1/production/recipe-versions/${versionId}`, { method: "PATCH", headers: commandHeaders(), body: JSON.stringify(payload) })).data;
}

export async function createProductionRecipeVersion(recipeId, payload) {
  return (await productionRequest(`/v1/production/recipes/${recipeId}/versions`, { method: "POST", headers: commandHeaders(), body: JSON.stringify(payload) })).data;
}

export async function submitProductionRecipeVersion(versionId) {
  return (await productionRequest(`/v1/production/recipe-versions/${versionId}/submit`, { method: "POST", headers: commandHeaders() })).data;
}

export async function approveProductionRecipeVersion(versionId, payload = {}) {
  return (await productionRequest(`/v1/production/recipe-versions/${versionId}/approve`, { method: "POST", headers: commandHeaders(), body: JSON.stringify(payload) })).data;
}

export async function createProductionMachine(payload){return (await productionRequest("/v1/production/machines",{method:"POST",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function updateProductionMachine(id,payload){return (await productionRequest(`/v1/production/machines/${id}`,{method:"PATCH",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function validateProductionResources(payload){return (await productionRequest("/v1/production/resource-validations",{method:"POST",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function createProductionOrder(payload){return (await productionRequest("/v1/production/orders",{method:"POST",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function updateProductionOrderStatus(id,payload){return (await productionRequest(`/v1/production/orders/${id}/status`,{method:"PATCH",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function updateProductionOrderStage(id,payload){return (await productionRequest(`/v1/production/order-stages/${id}`,{method:"PATCH",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
