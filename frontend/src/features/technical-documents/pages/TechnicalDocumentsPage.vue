<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import { useOrganizationProjects } from "../../../composables/useOrganizationProjects";
import TechnicalDocumentsScreen from "../components/TechnicalDocumentsScreen.vue";
import { useTechnicalDocuments } from "../composables/useTechnicalDocuments";

const { api, auth } = useAppContext();
const route = useRoute();
const organizationProjects = useOrganizationProjects(api.apiFetch);
const technicalDocuments = useTechnicalDocuments(api.apiFetch);
const canEdit = computed(() => Boolean(auth.currentUser.value?.is_staff));
const deepLinkReady = ref(false);
const deepLinkRequested = computed(() => route.query.document != null);
const deepLinkDocumentId = computed(() => {
  const rawValue = Array.isArray(route.query.document)
    ? route.query.document[0]
    : route.query.document;
  if (!/^\d+$/.test(String(rawValue || ""))) return null;
  const value = Number(rawValue);
  return value > 0 ? value : null;
});
const deepLinkAction = computed(() => (route.query.action === "notify" ? "notify" : "detail"));

async function loadPage() {
  deepLinkReady.value = false;
  try {
    await Promise.all([organizationProjects.loadProjects(), technicalDocuments.loadDocuments()]);
  } finally {
    deepLinkReady.value = true;
  }
}

onMounted(loadPage);
</script>

<template>
  <TechnicalDocumentsScreen
    :projects="organizationProjects.projects.value"
    :documents="technicalDocuments.documents.value"
    :loading="organizationProjects.loading.value || technicalDocuments.loading.value"
    :saving="technicalDocuments.saving.value"
    :notifying-id="technicalDocuments.notifyingId.value"
    :error="organizationProjects.error.value || technicalDocuments.error.value"
    :notice="technicalDocuments.notice.value"
    :can-edit="canEdit"
    :deep-link-ready="deepLinkReady"
    :deep-link-requested="deepLinkRequested"
    :deep-link-document-id="deepLinkDocumentId"
    :deep-link-action="deepLinkAction"
    @refresh="loadPage"
    @save="technicalDocuments.saveDocument"
    @delete="technicalDocuments.deleteDocument"
    @notify="technicalDocuments.notifyDocument"
  />
</template>
