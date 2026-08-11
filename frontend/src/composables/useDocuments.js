import { ref } from "vue";
import { errorMessage } from "./errorMessage";

const DEFAULT_PROMPT = "Bu belgeyi incele ve önemli bilgileri kısa maddeler halinde çıkar.";
const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"];

export function useDocuments(apiFetch) {
  const documents = ref([]);
  const loading = ref(false);
  const uploadError = ref("");
  const uploadNotice = ref("");
  const activeDocument = ref(null);
  const prompt = ref(DEFAULT_PROMPT);
  const useOcr = ref(false);
  const useAi = ref(true);
  const deletingDocumentId = ref(null);
  const controls = ref([]);
  const selectedControlIds = ref([]);
  const ragQuery = ref("");
  const ragResult = ref(null);
  const controlResult = ref(null);
  const analysisLoading = ref(false);
  const controlsLoading = ref(false);
  const analysisError = ref("");

  async function loadDocuments() {
    loading.value = true;
    try {
      const data = await apiFetch("/api/documents/");
      documents.value = Array.isArray(data) ? data : [];
    } finally {
      loading.value = false;
    }
  }

  async function uploadDocument({ file, onFinish, onError }) {
    uploadError.value = "";
    uploadNotice.value = "";
    const trimmedPrompt = prompt.value.trim();
    const fileName = file.file?.name?.toLowerCase() || "";
    const isImage = IMAGE_EXTENSIONS.some((extension) => fileName.endsWith(extension));
    if (useAi.value && !trimmedPrompt) {
      uploadError.value = "Belgeyi işlemek için prompt girin.";
      onError?.();
      return;
    }
    if (isImage && !useOcr.value) {
      uploadError.value = "Resim dosyalarından metin çıkarmak için OCR seçeneğini etkinleştirin.";
      onError?.();
      return;
    }

    const formData = new FormData();
    formData.append("file", file.file);
    formData.append("prompt", trimmedPrompt);
    formData.append("use_ocr", String(useOcr.value));
    formData.append("use_ai", String(useAi.value));

    try {
      const response = await apiFetch("/api/documents/upload/", {
        method: "POST",
        body: formData
      });
      activeDocument.value = response.document;
      uploadNotice.value = `Belge sıraya alındı. Job ${response.job.id.slice(0, 8)} arka planda çalışacak.`;
      await loadDocuments();
      onFinish?.();
    } catch (err) {
      uploadError.value = errorMessage(err, "Dosya yüklenemedi");
      onError?.();
    }
  }

  async function openDocument(documentId) {
    try {
      activeDocument.value = await apiFetch(`/api/documents/${documentId}/`);
      ragResult.value = null;
      controlResult.value = null;
      analysisError.value = "";
    } catch {
      activeDocument.value = null;
    }
  }

  async function loadControls() {
    controlsLoading.value = true;
    try {
      const firstLoad = controls.value.length === 0;
      controls.value = await apiFetch("/api/analysis-controls/");
      const available = new Set(
        controls.value.filter((item) => item.is_active).map((item) => item.id)
      );
      selectedControlIds.value = firstLoad
        ? controls.value
            .filter((item) => item.kind === "system" && item.is_active)
            .map((item) => item.id)
        : selectedControlIds.value.filter((id) => available.has(id));
    } finally {
      controlsLoading.value = false;
    }
  }

  async function askDocument() {
    const query = ragQuery.value.trim();
    if (!activeDocument.value || !query) return;
    analysisLoading.value = true;
    analysisError.value = "";
    try {
      const run = await apiFetch(`/api/documents/${activeDocument.value.id}/rag/query/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
      });
      ragResult.value = run.result;
    } catch (err) {
      analysisError.value = errorMessage(err, "RAG sorgusu çalıştırılamadı");
    } finally {
      analysisLoading.value = false;
    }
  }

  async function runControls() {
    if (!activeDocument.value) return;
    analysisLoading.value = true;
    analysisError.value = "";
    try {
      const run = await apiFetch(`/api/documents/${activeDocument.value.id}/controls/run/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ control_ids: selectedControlIds.value })
      });
      controlResult.value = run.result;
    } catch (err) {
      analysisError.value = errorMessage(err, "Kontroller çalıştırılamadı");
    } finally {
      analysisLoading.value = false;
    }
  }

  async function saveControl(payload) {
    const databaseId = payload.database_id;
    const url = databaseId ? `/api/analysis-controls/${databaseId}/` : "/api/analysis-controls/";
    analysisError.value = "";
    try {
      await apiFetch(url, {
        method: databaseId ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      await loadControls();
    } catch (err) {
      analysisError.value = errorMessage(err, "Kontrol kaydedilemedi");
    }
  }

  async function deleteControl(control) {
    if (!control.database_id || !window.confirm(`${control.name} kontrolü silinsin mi?`)) return;
    analysisError.value = "";
    try {
      await apiFetch(`/api/analysis-controls/${control.database_id}/`, { method: "DELETE" });
      selectedControlIds.value = selectedControlIds.value.filter((id) => id !== control.id);
      await loadControls();
    } catch (err) {
      analysisError.value = errorMessage(err, "Kontrol silinemedi");
    }
  }

  async function deleteDocument(document) {
    if (!window.confirm(`${document.original_name} silinsin mi?`)) return;

    deletingDocumentId.value = document.id;
    try {
      await apiFetch(`/api/documents/${document.id}/`, { method: "DELETE" });
      if (activeDocument.value?.id === document.id) activeDocument.value = null;
      await loadDocuments();
    } catch (err) {
      uploadError.value = errorMessage(err, "Belge silinemedi");
    } finally {
      deletingDocumentId.value = null;
    }
  }

  function resetDocuments() {
    documents.value = [];
    activeDocument.value = null;
    uploadError.value = "";
    uploadNotice.value = "";
    deletingDocumentId.value = null;
    controls.value = [];
    selectedControlIds.value = [];
    ragQuery.value = "";
    ragResult.value = null;
    controlResult.value = null;
    analysisError.value = "";
  }

  return {
    documents,
    loading,
    uploadError,
    uploadNotice,
    activeDocument,
    prompt,
    useOcr,
    useAi,
    deletingDocumentId,
    controls,
    selectedControlIds,
    ragQuery,
    ragResult,
    controlResult,
    analysisLoading,
    controlsLoading,
    analysisError,
    loadDocuments,
    uploadDocument,
    openDocument,
    deleteDocument,
    loadControls,
    askDocument,
    runControls,
    saveControl,
    deleteControl,
    resetDocuments
  };
}
