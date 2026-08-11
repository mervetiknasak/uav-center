import { ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";

export function useTechnicalDocuments(apiFetch) {
  const documents = ref([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref("");
  const notice = ref("");
  const notifyingId = ref(null);
  const notificationAttempts = new Map();

  function notificationFingerprint(document, payload) {
    return JSON.stringify([
      document.id,
      String(payload.subject || ""),
      String(payload.message || "")
    ]);
  }

  function notificationAttempt(document, payload) {
    const fingerprint = notificationFingerprint(document, payload);
    const current = notificationAttempts.get(document.id);
    if (current?.fingerprint === fingerprint) return current;

    const attempt = { fingerprint, key: crypto.randomUUID() };
    notificationAttempts.set(document.id, attempt);
    return attempt;
  }

  function shouldRetainNotificationAttempt(err) {
    const recordedFailure = err?.status === 502 && err?.data?.notification?.status === "failed";
    if (recordedFailure) return false;
    return !Number.isInteger(err?.status) || err.status === 409 || err.status >= 500;
  }

  async function loadDocuments() {
    loading.value = true;
    error.value = "";
    try {
      const data = await apiFetch("/api/technical-documents/");
      documents.value = Array.isArray(data) ? data : [];
    } catch (err) {
      error.value = errorMessage(err, "Teknik dokümanlar alınamadı");
    } finally {
      loading.value = false;
    }
  }

  async function saveDocument({ id, payload, done }) {
    saving.value = true;
    error.value = "";
    notice.value = "";
    try {
      const updated = await apiFetch(
        id ? `/api/technical-documents/${id}/` : "/api/technical-documents/",
        {
          method: id ? "PATCH" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }
      );
      documents.value = id
        ? documents.value.map((document) => (document.id === updated.id ? updated : document))
        : [updated, ...documents.value];
      notice.value = id
        ? `${updated.code} güncellendi.`
        : `${updated.code} teknik dokümanı oluşturuldu.`;
      done?.();
    } catch (err) {
      error.value = errorMessage(err, "Teknik doküman kaydedilemedi");
    } finally {
      saving.value = false;
    }
  }

  async function deleteDocument(document) {
    saving.value = true;
    error.value = "";
    notice.value = "";
    try {
      await apiFetch(`/api/technical-documents/${document.id}/`, { method: "DELETE" });
      documents.value = documents.value.filter((item) => item.id !== document.id);
      notice.value = `${document.code} silindi.`;
    } catch (err) {
      error.value = errorMessage(err, "Teknik doküman silinemedi");
    } finally {
      saving.value = false;
    }
  }

  async function notifyDocument({ document, payload, done }) {
    const attempt = notificationAttempt(document, payload);
    notifyingId.value = document.id;
    error.value = "";
    notice.value = "";
    try {
      const data = await apiFetch(`/api/technical-documents/${document.id}/notify/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": attempt.key
        },
        body: JSON.stringify(payload)
      });
      documents.value = documents.value.map((item) =>
        item.id === data.document.id ? data.document : item
      );
      notice.value = data.message;
      notificationAttempts.delete(document.id);
      done?.();
    } catch (err) {
      if (!shouldRetainNotificationAttempt(err)) {
        notificationAttempts.delete(document.id);
      }
      error.value = errorMessage(err, "Panel sorumlularına e-posta gönderilemedi");
    } finally {
      notifyingId.value = null;
    }
  }

  function resetDocuments() {
    documents.value = [];
    error.value = "";
    notice.value = "";
    notifyingId.value = null;
    notificationAttempts.clear();
  }

  return {
    documents,
    loading,
    saving,
    error,
    notice,
    notifyingId,
    loadDocuments,
    saveDocument,
    deleteDocument,
    notifyDocument,
    resetDocuments
  };
}
