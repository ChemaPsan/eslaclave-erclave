const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TENANT_ID = "ten_739ee59d765d5e14818674800d";
const DEFAULT_ACTOR_ID = "usr_595f3cd6d4325901a8dbd028e1";


export function getApiMode() {
  return localStorage.getItem("erclave-api-mode") || "mock";
}


export function setApiMode(mode) {
  localStorage.setItem("erclave-api-mode", mode === "api" ? "api" : "mock");
}


export function getApiBaseUrl() {
  return localStorage.getItem("erclave-api-base-url") || DEFAULT_API_BASE_URL;
}


export function getDemoTenantId() {
  return localStorage.getItem("erclave-api-tenant-id") || DEFAULT_TENANT_ID;
}


export function getDemoActorId() {
  return localStorage.getItem("erclave-api-actor-id") || DEFAULT_ACTOR_ID;
}
