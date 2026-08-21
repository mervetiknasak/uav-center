import { ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";
import { normalizeOperationalAlertsPayload } from "../model/alerts";

const EMPTY_PAYLOAD = Object.freeze({
  as_of: "",
  thresholds: { critical_days: 7, horizon_days: 30, stale_days: 14 },
  summary: { total: 0, overdue: 0, next_7_days: 0, next_30_days: 0, stale: 0 },
  alerts: []
});

export function useOperationalAlerts(apiFetch) {
  const data = ref(normalizeOperationalAlertsPayload(EMPTY_PAYLOAD));
  const loading = ref(false);
  const error = ref("");

  async function loadAlerts() {
    loading.value = true;
    error.value = "";
    try {
      data.value = normalizeOperationalAlertsPayload(await apiFetch("/api/operational-alerts/"));
    } catch (err) {
      error.value = errorMessage(err, "Operasyonel uyarılar alınamadı");
    } finally {
      loading.value = false;
    }
  }

  return { data, loading, error, loadAlerts };
}
