import { ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useJobs(apiFetch) {
  const jobs = ref([]);
  const loading = ref(false);
  const error = ref("");
  const cancellingId = ref(null);
  let pollTimer = null;
  let requestInFlight = false;

  async function loadJobs({ silent = false } = {}) {
    if (requestInFlight) return;
    requestInFlight = true;
    if (!silent) loading.value = true;
    try {
      jobs.value = await apiFetch("/api/jobs/?limit=200");
      error.value = "";
    } catch (err) {
      error.value = errorMessage(err, "Joblar yüklenemedi");
    } finally {
      requestInFlight = false;
      if (!silent) loading.value = false;
    }
  }

  function startPolling() {
    stopPolling();
    loadJobs();
    pollTimer = window.setInterval(() => loadJobs({ silent: true }), 3000);
  }

  function stopPolling() {
    if (pollTimer) window.clearInterval(pollTimer);
    pollTimer = null;
  }

  async function cancelJob(job) {
    cancellingId.value = job.id;
    try {
      await apiFetch(`/api/jobs/${job.id}/cancel/`, { method: "POST" });
      await loadJobs({ silent: true });
    } catch (err) {
      error.value = errorMessage(err, "Job iptal edilemedi");
    } finally {
      cancellingId.value = null;
    }
  }

  function resetJobs() {
    stopPolling();
    jobs.value = [];
    error.value = "";
    cancellingId.value = null;
  }

  return { jobs, loading, error, cancellingId, loadJobs, startPolling, stopPolling, cancelJob, resetJobs };
}
