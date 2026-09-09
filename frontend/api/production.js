import { apiDownloadAt, apiRequestAt } from "./client.js";
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
export function downloadProductionReport(code,filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==""&&value!=="all")query.set(key,String(value));});return apiDownloadAt(getProductionApiBaseUrl(),`/v1/production/reports/${encodeURIComponent(code)}/export?${query}`,{headers:{"X-Tenant-Id":getDemoTenantId()}},"Production API");}

export async function getProductionCatalog(options = {}) {
  const enabled = { products: true, recipes: true, machines: true, orders: true, ...options };
  const [products, recipes, machines, orders] = await Promise.all([
    enabled.products ? productionRequest("/v1/production/product-services?limit=200") : { data: [] },
    enabled.recipes ? productionRequest("/v1/production/recipes?limit=200") : { data: [] },
    enabled.machines ? productionRequest("/v1/production/machines") : { data: [] },
    enabled.orders ? productionRequest("/v1/production/orders?limit=200") : { data: [] }
  ]);
  return { products: products.data, recipes: recipes.data, machines: machines.data, orders: orders.data };
}
export async function getProductionProducts(){return (await productionRequest("/v1/production/product-services?limit=200&status=active")).data;}
export async function getFinishedGoodsCandidates(){
  const candidates=(await productionRequest("/v1/production/finished-goods-candidates?limit=200")).data||[];
  const products=[...new Map(candidates.map((candidate)=>[candidate.product.id,candidate.product])).values()];
  return {orders:candidates.map((candidate)=>candidate.order),products};
}
export async function getProductionWarehouseRequests(offset=0){return productionRequest(`/v1/production/warehouse-material-requests?limit=25&offset=${offset}`);}
export async function issueProductionMaterials(id){return (await productionRequest(`/v1/production/orders/${id}/issue-materials`,{method:"POST",headers:commandHeaders()})).data;}
export async function getUnlinkedProductionProducts(){return (await productionRequest("/v1/production/product-services?limit=200&status=active&type=product&inventory_mapping=missing")).data;}
export async function createAndLinkFinishedGood(id,inventoryItem){return (await productionRequest(`/v1/production/product-services/${id}/finished-good-link`,{method:"PUT",headers:commandHeaders(),body:JSON.stringify({inventory_item:inventoryItem})})).data;}

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
export async function updateProductionOrderResource(orderId,resourceId,payload){return (await productionRequest(`/v1/production/orders/${orderId}/resources/${resourceId}`,{method:"PATCH",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}
export async function updateProductionOrderStage(id,payload){return (await productionRequest(`/v1/production/order-stages/${id}`,{method:"PATCH",headers:commandHeaders(),body:JSON.stringify(payload)})).data;}

export function getProductionReturnableMaterials(offset=0){return productionRequest(`/v1/production/returnable-materials?limit=26&offset=${offset}`);}

export function getFailedProductionCreations(offset=0){return productionRequest(`/v1/production/failed-order-creations?limit=26&offset=${offset}`);}
export async function recoverProductionCreation(id){return (await productionRequest(`/v1/production/failed-order-creations/${encodeURIComponent(id)}/recover`,{method:"POST",headers:commandHeaders()})).data;}
