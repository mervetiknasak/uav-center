import { ref } from "vue";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

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
    const firstMessage = Object.values(data).flat().find((message) => typeof message === "string");
    if (firstMessage) return firstMessage;
  }
  return fallback;
}

export function useApi() {
  const csrfToken = ref("");

  function apiUrl(path) {
    return `${API_BASE_URL}${path}`;
  }

  async function ensureCsrfToken() {
    if (csrfToken.value) return csrfToken.value;

    const response = await fetch(apiUrl("/api/auth/csrf/"), { credentials: "include" });
    const data = await readResponse(response);
    if (!response.ok) {
      throw new Error(responseError(data, `CSRF hazırlanamadı: HTTP ${response.status}`));
    }

    csrfToken.value = data.csrfToken;
    return csrfToken.value;
  }

  async function apiFetch(path, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = new Headers(options.headers || {});
    if (!SAFE_METHODS.has(method)) {
      headers.set("X-CSRFToken", await ensureCsrfToken());
    }

    const response = await fetch(apiUrl(path), {
      ...options,
      method,
      credentials: "include",
      headers
    });
    const data = await readResponse(response);
    if (!response.ok) throw new Error(responseError(data, `HTTP ${response.status}`));
    return data;
  }

  function resetCsrfToken() {
    csrfToken.value = "";
  }

  return { API_BASE_URL, apiFetch, ensureCsrfToken, resetCsrfToken };
}
