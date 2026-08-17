import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, useApi } from "./useApi";

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useApi transport boundary", () => {
  it("deduplicates concurrent CSRF requests", async () => {
    const request = deferred();
    const fetchMock = vi.fn(() => request.promise);
    vi.stubGlobal("fetch", fetchMock);
    const { ensureCsrfToken } = useApi();

    const first = ensureCsrfToken();
    const second = ensureCsrfToken();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    request.resolve(jsonResponse({ csrfToken: "csrf-1" }));
    await expect(Promise.all([first, second])).resolves.toEqual(["csrf-1", "csrf-1"]);
    expect(fetchMock).toHaveBeenCalledWith("/api/auth/csrf/", { credentials: "include" });
  });

  it("adds CSRF and credential policy to unsafe methods", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: "csrf-safe" }))
      .mockResolvedValueOnce(jsonResponse({ saved: true }));
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = useApi();

    await expect(
      apiFetch("/api/resource/", {
        method: "post",
        headers: { "X-Request-ID": "request-1" },
        body: "{}"
      })
    ).resolves.toEqual({ saved: true });

    const [url, options] = fetchMock.mock.calls[1];
    expect(url).toBe("/api/resource/");
    expect(options.method).toBe("POST");
    expect(options.credentials).toBe("include");
    expect(options.headers).toBeInstanceOf(Headers);
    expect(options.headers.get("X-CSRFToken")).toBe("csrf-safe");
    expect(options.headers.get("X-Request-ID")).toBe("request-1");
    expect(options.headers.get("Content-Type")).toBe("application/json");
  });

  it("does not set a JSON content type for multipart form data", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: "csrf-form" }))
      .mockResolvedValueOnce(jsonResponse({ saved: true }));
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = useApi();

    await apiFetch("/api/upload/", { method: "POST", body: new FormData() });

    const options = fetchMock.mock.calls[1][1];
    expect(options.headers.get("Content-Type")).toBeNull();
    expect(options.headers.get("X-CSRFToken")).toBe("csrf-form");
  });

  it("does not let a stale CSRF generation overwrite a reset token", async () => {
    const oldRequest = deferred();
    const fetchMock = vi
      .fn()
      .mockImplementationOnce(() => oldRequest.promise)
      .mockResolvedValueOnce(jsonResponse({ csrfToken: "csrf-new" }));
    vi.stubGlobal("fetch", fetchMock);
    const { ensureCsrfToken, resetCsrfToken } = useApi();

    const oldToken = ensureCsrfToken();
    resetCsrfToken();
    const newToken = ensureCsrfToken();
    oldRequest.resolve(jsonResponse({ csrfToken: "csrf-old" }));

    await expect(oldToken).resolves.toBe("csrf-old");
    await expect(newToken).resolves.toBe("csrf-new");
    await expect(ensureCsrfToken()).resolves.toBe("csrf-new");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("aborts one waiter without cancelling the shared CSRF request", async () => {
    const request = deferred();
    const fetchMock = vi.fn(() => request.promise);
    vi.stubGlobal("fetch", fetchMock);
    const { ensureCsrfToken } = useApi();
    const controller = new AbortController();

    const shared = ensureCsrfToken();
    const waiter = ensureCsrfToken({ signal: controller.signal });
    controller.abort();

    await expect(waiter).rejects.toMatchObject({ name: "AbortError" });
    request.resolve(jsonResponse({ csrfToken: "csrf-shared" }));
    await expect(shared).resolves.toBe("csrf-shared");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("forwards AbortSignal to the resource request", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: "csrf-signal" }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = useApi();
    const controller = new AbortController();

    await apiFetch("/api/resource/", { method: "PATCH", signal: controller.signal });
    expect(fetchMock.mock.calls[1][1].signal).toBe(controller.signal);
  });

  it("preserves safe HTTP status and response data on API errors", async () => {
    const responseData = {
      detail: "Aynı bildirim isteği halen işleniyor.",
      notification: { status: "pending" }
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrfToken: "csrf-error" }))
      .mockResolvedValueOnce(jsonResponse(responseData, 409));
    vi.stubGlobal("fetch", fetchMock);
    const { apiFetch } = useApi();

    await expect(apiFetch("/api/resource/", { method: "POST" })).rejects.toMatchObject({
      name: "ApiError",
      status: 409,
      data: responseData
    });
    await expect(
      Promise.reject(new ApiError("Kontrollü hata", { status: 400 }))
    ).rejects.toBeInstanceOf(Error);
  });
});
