import { apiRequestAt } from "./client.js";
import { getDemoTenantId,getHrApiBaseUrl } from "./config.js";
function headers(command=false){const id=crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;return {"X-Tenant-Id":getDemoTenantId(),"X-Correlation-Id":`web-${id}`,...(command?{"Idempotency-Key":`web-${id}`}:{})};}
function request(path,options={}){return apiRequestAt(getHrApiBaseUrl(),path,{...options,headers:{...headers(Boolean(options.method&&options.method!=="GET")),...(options.headers||{})}},"HR API");}
export async function getHrCatalog(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([k,v])=>{if(v!==undefined&&v!==null&&v!=="")query.set(k,String(v));});const [areas,positions]=await Promise.all([request("/v1/hr/areas"),request(`/v1/hr/positions?${query}`)]);return {areas:areas.data,positions:positions.data};}
export async function getHrAreas(){return (await request("/v1/hr/areas")).data;}
export async function createHrArea(payload){return (await request("/v1/hr/areas",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateHrArea(id,payload){return (await request(`/v1/hr/areas/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function createHrPosition(payload){return (await request("/v1/hr/positions",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateHrPosition(id,payload){return (await request(`/v1/hr/positions/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
