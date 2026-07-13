import { computed, ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useSystemStatus(apiFetch) {
  const loading = ref(false);
  const error = ref("");
  const health = ref(null);

  const apiStatus = computed(() => {
    if (loading.value) return "Bağlantı kontrol ediliyor";
    if (error.value) return "Backend ulaşılamıyor";
    if (health.value?.status === "ok") return "Backend hazır";
    return "Henüz kontrol edilmedi";
  });

  async function checkBackend() {
    loading.value = true;
    error.value = "";

    try {
      health.value = await apiFetch("/api/health/");
    } catch (err) {
      health.value = null;
      error.value = errorMessage(err, "Bilinmeyen hata");
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, health, apiStatus, checkBackend };
}
