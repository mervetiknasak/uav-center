import { ref } from "vue";
import { errorMessage } from "./errorMessage";

export function useWordToJira(apiFetch) {
  const parseLoading = ref(false);
  const publishLoading = ref(false);
  const error = ref("");
  const parseResult = ref(null);
  const publishResult = ref(null);

  async function parse({ file, onFinish, onError }) {
    parseLoading.value = true;
    error.value = "";
    parseResult.value = null;
    publishResult.value = null;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const data = await apiFetch("/api/word-to-jira/parse/", { method: "POST", body: formData });
      parseResult.value = data;
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
      publishResult.value = await apiFetch("/api/word-to-jira/publish/", {
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

  return { parseLoading, publishLoading, error, parseResult, publishResult, parse, publish };
}
