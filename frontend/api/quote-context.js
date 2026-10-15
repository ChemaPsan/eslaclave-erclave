import { apiRequestAt } from "./client.js";
import { getSalesApiBaseUrl, getDemoTenantId } from "./config.js";
const request = (path, options={}) => apiRequestAt(getSalesApiBaseUrl(),path,{...options,headers:{"X-Tenant-Id":getDemoTenantId(),...options.headers}},"Sales API");
export async function readQuoteContext(id){return (await request(`/v1/sales/quotes/${encodeURIComponent(id)}`)).data;}
export function findQuoteDivisions(q="",offset=0){return request(`/v1/sales/organization/quote-divisions?${new URLSearchParams({q,offset,limit:20})}`);}
export async function saveQuoteContext(id,payload,key){return (await request(`/v1/sales/quotes/${encodeURIComponent(id)}/organization-context`,{method:"PUT",body:JSON.stringify(payload),headers:{"Idempotency-Key":key,"X-Correlation-Id":key}})).data;}
