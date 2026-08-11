<script setup>
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import { useDocuments } from "../../../composables/useDocuments";
import DocumentProcessingView from "../../../views/DocumentProcessingView.vue";

const { api } = useAppContext();
const route = useRoute();
const documents = useDocuments(api.apiFetch);
const initialized = ref(false);

function requestedDocumentId() {
  const value = Number.parseInt(String(route.query.document || ""), 10);
  return Number.isInteger(value) && value > 0 ? value : null;
}

async function openRequestedDocument() {
  const documentId = requestedDocumentId();
  if (documentId) await documents.openDocument(documentId);
}

async function loadPage() {
  await Promise.all([documents.loadDocuments(), documents.loadControls()]);
  initialized.value = true;
  await openRequestedDocument();
}

watch(
  () => route.query.document,
  () => {
    if (initialized.value) openRequestedDocument();
  }
);

onMounted(loadPage);
</script>

<template>
  <DocumentProcessingView
    :documents="documents.documents.value"
    :loading="documents.loading.value"
    :prompt="documents.prompt.value"
    :use-ocr="documents.useOcr.value"
    :use-ai="documents.useAi.value"
    :upload-error="documents.uploadError.value"
    :upload-notice="documents.uploadNotice.value"
    :active-document="documents.activeDocument.value"
    :deleting-document-id="documents.deletingDocumentId.value"
    :controls="documents.controls.value"
    :selected-control-ids="documents.selectedControlIds.value"
    :rag-query="documents.ragQuery.value"
    :rag-result="documents.ragResult.value"
    :control-result="documents.controlResult.value"
    :analysis-loading="documents.analysisLoading.value"
    :controls-loading="documents.controlsLoading.value"
    :analysis-error="documents.analysisError.value"
    @update:prompt="documents.prompt.value = $event"
    @update:use-ocr="documents.useOcr.value = $event"
    @update:use-ai="documents.useAi.value = $event"
    @update:rag-query="documents.ragQuery.value = $event"
    @update:selected-control-ids="documents.selectedControlIds.value = $event"
    @upload="documents.uploadDocument"
    @open="documents.openDocument"
    @delete="documents.deleteDocument"
    @ask-document="documents.askDocument"
    @run-controls="documents.runControls"
    @save-control="documents.saveControl"
    @delete-control="documents.deleteControl"
  />
</template>
