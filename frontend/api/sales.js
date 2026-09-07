import { apiDownloadAt, apiRequestAt } from "./client.js";
import { getDemoTenantId, getSalesApiBaseUrl } from "./config.js";

function commandHeaders() {
  const id = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  return { "X-Tenant-Id": getDemoTenantId(), "X-Correlation-Id": `web-${id}`, "Idempotency-Key": `web-${id}` };
}
function request(path, options = {}) {
  const command = options.method && options.method !== "GET";
  return apiRequestAt(getSalesApiBaseUrl(), path, { ...options, headers: { "X-Tenant-Id": getDemoTenantId(), ...(command ? commandHeaders() : {}), ...(options.headers || {}) } }, "Sales API");
}
export function downloadSalesReport(code,filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==""&&value!=="all")query.set(key,String(value));});return apiDownloadAt(getSalesApiBaseUrl(),`/v1/sales/reports/${encodeURIComponent(code)}/export?${query}`,{headers:{"X-Tenant-Id":getDemoTenantId()}},"Sales API");}
export async function getSalesWorkspace({ customers = true, quotes = true, orders = true, deliveries = true, serviceOrders = true, references = true } = {}) {
  const names = ["customers", "quotes", "orders", "deliveries", "serviceOrders", "references"];
  const results = await Promise.allSettled([
    customers ? request("/v1/sales/customers") : Promise.resolve({ data: [] }),
    quotes ? request("/v1/sales/quotes") : Promise.resolve({ data: [] }),
    orders ? request("/v1/sales/orders") : Promise.resolve({ data: [] }),
    deliveries ? request("/v1/sales/deliveries") : Promise.resolve({ data: [] }),
    serviceOrders ? request("/v1/sales/service-orders") : Promise.resolve({ data: [] }),
    references ? request("/v1/sales/reference-data") : Promise.resolve({ data: { currencies: [], payment_terms: [] } })
  ]);
  const workspace = { customers: [], quotes: [], orders: [], deliveries: [], serviceOrders: [], references: { currencies: [], payment_terms: [] }, errors: {} };
  results.forEach((result, index) => {
    const name = names[index];
    if (result.status === "fulfilled") workspace[name] = result.value.data;
    else workspace.errors[name] = result.reason;
  });
  return workspace;
}
export async function createSalesCustomer(payload){return (await request("/v1/sales/customers",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateSalesCustomer(id,payload){return (await request(`/v1/sales/customers/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function createSalesQuote(payload){return (await request("/v1/sales/quotes",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateSalesQuote(id,payload){return (await request(`/v1/sales/quotes/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function submitSalesQuote(id){return (await request(`/v1/sales/quotes/${id}/submit`,{method:"POST"})).data;}
export async function approveSalesQuote(id){return (await request(`/v1/sales/quotes/${id}/approve`,{method:"POST"})).data;}
export async function expireSalesQuote(id){return (await request(`/v1/sales/quotes/${id}/expire`,{method:"POST"})).data;}
export async function cancelSalesQuote(id){return (await request(`/v1/sales/quotes/${id}/cancel`,{method:"POST"})).data;}
export async function createSalesOrder(payload){return (await request("/v1/sales/orders",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function configureSalesOrderFulfillment(id,payload){return (await request(`/v1/sales/orders/${id}/fulfillment`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function cancelSalesOrder(id,reason){return (await request(`/v1/sales/orders/${id}/cancel`,{method:"POST",body:JSON.stringify({reason})})).data;}
export async function createSalesDelivery(payload){return (await request("/v1/sales/deliveries",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function confirmSalesDelivery(id,reason){return (await request(`/v1/sales/deliveries/${id}/confirm`,{method:"POST",body:JSON.stringify({reason})})).data;}
export async function cancelSalesDelivery(id,reason){return (await request(`/v1/sales/deliveries/${id}/cancel`,{method:"POST",body:JSON.stringify({reason})})).data;}
export async function getSalesServiceOrder(id){return (await request(`/v1/sales/service-orders/${id}`)).data;}
export async function planSalesServiceOrder(id,payload){return (await request(`/v1/sales/service-orders/${id}/plan`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function addSalesServiceOrderTimeEntry(id,payload){return (await request(`/v1/sales/service-orders/${id}/time-entries`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function addSalesServiceOrderCostEntry(id,payload){return (await request(`/v1/sales/service-orders/${id}/cost-entries`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function addSalesServiceOrderEvidence(id,payload){return (await request(`/v1/sales/service-orders/${id}/evidence`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function transitionSalesServiceOrder(id,action,payload={}){return (await request(`/v1/sales/service-orders/${id}/transitions/${action}`,{method:"POST",body:JSON.stringify(payload)})).data;}
