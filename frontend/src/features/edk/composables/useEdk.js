import { ref } from "vue";
import { errorMessage } from "../../../composables/errorMessage";

export function useEdk(apiFetch) {
  const applications = ref([]);
  const applicationsLoading = ref(false);
  const applicationSubmitting = ref(false);
  const decisionLoadingId = ref(null);
  const parseLoading = ref(false);
  const publishLoading = ref(false);
  const error = ref("");
  const parseResult = ref(null);
  const publishResult = ref(null);

  async function loadApplications() {
    applicationsLoading.value = true;
    error.value = "";
    try {
      const data = await apiFetch("/api/edk/applications/");
      applications.value = Array.isArray(data) ? data : [];
    } catch (err) {
      error.value = errorMessage(err, "EDK başvuruları alınamadı");
    } finally {
      applicationsLoading.value = false;
    }
  }

  async function createApplication(application) {
    applicationSubmitting.value = true;
    error.value = "";
    const formData = new FormData();
    Object.entries(application).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") formData.append(key, value);
    });
    try {
      const created = await apiFetch("/api/edk/applications/", {
        method: "POST",
        body: formData
      });
      applications.value = [created, ...applications.value];
      return true;
    } catch (err) {
      error.value = errorMessage(err, "EDK başvurusu oluşturulamadı");
      return false;
    } finally {
      applicationSubmitting.value = false;
    }
  }

  async function decide(application, status, decisionNote = "") {
    decisionLoadingId.value = application.id;
    error.value = "";
    try {
      const updated = await apiFetch(`/api/edk/applications/${application.id}/decision/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status, decision_note: decisionNote })
      });
      applications.value = applications.value.map((item) =>
        item.id === updated.id ? updated : item
      );
      return true;
    } catch (err) {
      error.value = errorMessage(err, "EDK başvurusu karara bağlanamadı");
      return false;
    } finally {
      decisionLoadingId.value = null;
    }
  }

  async function parse({ applicationId, file, onFinish, onError }) {
    parseLoading.value = true;
    error.value = "";
    parseResult.value = null;
    publishResult.value = null;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const data = await apiFetch(`/api/edk/applications/${applicationId}/minutes/parse/`, {
        method: "POST",
        body: formData
      });
      parseResult.value = data;
      await loadApplications();
      onFinish?.();
    } catch (err) {
      error.value = errorMessage(err, "Word dosyası okunamadı");
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
    applications,
    applicationsLoading,
    applicationSubmitting,
    decisionLoadingId,
    parseLoading,
    publishLoading,
    error,
    parseResult,
    publishResult,
    loadApplications,
    createApplication,
    decide,
    parse,
    publish
  };
}
