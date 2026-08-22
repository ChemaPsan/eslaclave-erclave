import { apiRequestAt } from "./client.js";
import { getDemoTenantId, getInventoryApiBaseUrl } from "./config.js";
function headers(command=false){const id=crypto.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`;return {"X-Tenant-Id":getDemoTenantId(),"X-Correlation-Id":`web-${id}`,...(command?{"Idempotency-Key":`web-${id}`}:{})};}
function request(path,options={}){return apiRequestAt(getInventoryApiBaseUrl(),path,{...options,headers:{...headers(Boolean(options.method&&options.method!=="GET")),...(options.headers||{})}},"Inventory API");}
export async function getInventoryCatalog(){const warehouses=await request("/v1/inventory/warehouses");return {warehouses:warehouses.data};}
export async function getInventoryItems(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==""&&value!=="all")query.set(key,String(value));});return request(`/v1/inventory/items?${query.toString()}`);}
export async function getInventoryMovements(filters={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==""&&value!=="all")query.set(key,String(value));});return request(`/v1/inventory/movements?${query.toString()}`);}
export async function getInventoryBalances(filters={},options={}){const query=new URLSearchParams();Object.entries(filters).forEach(([key,value])=>{if(value!==undefined&&value!==null&&value!==""&&value!=="all")query.set(key,String(value));});return request(`/v1/inventory/balances?${query.toString()}`,{signal:options.signal});}
export async function createInventoryWarehouse(payload){return (await request("/v1/inventory/warehouses",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateInventoryWarehouse(id,payload){return (await request(`/v1/inventory/warehouses/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function createInventoryItem(payload){return (await request("/v1/inventory/items",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function updateInventoryItem(id,payload){return (await request(`/v1/inventory/items/${id}`,{method:"PATCH",body:JSON.stringify(payload)})).data;}
export async function createInventoryMovement(payload){return (await request("/v1/inventory/movements",{method:"POST",body:JSON.stringify(payload)})).data;}
export async function getFinishedGoodsReceipts(){return request("/v1/inventory/finished-goods-receipts");}
export async function createFinishedGoodsReceipt(payload){return (await request("/v1/inventory/finished-goods-receipts",{method:"POST",body:JSON.stringify(payload)})).data;}
