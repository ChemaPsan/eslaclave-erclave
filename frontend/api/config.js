const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TENANT_ID = "ten_739ee59d765d5e14818674800d";
const DEFAULT_ACTOR_ID = "usr_595f3cd6d4325901a8dbd028e1";


function getRuntimeConfigValue(key) {
  return window.ERCLAVE_CONFIG?.[key] || "";
}


export function getApiMode() {
  return localStorage.getItem("erclave-api-mode") || getRuntimeConfigValue("apiMode") || "mock";
}


export function setApiMode(mode) {
  localStorage.setItem("erclave-api-mode", mode === "api" ? "api" : "mock");
}


export function getApiBaseUrl() {
  return localStorage.getItem("erclave-api-base-url") || getRuntimeConfigValue("apiBaseUrl") || DEFAULT_API_BASE_URL;
}


export function getDemoTenantId() {
  return localStorage.getItem("erclave-api-tenant-id") || getRuntimeConfigValue("tenantId") || DEFAULT_TENANT_ID;
}


export function getDemoActorId() {
  return localStorage.getItem("erclave-api-actor-id") || getRuntimeConfigValue("actorId") || DEFAULT_ACTOR_ID;
}
