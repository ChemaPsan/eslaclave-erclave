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
  const [products, recipes] = await Promise.all([
    productionRequest("/v1/production/product-services?limit=200"),
    productionRequest("/v1/production/recipes?limit=200")
  ]);
  return { products: products.data, recipes: recipes.data };
}

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
