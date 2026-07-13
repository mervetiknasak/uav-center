<script setup>
import { computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppSidebar from "./components/AppSidebar.vue";
import AuthPanel from "./components/AuthPanel.vue";
import { useAdminUsers } from "./composables/useAdminUsers";
import { useApi } from "./composables/useApi";
import { useAuth } from "./composables/useAuth";
import { useDocuments } from "./composables/useDocuments";
import { useOrganization } from "./composables/useOrganization";
import { useSystemStatus } from "./composables/useSystemStatus";
import { useTechnicalDocuments } from "./composables/useTechnicalDocuments";
import { useWordToJira } from "./composables/useWordToJira";
import { DEFAULT_ROUTE_NAME, menuSections } from "./router";

const { API_BASE_URL, apiFetch, ensureCsrfToken, resetCsrfToken } = useApi();
const route = useRoute();
const router = useRouter();

const system = useSystemStatus(apiFetch);
const documentStore = useDocuments(apiFetch);
const admin = useAdminUsers(apiFetch);
const organization = useOrganization(apiFetch);
const technical = useTechnicalDocuments(apiFetch);
const wordToJira = useWordToJira(apiFetch);
const auth = useAuth({
  apiFetch,
  ensureCsrfToken,
  resetCsrfToken,
  onLogout: () => {
    documentStore.resetDocuments();
    admin.resetUsers();
    organization.resetOrganization();
    technical.resetDocuments();
  }
});

const activeMenuKey = computed(() => route.meta.menuKey || DEFAULT_ROUTE_NAME);
const menuOptions = computed(() =>
  menuSections.filter((section) => !section.requiresAdmin || auth.currentUser.value?.is_staff)
);

async function loadRouteData(key) {
  if (key === "system-dashboard") {
    await Promise.all([
      system.checkBackend(),
      documentStore.loadDocuments(),
      admin.loadUsersIfAdmin(auth.currentUser.value)
    ]);
    return;
  }
  if (key === "users") {
    await admin.loadUsersIfAdmin(auth.currentUser.value);
    return;
  }
  if (key === "technical-documents") {
    await Promise.all([organization.loadOrganization(), technical.loadDocuments()]);
    return;
  }
  if (key === "organization-projects" || key === "organization-admin") {
    await organization.loadOrganization();
    return;
  }
  if (key === "documents" || key === "results") await documentStore.loadDocuments();
}

function handleMenuUpdate(key) {
  router.push({ name: key });
}

const routeProps = computed(() => {
  switch (route.name) {
    case "technical-documents":
      return {
        projects: organization.projects.value,
        documents: technical.documents.value,
        loading: technical.loading.value,
        saving: technical.saving.value,
        notifyingId: technical.notifyingId.value,
        error: technical.error.value,
        notice: technical.notice.value,
        canEdit: auth.currentUser.value?.is_staff
      };
    case "organization-projects":
    case "organization-admin":
      return {
        projects: organization.projects.value,
        personGroups: organization.personGroups.value,
        loading: organization.loading.value,
        saving: organization.saving.value,
        error: organization.error.value,
        canEdit: route.name === "organization-admin" && auth.currentUser.value?.is_staff
      };
    case "users":
      return {
        users: admin.users.value,
        loading: admin.loading.value,
        error: admin.error.value,
        updatingUserId: admin.updatingUserId.value
      };
    case "system-dashboard":
      return {
        health: system.health.value,
        apiStatus: system.apiStatus.value,
        error: system.error.value,
        loading: system.loading.value,
        documents: documentStore.documents.value,
        documentsLoading: documentStore.loading.value,
        adminUsers: admin.users.value,
        adminUsersLoading: admin.loading.value,
        adminUsersError: admin.error.value,
        currentUser: auth.currentUser.value,
        apiBaseUrl: API_BASE_URL
      };
    case "word-to-jira":
      return {
        loading: wordToJira.parseLoading.value,
        publishing: wordToJira.publishLoading.value,
        error: wordToJira.error.value,
        result: wordToJira.parseResult.value,
        publishResult: wordToJira.publishResult.value
      };
    default:
      return {
        prompt: documentStore.prompt.value,
        documents: documentStore.documents.value,
        loading: documentStore.loading.value,
        uploadError: documentStore.uploadError.value,
        activeDocument: documentStore.activeDocument.value,
        deletingDocumentId: documentStore.deletingDocumentId.value
      };
  }
});

const routeListeners = computed(() => {
  switch (route.name) {
    case "technical-documents":
      return {
        refresh: technical.loadDocuments,
        save: technical.saveDocument,
        delete: technical.deleteDocument,
        notify: technical.notifyDocument
      };
    case "organization-projects":
    case "organization-admin":
      return {
        refresh: organization.loadOrganization,
        save: organization.saveItem,
        delete: organization.deleteItem,
        "reorder-responsibles": organization.reorderResponsibles
      };
    case "users":
      return { refresh: admin.loadUsers, "update-status": admin.updateUserStatus };
    case "system-dashboard":
      return {
        "check-backend": system.checkBackend,
        "refresh-documents": documentStore.loadDocuments,
        "refresh-users": admin.loadUsers
      };
    case "word-to-jira":
      return { parse: wordToJira.parse, publish: wordToJira.publish };
    default:
      return {
        "update:prompt": (value) => (documentStore.prompt.value = value),
        upload: documentStore.uploadDocument,
        open: documentStore.openDocument,
        delete: documentStore.deleteDocument
      };
  }
});

watch(
  () => [route.name, auth.currentUser.value],
  async ([routeName, user]) => {
    if (!user) return;
    if (route.meta.requiresAdmin && !user.is_staff) {
      await router.replace({ name: DEFAULT_ROUTE_NAME });
      return;
    }
    await loadRouteData(routeName);
  }
);

onMounted(auth.loadSession);
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <n-dialog-provider>
        <AuthPanel
          v-if="auth.checking.value || !auth.currentUser.value"
          :checking="auth.checking.value"
          :mode="auth.mode.value"
          :credentials="auth.credentials.value"
          :title="auth.title.value"
          :button-label="auth.buttonLabel.value"
          :passwords-match="auth.passwordsMatch.value"
          :submit-disabled="auth.submitDisabled.value"
          :loading="auth.loading.value"
          :error="auth.error.value"
          :register-message="auth.registerMessage.value"
          @submit="auth.submit"
          @switch-mode="auth.switchMode"
        />

        <main v-else class="app-shell">
          <AppSidebar
            :user="auth.currentUser.value"
            :menu-key="activeMenuKey"
            :menu-options="menuOptions"
            :loading="auth.loading.value"
            @logout="auth.logout"
            @update:menu-key="handleMenuUpdate"
          />

          <section class="workspace">
            <router-view v-slot="{ Component }">
              <component :is="Component" v-bind="routeProps" v-on="routeListeners" />
            </router-view>
          </section>
        </main>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
