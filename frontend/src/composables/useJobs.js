import { ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useJobs(apiFetch) {
  const jobs = ref([]);
  const loading = ref(false);
  const error = ref("");
  const cancellingId = ref(null);
  let pollTimer = null;
  let requestInFlight = false;
  let pollingController = null;
  let visibilityListenerRegistered = false;

  async function loadJobs({ silent = false, signal } = {}) {
    if (requestInFlight) return;
    requestInFlight = true;
    if (!silent) loading.value = true;
    try {
      jobs.value = await apiFetch("/api/jobs/?limit=200", { signal });
      error.value = "";
    } catch (err) {
      if (err?.name === "AbortError") return;
      error.value = errorMessage(err, "Joblar yüklenemedi");
    } finally {
      requestInFlight = false;
      if (!silent) loading.value = false;
    }
  }

  function clearPollTimer() {
    if (pollTimer) window.clearInterval(pollTimer);
    pollTimer = null;
  }

  function schedulePolling() {
    if (pollTimer || !pollingController || document.hidden) return;
    pollTimer = window.setInterval(
      () => loadJobs({ silent: true, signal: pollingController?.signal }),
      3000
    );
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      clearPollTimer();
      return;
    }
    loadJobs({ silent: true, signal: pollingController?.signal });
    schedulePolling();
  }

  function startPolling() {
    stopPolling();
    pollingController = new AbortController();
    document.addEventListener("visibilitychange", handleVisibilityChange);
    visibilityListenerRegistered = true;
    loadJobs({ signal: pollingController.signal });
    schedulePolling();
  }

  function stopPolling() {
    clearPollTimer();
    pollingController?.abort();
    pollingController = null;
    if (visibilityListenerRegistered) {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      visibilityListenerRegistered = false;
    }
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

  return {
    jobs,
    loading,
    error,
    cancellingId,
    loadJobs,
    startPolling,
    stopPolling,
    cancelJob,
    resetJobs
  };
}
