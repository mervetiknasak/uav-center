import { ref } from "vue";
import { errorMessage } from "./errorMessage";

const DEFAULT_PROMPT = "Bu belgeyi incele ve önemli bilgileri kısa maddeler halinde çıkar.";
const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"];

export function useDocuments(apiFetch) {
  const documents = ref([]);
  const loading = ref(false);
  const uploadError = ref("");
  const activeDocument = ref(null);
  const prompt = ref(DEFAULT_PROMPT);
  const useOcr = ref(false);
  const useAi = ref(true);
  const deletingDocumentId = ref(null);

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
      activeDocument.value = await apiFetch("/api/documents/upload/", {
        method: "POST",
        body: formData
      });
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
    } catch {
      activeDocument.value = null;
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
    deletingDocumentId.value = null;
  }

  return {
    documents,
    loading,
    uploadError,
    activeDocument,
    prompt,
    useOcr,
    useAi,
    deletingDocumentId,
    loadDocuments,
    uploadDocument,
    openDocument,
    deleteDocument,
    resetDocuments
  };
}
