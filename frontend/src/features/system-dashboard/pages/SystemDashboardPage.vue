<script setup>
import { onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import { useAdminUsers } from "../../../composables/useAdminUsers";
import { useDocuments } from "../../../composables/useDocuments";
import { useSystemStatus } from "../../../composables/useSystemStatus";
import SystemView from "../../../views/SystemView.vue";

const { api, auth } = useAppContext();
const system = useSystemStatus(api.apiFetch);
const documents = useDocuments(api.apiFetch);
const adminUsers = useAdminUsers(api.apiFetch);

onMounted(() =>
  Promise.all([
    system.checkBackend(),
    documents.loadDocuments(),
    adminUsers.loadUsersIfAdmin(auth.currentUser.value)
  ])
);
</script>

<template>
  <SystemView
    :health="system.health.value"
    :api-status="system.apiStatus.value"
    :error="system.error.value"
    :loading="system.loading.value"
    :documents="documents.documents.value"
    :documents-loading="documents.loading.value"
    :admin-users="adminUsers.users.value"
    :admin-users-loading="adminUsers.loading.value"
    :admin-users-error="adminUsers.error.value"
    :current-user="auth.currentUser.value"
    :api-base-url="api.API_BASE_URL"
    @check-backend="system.checkBackend"
    @refresh-documents="documents.loadDocuments"
    @refresh-users="adminUsers.loadUsers"
  />
</template>
