import { getApiBaseUrl } from "./config.js";
import { getAuthToken } from "../auth.js";
import { MUTATION_FINISHED_EVENT, MUTATION_STARTED_EVENT } from "../utils/mutation-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";

const API_REQUEST_TIMEOUT_MS = 15000;

export class ErclaveApiError extends Error {
  constructor(serverMessage, status, payload = null, metadata = {}) {
    const code = String(payload?.error?.code || metadata.code || "request_failed");
    const correlationId = String(payload?.error?.correlation_id || metadata.correlationId || "");
    const details = payload?.error?.details || metadata.details || {};
    const diagnostic = { name: "ErclaveApiError", status, payload, code, correlationId, details };
    super(getLocalizedErrorMessage(diagnostic, { lang: globalThis.localStorage?.getItem("erclave-lang") || "es", service: details.service }));
    this.name = "ErclaveApiError";
    this.status = status;
    this.payload = payload;
    this.code = code;
    this.correlationId = correlationId;
    this.details = details;
    this.serverMessage = String(serverMessage || "");
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
  const method = String(options.method || "GET").toUpperCase();
  const isMutation = !["GET", "HEAD", "OPTIONS"].includes(method);
  if (isMutation) window.dispatchEvent(new CustomEvent(MUTATION_STARTED_EVENT));
  try {
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
        throw new ErclaveApiError("Network request and local fallback failed.", 0, {
          error: {
            code: error?.name === "AbortError" || fallbackError?.name === "AbortError" ? "request_timeout" : "network_unavailable",
            message: "The API could not be reached.",
            correlation_id: "",
            details: { service: apiLabel, cause: error?.message || "fetch_failed", fallback_cause: fallbackError?.message || "fallback_fetch_failed", url, fallback_url: fallbackUrl }
          }
        });
      }
    } else {
      throw new ErclaveApiError("Network request failed.", 0, {
        error: {
          code: error?.name === "AbortError" ? "request_timeout" : "network_unavailable",
          message: "The API could not be reached.",
          correlation_id: "",
          details: { service: apiLabel, cause: error?.message || "fetch_failed", url }
        }
      });
    }
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const responseCorrelationId = response.headers.get("X-Correlation-Id") || "";
    const fallbackCode = ({
      401: "auth_required",
      403: "permission_denied",
      404: "record_not_found",
      409: "operation_conflict",
      422: "validation_failed",
      429: "rate_limit_exceeded"
    })[response.status] || (response.status >= 500 ? "service_unavailable" : "request_failed");
    const normalizedPayload = payload?.error
      ? {
          ...payload,
          error: {
            ...payload.error,
            correlation_id: payload.error.correlation_id || responseCorrelationId,
            details: { ...(payload.error.details || {}), service: apiLabel }
          }
        }
      : {
          error: {
            code: fallbackCode,
            message: typeof payload?.detail === "string" ? payload.detail : "The request was rejected.",
            correlation_id: responseCorrelationId,
            details: { service: apiLabel, issues: Array.isArray(payload?.detail) ? payload.detail : [] }
          }
        };
    throw new ErclaveApiError(normalizedPayload.error.message, response.status, normalizedPayload);
  }

  return payload;
  } finally {
    if (isMutation) window.dispatchEvent(new CustomEvent(MUTATION_FINISHED_EVENT));
  }
}
