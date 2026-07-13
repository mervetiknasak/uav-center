import { ref } from "vue";
import { errorMessage } from "./errorMessage";

const DEFAULT_PROMPT = "Bu belgeyi incele ve önemli bilgileri kısa maddeler halinde çıkar.";

export function useDocuments(apiFetch) {
  const documents = ref([]);
  const loading = ref(false);
  const uploadError = ref("");
  const activeDocument = ref(null);
  const prompt = ref(DEFAULT_PROMPT);
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
    if (!trimmedPrompt) {
      uploadError.value = "Belgeyi işlemek için prompt girin.";
      onError?.();
      return;
    }

    const formData = new FormData();
    formData.append("file", file.file);
    formData.append("prompt", trimmedPrompt);

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
    deletingDocumentId,
    loadDocuments,
    uploadDocument,
    openDocument,
    deleteDocument,
    resetDocuments
  };
}
