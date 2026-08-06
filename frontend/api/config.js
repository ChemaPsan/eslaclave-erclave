const LEGACY_DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_API_BASE_URL = "http://127.0.0.1:8010";
const DEFAULT_TENANT_ID = "ten_739ee59d765d5e14818674800d";
const DEFAULT_ACTOR_ID = "usr_595f3cd6d4325901a8dbd028e1";


function isLocalPreviewHost() {
  return ["localhost", "127.0.0.1"].includes(window.location.hostname);
}


function getRuntimeConfigValue(key) {
  return window.ERCLAVE_CONFIG?.[key] || "";
}


function getSafeLocalBaseUrl(candidate, fallback) {
  try {
    const parsed = new URL(candidate || fallback);
    if (!["localhost", "127.0.0.1"].includes(parsed.hostname)) return fallback;
    parsed.hostname = "127.0.0.1";
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return fallback;
  }
}


export function getApiMode() {
  return localStorage.getItem("erclave-api-mode") || getRuntimeConfigValue("apiMode") || "mock";
}


export function setApiMode(mode) {
  localStorage.setItem("erclave-api-mode", mode === "api" ? "api" : "mock");
}

export function isInventoryApiEnabled() {
  return (localStorage.getItem("erclave-inventory-api-mode") || getRuntimeConfigValue("inventoryApiMode") || "mock") === "api";
}


export function getApiBaseUrl() {
  const runtimeBaseUrl = getRuntimeConfigValue("apiBaseUrl");
  if (isLocalPreviewHost()) {
    const localOverride = localStorage.getItem("erclave-api-base-url") || "";
    const localRuntimeBaseUrl = getRuntimeConfigValue("localApiBaseUrl");
    const candidate = localOverride && localOverride !== LEGACY_DEFAULT_API_BASE_URL
      ? localOverride
      : localRuntimeBaseUrl || runtimeBaseUrl;
    return getSafeLocalBaseUrl(candidate, DEFAULT_API_BASE_URL);
  }
  return localStorage.getItem("erclave-api-base-url") || runtimeBaseUrl || DEFAULT_API_BASE_URL;
}


export function getProductionApiBaseUrl() {
  const runtimeBaseUrl = getRuntimeConfigValue("productionApiBaseUrl") || "http://127.0.0.1:8002";
  if (isLocalPreviewHost()) {
    const localOverride = localStorage.getItem("erclave-production-api-base-url") || "";
    const localRuntimeBaseUrl = getRuntimeConfigValue("localProductionApiBaseUrl");
    return getSafeLocalBaseUrl(localOverride || localRuntimeBaseUrl || runtimeBaseUrl, "http://127.0.0.1:8002");
  }
  return localStorage.getItem("erclave-production-api-base-url") || runtimeBaseUrl;
}

export function getInventoryApiBaseUrl() {
  const runtimeBaseUrl = getRuntimeConfigValue("inventoryApiBaseUrl") || "http://127.0.0.1:8004";
  if (isLocalPreviewHost()) {
    const override = localStorage.getItem("erclave-inventory-api-base-url") || "";
    const localBaseUrl = getRuntimeConfigValue("localInventoryApiBaseUrl");
    return getSafeLocalBaseUrl(override || localBaseUrl || runtimeBaseUrl, "http://127.0.0.1:8004");
  }
  return localStorage.getItem("erclave-inventory-api-base-url") || runtimeBaseUrl;
}

export function getHrApiBaseUrl() {
  const runtimeBaseUrl = getRuntimeConfigValue("hrApiBaseUrl") || "http://127.0.0.1:8006";
  if (isLocalPreviewHost()) {
    const override = localStorage.getItem("erclave-hr-api-base-url") || "";
    const localBaseUrl = getRuntimeConfigValue("localHrApiBaseUrl");
    return getSafeLocalBaseUrl(override || localBaseUrl || runtimeBaseUrl, "http://127.0.0.1:8006");
  }
  return localStorage.getItem("erclave-hr-api-base-url") || runtimeBaseUrl;
}


export function getDemoTenantId() {
  return localStorage.getItem("erclave-api-tenant-id") || getRuntimeConfigValue("tenantId") || DEFAULT_TENANT_ID;
}


export function getConfiguredTenantId() {
  return getRuntimeConfigValue("tenantId") || DEFAULT_TENANT_ID;
}


export function setActiveTenantId(tenantId) {
  if (tenantId) {
    localStorage.setItem("erclave-api-tenant-id", tenantId);
  } else {
    localStorage.removeItem("erclave-api-tenant-id");
  }
}


export function getDemoActorId() {
  return localStorage.getItem("erclave-api-actor-id") || getRuntimeConfigValue("actorId") || DEFAULT_ACTOR_ID;
}


export function getFirebaseConfig() {
  if (isLocalPreviewHost()) {
    const authMode = getRuntimeConfigValue("authMode") || "demo";
    if (authMode !== "firebase-emulator") return null;
    return window.ERCLAVE_CONFIG?.localFirebaseConfig || null;
  }
  return window.ERCLAVE_CONFIG?.firebaseConfig || null;
}

export function getFirebaseAuthEmulatorUrl() {
  if (!isLocalPreviewHost()) return "";
  const authMode = getRuntimeConfigValue("authMode") || "demo";
  if (authMode !== "firebase-emulator") return "";
  return getRuntimeConfigValue("firebaseAuthEmulatorUrl") || "http://127.0.0.1:9099";
}
