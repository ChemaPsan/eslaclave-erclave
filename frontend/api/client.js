import { getApiBaseUrl } from "./config.js";
import { getAuthToken } from "../auth.js";

const API_REQUEST_TIMEOUT_MS = 15000;

export class ErclaveApiError extends Error {
  constructor(message, status, payload = null) {
    super(message);
    this.name = "ErclaveApiError";
    this.status = status;
    this.payload = payload;
  }
}

function getLocalFallbackUrl(url) {
  if (url.includes("://localhost:")) return url.replace("://localhost:", "://127.0.0.1:");
  if (url.includes("://127.0.0.1:")) return url.replace("://127.0.0.1:", "://localhost:");
  return "";
}

async function fetchApi(url, token, options) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, {
      ...options,
      signal: options.signal || controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {})
      }
    });
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function apiRequest(path, options = {}) {
  return apiRequestAt(getApiBaseUrl(), path, options, "Admin API");
}

export async function apiRequestAt(baseUrl, path, options = {}, apiLabel = "API") {
  const url = `${baseUrl}${path}`;
  const token = await getAuthToken();
  let response;
  try {
    response = await fetchApi(url, token, options);
  } catch (error) {
    const fallbackUrl = getLocalFallbackUrl(url);
    if (fallbackUrl) {
      try {
        response = await fetchApi(fallbackUrl, token, options);
      } catch (fallbackError) {
        throw new ErclaveApiError(`No se pudo conectar con ${apiLabel} en ${baseUrl}. Tambien se intento ${fallbackUrl}. Revisa que el servicio local este activo y que el navegador no tenga cache de la URL anterior.`, 0, {
          cause: error?.message || "fetch_failed",
          fallback_cause: fallbackError?.message || "fallback_fetch_failed",
          url,
          fallback_url: fallbackUrl
        });
      }
    } else {
      throw new ErclaveApiError(`No se pudo conectar con ${apiLabel} en ${baseUrl}. Revisa que el servicio local este activo y que el navegador no tenga cache de la URL anterior.`, 0, {
        cause: error?.message || "fetch_failed",
        url
      });
    }
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message || `API request failed with status ${response.status}`;
    throw new ErclaveApiError(message, response.status, payload);
  }

  return payload;
}
