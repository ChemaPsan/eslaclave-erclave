import { getApiBaseUrl } from "./config.js";
import { getAuthToken } from "../auth.js";
import { MUTATION_FINISHED_EVENT, MUTATION_STARTED_EVENT } from "../utils/mutation-feedback.js";
import { getLocalizedErrorMessage } from "../i18n/api-errors.js";

const API_REQUEST_TIMEOUT_MS = 35000;

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

export async function apiRequest(path, options = {}) {
  return apiRequestAt(getApiBaseUrl(), path, options, "Admin API");
}

export async function apiRequestAt(baseUrl, path, options = {}, apiLabel = "API") {
  const method = String(options.method || "GET").toUpperCase();
  const isMutation = !["GET", "HEAD", "OPTIONS"].includes(method);
  const formRequest = { path, method, body: options.body, context: null };
  if (isMutation) window.dispatchEvent(new CustomEvent("erclave:form-request", { detail: formRequest }));
  if (isMutation) window.dispatchEvent(new CustomEvent(MUTATION_STARTED_EVENT));
  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => { timedOut = true; controller.abort(); }, API_REQUEST_TIMEOUT_MS);
  const cancel = () => controller.abort();
  options.signal?.addEventListener("abort", cancel, { once: true });
  if (options.signal?.aborted) cancel();
  const bounded = async (operation) => {
    if (controller.signal.aborted) throw new DOMException("Request aborted", "AbortError");
    let rejectAbort;
    const aborted = new Promise((_, reject) => { rejectAbort = () => reject(new DOMException("Request aborted", "AbortError")); });
    controller.signal.addEventListener("abort", rejectAbort, { once: true });
    try { return await Promise.race([operation(), aborted]); }
    finally { controller.signal.removeEventListener("abort", rejectAbort); }
  };
  try {
  const token = await bounded(() => getAuthToken());
  const response = await bounded(() => fetch(`${baseUrl}${path}`, {
    ...options,
    signal: controller.signal,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  }));

  const expectsBlob = options.responseType === "blob";
  const payload = expectsBlob && response.ok ? null : await bounded(() => response.json().catch(error => { if (error?.name === "AbortError") throw error; return null; }));
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
            details: { service: apiLabel, ...(payload.error.details || {}), api_service: apiLabel }
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

  if (expectsBlob) {
    if (response.status === 204) return { empty: true, blob: null, filename: "" };
    const disposition = response.headers.get("Content-Disposition") || "";
    const encodedFilename = disposition.match(/filename\*=UTF-8\'\'([^;]+)/i)?.[1];
    let filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || "report.csv";
    if(encodedFilename){try{filename=decodeURIComponent(encodedFilename);}catch{filename="attachment";}}
    return { empty: false, blob: await bounded(() => response.blob()), filename };
  }
  return payload;
  } catch (error) {
    if (!(error instanceof ErclaveApiError)) {
      error = new ErclaveApiError("Request could not be completed.", 0, null, {
        code: timedOut ? "request_timeout" : controller.signal.aborted ? "request_cancelled" : "network_unavailable",
        details: { service: apiLabel }
      });
    }
    if (formRequest.context && error && typeof error === "object") {
      error.formContext = formRequest.context;
      window.dispatchEvent(new CustomEvent("erclave:form-error", { detail: error }));
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    options.signal?.removeEventListener("abort", cancel);
    if (formRequest.context) window.dispatchEvent(new CustomEvent("erclave:form-complete", { detail: formRequest.context }));
    if (isMutation) window.dispatchEvent(new CustomEvent(MUTATION_FINISHED_EVENT));
  }
}

export async function apiDownloadAt(baseUrl, path, options = {}, apiLabel = "API") {
  return apiRequestAt(baseUrl, path, { ...options, method: "GET", responseType: "blob" }, apiLabel);
}
