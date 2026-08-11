import { ref } from "vue";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

export class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function readResponse(response) {
  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function responseError(data, fallback) {
  if (!data) return fallback;
  if (typeof data === "string") return data || fallback;
  if (data.detail) return data.detail;
  if (data.non_field_errors?.length) return data.non_field_errors.join(" ");

  const knownFields = ["username", "email", "password", "password_confirm", "file"];
  for (const field of knownFields) {
    if (data[field]?.length) return data[field].join(" ");
  }

  if (data.error_message) return data.error_message;
  if (typeof data === "object") {
    const firstMessage = Object.values(data)
      .flat()
      .find((message) => typeof message === "string");
    if (firstMessage) return firstMessage;
  }
  return fallback;
}

export function useApi() {
  const csrfToken = ref("");
  let csrfRequest = null;
  let csrfGeneration = 0;

  function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
  }

  function abortError(signal) {
    return signal?.reason instanceof Error
      ? signal.reason
      : new DOMException("İstek iptal edildi.", "AbortError");
  }

  function waitForRequest(request, signal) {
    if (!signal) return request;
    if (signal.aborted) return Promise.reject(abortError(signal));

    return new Promise((resolve, reject) => {
      const onAbort = () => {
        cleanup();
        reject(abortError(signal));
      };
      const cleanup = () => signal.removeEventListener("abort", onAbort);

      signal.addEventListener("abort", onAbort, { once: true });
      request.then(
        (value) => {
          cleanup();
          resolve(value);
        },
        (error) => {
          cleanup();
          reject(error);
        }
      );
    });
  }

  function startCsrfRequest() {
    const generation = csrfGeneration;
    const request = (async () => {
      const response = await fetch(apiUrl("/api/auth/csrf/"), { credentials: "include" });
      const data = await readResponse(response);
      if (!response.ok) {
        throw new Error(responseError(data, `CSRF hazırlanamadı: HTTP ${response.status}`));
      }

      if (generation === csrfGeneration) csrfToken.value = data.csrfToken;
      return data.csrfToken;
    })();
    const trackedRequest = request.finally(() => {
      if (csrfRequest === trackedRequest) csrfRequest = null;
    });
    csrfRequest = trackedRequest;
    return trackedRequest;
  }

  async function ensureCsrfToken({ signal } = {}) {
    if (csrfToken.value) return csrfToken.value;
    return waitForRequest(csrfRequest || startCsrfRequest(), signal);
  }

  async function apiFetch(path, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = new Headers(options.headers || {});
    const signal = options.signal;
    if (!SAFE_METHODS.has(method)) {
      headers.set("X-CSRFToken", await ensureCsrfToken({ signal }));
    }
    if (signal?.aborted) throw abortError(signal);

    const response = await fetch(apiUrl(path), {
      ...options,
      method,
      credentials: "include",
      headers
    });
    const data = await readResponse(response);
    if (!response.ok) {
      throw new ApiError(responseError(data, `HTTP ${response.status}`), {
        status: response.status,
        data
      });
    }
    return data;
  }

  function resetCsrfToken() {
    csrfGeneration += 1;
    csrfToken.value = "";
    csrfRequest = null;
  }

  return { API_BASE_URL, apiFetch, ensureCsrfToken, resetCsrfToken };
}
