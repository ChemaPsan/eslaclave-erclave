import { apiRequestAt } from "./client.js";
import { getDemoTenantId,getMaintenanceApiBaseUrl } from "./config.js";
function request(path,options={}){const command=options.method&&options.method!=="GET";const id=crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;return apiRequestAt(getMaintenanceApiBaseUrl(),path,{...options,headers:{"X-Tenant-Id":getDemoTenantId(),...(command?{"X-Correlation-Id":`web-${id}`,"Idempotency-Key":`web-${id}`}:{}) ,...(options.headers||{})}},"Maintenance API");}
export async function getMaintenanceOrders(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([k,v])=>{if(v!==undefined&&v!==null&&v!=="")query.set(k,String(v));});return (await request(`/v1/maintenance/orders?${query}`)).data;}
export async function createMaintenanceOrder(payload){return (await request("/v1/maintenance/orders",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateMaintenanceOrder(id,payload){return (await request(`/v1/maintenance/orders/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function transitionMaintenanceOrder(id,transition,extra={}){return (await request(`/v1/maintenance/orders/${id}/transitions`,{method:"POST",body:JSON.stringify({transition,...extra})})).data;}
export async function reconcileMaintenanceOrder(id){return (await request(`/v1/maintenance/orders/${id}/reconcile`,{method:"POST"})).data;}
export async function createMaintenanceTime(id,payload){return (await request(`/v1/maintenance/orders/${id}/time-entries`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function createMaintenanceMaterialRequest(id,payload){return (await request(`/v1/maintenance/orders/${id}/material-requests`,{method:"POST",body:JSON.stringify(payload)})).data;}
export async function cancelMaintenanceMaterialRequest(id){return (await request(`/v1/maintenance/material-requests/${id}/cancel`,{method:"POST"})).data;}
export async function reconcileMaintenanceMaterialRequest(id){return (await request(`/v1/maintenance/material-requests/${id}/reconcile`,{method:"POST"})).data;}
