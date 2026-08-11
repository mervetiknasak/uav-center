import { ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useFlightPermits(apiFetch) {
  const permits = ref([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref("");
  const notice = ref("");

  async function loadPermits() {
    loading.value = true;
    error.value = "";
    try {
      const data = await apiFetch("/api/flight-permits/");
      permits.value = Array.isArray(data) ? data : [];
    } catch (err) {
      error.value = errorMessage(err, "Uçuş izinleri alınamadı");
    } finally {
      loading.value = false;
    }
  }

  async function savePermit({ id, payload, file, removeDocument, done }) {
    saving.value = true;
    error.value = "";
    notice.value = "";
    const formData = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== null && value !== undefined) formData.append(key, value);
    });
    if (file) formData.append("document", file, file.name);
    if (removeDocument) formData.append("remove_document", "true");

    try {
      const saved = await apiFetch(id ? `/api/flight-permits/${id}/` : "/api/flight-permits/", {
        method: id ? "PATCH" : "POST",
        body: formData
      });
      permits.value = id
        ? permits.value.map((permit) => (permit.id === saved.id ? saved : permit))
        : [saved, ...permits.value];
      notice.value = id
        ? `${saved.permit_number} numaralı izin güncellendi.`
        : `${saved.permit_number} numaralı izin oluşturuldu.`;
      done?.();
    } catch (err) {
      error.value = errorMessage(err, "Uçuş izni kaydedilemedi");
    } finally {
      saving.value = false;
    }
  }

  async function deletePermit(permit) {
    saving.value = true;
    error.value = "";
    notice.value = "";
    try {
      await apiFetch(`/api/flight-permits/${permit.id}/`, { method: "DELETE" });
      permits.value = permits.value.filter((item) => item.id !== permit.id);
      notice.value = `${permit.permit_number} numaralı izin silindi.`;
    } catch (err) {
      error.value = errorMessage(err, "Uçuş izni silinemedi");
    } finally {
      saving.value = false;
    }
  }

  function resetPermits() {
    permits.value = [];
    error.value = "";
    notice.value = "";
  }

  return {
    permits,
    loading,
    saving,
    error,
    notice,
    loadPermits,
    savePermit,
    deletePermit,
    resetPermits
  };
}
