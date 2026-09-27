import { ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";

export function useEdkApplicationDetail(apiFetch) {
  const application = ref(null);
  const loading = ref(false);
  const decisionLoading = ref(false);
  const parseLoading = ref(false);
  const publishLoading = ref(false);
  const trackingLoading = ref(false);
  const error = ref("");
  const parseResult = ref(null);
  const publishResult = ref(null);

  async function loadApplication(applicationId) {
    loading.value = true;
    error.value = "";
    try {
      application.value = await apiFetch(`/api/edk/applications/${applicationId}/`);
      return true;
    } catch (err) {
      error.value = errorMessage(err, "EDK başvuru detayı alınamadı");
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function decide(status, decisionNote = "") {
    if (!application.value) return false;
    decisionLoading.value = true;
    error.value = "";
    try {
      application.value = await apiFetch(
        `/api/edk/applications/${application.value.id}/decision/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status, decision_note: decisionNote })
        }
      );
      return true;
    } catch (err) {
      error.value = errorMessage(err, "EDK başvurusu karara bağlanamadı");
      return false;
    } finally {
      decisionLoading.value = false;
    }
  }

  async function parse({ file, onFinish, onError }) {
    if (!application.value) return;
    parseLoading.value = true;
    error.value = "";
    parseResult.value = null;
    publishResult.value = null;
    const formData = new FormData();
    formData.append("file", file);

    try {
      parseResult.value = await apiFetch(
        `/api/edk/applications/${application.value.id}/minutes/parse/`,
        { method: "POST", body: formData }
      );
      await loadApplication(application.value.id);
      onFinish?.();
    } catch (err) {
      error.value = errorMessage(err, "Toplantı tutanağı okunamadı");
      onError?.();
    } finally {
      parseLoading.value = false;
    }
  }

  async function publish(draft) {
    if (!application.value) return false;
    publishLoading.value = true;
    error.value = "";
    publishResult.value = null;
    try {
      publishResult.value = await apiFetch(
        `/api/edk/applications/${application.value.id}/jira/publish/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(draft)
        }
      );
      await loadApplication(application.value.id);
      return true;
    } catch (err) {
      error.value = errorMessage(err, "Jira aktarımı başarısız");
      return false;
    } finally {
      publishLoading.value = false;
    }
  }

  async function refreshJiraTracking() {
    if (!application.value?.jira_tracking) return false;
    trackingLoading.value = true;
    error.value = "";
    try {
      const tracking = await apiFetch(
        `/api/edk/applications/${application.value.id}/jira/refresh/`,
        { method: "POST" }
      );
      application.value = { ...application.value, jira_tracking: tracking };
      return true;
    } catch (err) {
      error.value = errorMessage(err, "Jira takip bilgisi yenilenemedi");
      return false;
    } finally {
      trackingLoading.value = false;
    }
  }

  return {
    application,
    loading,
    decisionLoading,
    parseLoading,
    publishLoading,
    trackingLoading,
    error,
    parseResult,
    publishResult,
    loadApplication,
    decide,
    parse,
    publish,
    refreshJiraTracking
  };
}
