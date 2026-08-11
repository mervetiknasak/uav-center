<script setup>
import { computed, onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import { useOrganizationProjects } from "../../../composables/useOrganizationProjects";
import TechnicalDocumentsScreen from "../components/TechnicalDocumentsScreen.vue";
import { useTechnicalDocuments } from "../composables/useTechnicalDocuments";

const { api, auth } = useAppContext();
const organizationProjects = useOrganizationProjects(api.apiFetch);
const technicalDocuments = useTechnicalDocuments(api.apiFetch);
const canEdit = computed(() => Boolean(auth.currentUser.value?.is_staff));

function loadPage() {
  return Promise.all([organizationProjects.loadProjects(), technicalDocuments.loadDocuments()]);
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
    @refresh="loadPage"
    @save="technicalDocuments.saveDocument"
    @delete="technicalDocuments.deleteDocument"
    @notify="technicalDocuments.notifyDocument"
  />
</template>
