import { describe, expect, it, vi } from "vitest";

import { useTechnicalDocuments } from "./useTechnicalDocuments";

describe("technical document notification transport", () => {
  it("uses one request-scoped idempotency key for a delivery attempt", async () => {
    const apiFetch = vi.fn().mockResolvedValue({
      message: "Bildirim gönderildi.",
      document: { id: 42, code: "TPL-NOTIFY-1" }
    });
    const done = vi.fn();
    const documents = useTechnicalDocuments(apiFetch);

    await documents.notifyDocument({
      document: { id: 42, code: "TPL-NOTIFY-1" },
      payload: { message: "İnceleme için bilginize." },
      done
    });

    const [path, options] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/technical-documents/42/notify/");
    expect(options.headers["Idempotency-Key"]).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
    );
    expect(done).toHaveBeenCalledOnce();
  });

  it("reuses the same key when an ambiguous transport failure is retried", async () => {
    const apiFetch = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("network unavailable"))
      .mockResolvedValueOnce({
        message: "Mevcut sonuç döndürüldü.",
        document: { id: 42, code: "TPL-NOTIFY-1" }
      });
    const documents = useTechnicalDocuments(apiFetch);
    const request = {
      document: { id: 42, code: "TPL-NOTIFY-1" },
      payload: { subject: "İnceleme", message: "Bilginize." }
    };

    await documents.notifyDocument(request);
    await documents.notifyDocument(request);

    expect(apiFetch.mock.calls[1][1].headers["Idempotency-Key"]).toBe(
      apiFetch.mock.calls[0][1].headers["Idempotency-Key"]
    );
  });

  it("uses a new key after the backend records a failed delivery", async () => {
    const recordedFailure = Object.assign(new Error("E-posta gönderilemedi."), {
      status: 502,
      data: { notification: { status: "failed" } }
    });
    const apiFetch = vi
      .fn()
      .mockRejectedValueOnce(recordedFailure)
      .mockResolvedValueOnce({
        message: "Bildirim gönderildi.",
        document: { id: 42, code: "TPL-NOTIFY-1" }
      });
    const documents = useTechnicalDocuments(apiFetch);
    const request = {
      document: { id: 42, code: "TPL-NOTIFY-1" },
      payload: { message: "Bilginize." }
    };

    await documents.notifyDocument(request);
    await documents.notifyDocument(request);

    expect(apiFetch.mock.calls[1][1].headers["Idempotency-Key"]).not.toBe(
      apiFetch.mock.calls[0][1].headers["Idempotency-Key"]
    );
  });

  it("starts a new attempt when the notification payload changes", async () => {
    const apiFetch = vi.fn().mockRejectedValue(new TypeError("network unavailable"));
    const documents = useTechnicalDocuments(apiFetch);
    const document = { id: 42, code: "TPL-NOTIFY-1" };

    await documents.notifyDocument({ document, payload: { message: "İlk mesaj" } });
    await documents.notifyDocument({ document, payload: { message: "Yeni mesaj" } });

    expect(apiFetch.mock.calls[1][1].headers["Idempotency-Key"]).not.toBe(
      apiFetch.mock.calls[0][1].headers["Idempotency-Key"]
    );
  });
});
