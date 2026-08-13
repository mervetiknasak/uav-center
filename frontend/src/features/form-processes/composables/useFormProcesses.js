import { ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";

export function useFormProcesses(apiFetch) {
  const records = ref([]);
  const processes = ref([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref("");
  const notice = ref("");

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      const [recordData, catalogData] = await Promise.all([
        apiFetch("/api/form-processes/"),
        apiFetch("/api/form-processes/templates/")
      ]);
      records.value = Array.isArray(recordData) ? recordData : [];
      processes.value = Array.isArray(catalogData) ? catalogData : [];
    } catch (err) {
      error.value = errorMessage(err, "Form süreçleri alınamadı");
    } finally {
      loading.value = false;
    }
  }

  async function save({ id, payload, done }) {
    saving.value = true;
    error.value = "";
    notice.value = "";
    try {
      const saved = await apiFetch(id ? `/api/form-processes/${id}/` : "/api/form-processes/", {
        method: id ? "PATCH" : "POST",
        body: JSON.stringify(payload)
      });
      records.value = id
        ? records.value.map((record) => (record.id === saved.id ? saved : record))
        : [saved, ...records.value];
      notice.value = `${saved.record_number} numaralı kayıt ${id ? "güncellendi" : "oluşturuldu"}.`;
      done?.();
    } catch (err) {
      error.value = errorMessage(err, "Form kaydı kaydedilemedi");
    } finally {
      saving.value = false;
    }
  }

  async function remove(record) {
    saving.value = true;
    error.value = "";
    notice.value = "";
    try {
      await apiFetch(`/api/form-processes/${record.id}/`, { method: "DELETE" });
      records.value = records.value.filter((item) => item.id !== record.id);
      notice.value = `${record.record_number} numaralı kayıt silindi.`;
    } catch (err) {
      error.value = errorMessage(err, "Form kaydı silinemedi");
    } finally {
      saving.value = false;
    }
  }

  return { records, processes, loading, saving, error, notice, load, save, remove };
}
