import { apiDownloadAt, apiRequestAt } from "./client.js";
import { getDemoTenantId, getPurchasingApiBaseUrl } from "./config.js";
function request(path,options={}){const command=options.method&&options.method!=="GET";const id=crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;return apiRequestAt(getPurchasingApiBaseUrl(),path,{...options,headers:{"X-Tenant-Id":getDemoTenantId(),...(command?{"X-Correlation-Id":`web-${id}`,"Idempotency-Key":`web-${id}`}:{}) ,...(options.headers||{})}},"Purchasing API");}
export function downloadPurchasingReport(code,filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==""&&value!=="all")query.set(key,String(value));});return apiDownloadAt(getPurchasingApiBaseUrl(),`/v1/purchasing/reports/${encodeURIComponent(code)}/export?${query}`,{headers:{"X-Tenant-Id":getDemoTenantId()}},"Purchasing API");}
export async function getPurchasingWorkspace(enabled={}){const names=["suppliers","requisitions","orders","receipts"];const values=await Promise.allSettled(names.map(name=>enabled[name]===false?Promise.resolve({data:[]}):request(`/v1/purchasing/${name}`)));const result={suppliers:[],requisitions:[],orders:[],receipts:[],errors:{}};values.forEach((value,index)=>value.status==="fulfilled"?result[names[index]]=value.value.data:result.errors[names[index]]=value.reason);return result;}
export async function createPurchasingSupplier(payload){return (await request("/v1/purchasing/suppliers",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updatePurchasingSupplier(id,payload){return (await request(`/v1/purchasing/suppliers/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function createPurchasingRequisition(payload){return (await request("/v1/purchasing/requisitions",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updatePurchasingRequisition(id,payload){return (await request(`/v1/purchasing/requisitions/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function transitionPurchasingRequisition(id,action,reason){return (await request(`/v1/purchasing/requisitions/${id}/${action}`,{method:"POST",...(reason?{body:JSON.stringify({reason})}:{})})).data;}
export async function cancelPurchasingRequisition(id,reason){return transitionPurchasingRequisition(id,"cancel",reason);}
export async function createPurchasingOrder(payload){return (await request("/v1/purchasing/orders",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updatePurchasingOrder(id,payload){return (await request(`/v1/purchasing/orders/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function issuePurchasingOrder(id){return (await request(`/v1/purchasing/orders/${id}/issue`,{method:"POST"})).data;}
export async function cancelPurchasingOrder(id,reason){return (await request(`/v1/purchasing/orders/${id}/cancel`,{method:"POST",body:JSON.stringify({reason})})).data;}
export async function createPurchasingReceipt(payload){return (await request("/v1/purchasing/receipts",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function reconcilePurchasingReceipt(id){return (await request(`/v1/purchasing/receipts/${id}/reconcile`,{method:"POST"})).data;}

export function getWarehousePurchaseReceipts(offset=0){return request(`/v1/purchasing/warehouse-receipts?limit=26&offset=${offset}`);}
export function getPurchasedServiceAcceptances(offset=0){return request(`/v1/purchasing/service-acceptances?limit=26&offset=${offset}`);}
export async function acceptPurchasedServices(id){return (await request(`/v1/purchasing/receipts/${encodeURIComponent(id)}/accept-services`,{method:"POST"})).data;}