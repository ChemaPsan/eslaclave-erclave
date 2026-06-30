import { getApiBaseUrl } from "./config.js";


export class ErclaveApiError extends Error {
  constructor(message, status, payload = null) {
    super(message);
    this.name = "ErclaveApiError";
    this.status = status;
    this.payload = payload;
  }
}


export async function apiRequest(path, options = {}) {
  const url = `${getApiBaseUrl()}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message || `API request failed with status ${response.status}`;
    throw new ErclaveApiError(message, response.status, payload);
  }

  return payload;
}
