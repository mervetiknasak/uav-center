import { ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";

export function useEdkApplicationDetail(apiFetch) {
  const application = ref(null);
  const loading = ref(false);
  const decisionLoading = ref(false);
  const parseLoading = ref(false);
  const publishLoading = ref(false);
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
    publishLoading.value = true;
    error.value = "";
    publishResult.value = null;
    try {
      publishResult.value = await apiFetch("/api/edk/jira/publish/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft)
      });
    } catch (err) {
      error.value = errorMessage(err, "Jira aktarımı başarısız");
    } finally {
      publishLoading.value = false;
    }
  }

  return {
    application,
    loading,
    decisionLoading,
    parseLoading,
    publishLoading,
    error,
    parseResult,
    publishResult,
    loadApplication,
    decide,
    parse,
    publish
  };
}
