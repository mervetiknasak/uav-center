<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import AppSidebar from "./components/AppSidebar.vue";
import AuthPanel from "./components/AuthPanel.vue";
import { useApi } from "./composables/useApi";
import AdminMembershipView from "./views/AdminMembershipView.vue";
import DocumentProcessingView from "./views/DocumentProcessingView.vue";
import OrganizationView from "./views/OrganizationView.vue";
import SystemView from "./views/SystemView.vue";
import TechnicalDocumentsView from "./views/TechnicalDocumentsView.vue";
import WordToJiraView from "./views/WordToJiraView.vue";

const { API_BASE_URL, apiFetch, ensureCsrfToken, resetCsrfToken } = useApi();

const loading = ref(false);
const error = ref("");
const health = ref(null);
const documents = ref([]);
const documentsLoading = ref(false);
const uploadError = ref("");
const activeDocument = ref(null);
const prompt = ref("Bu belgeyi incele ve önemli bilgileri kısa maddeler halinde çıkar.");
const deletingDocumentId = ref(null);
const activeMenuKey = ref("technical-documents");
const authChecking = ref(true);
const authLoading = ref(false);
const authMode = ref("login");
const authError = ref("");
const registerMessage = ref("");
const currentUser = ref(null);
const adminUsers = ref([]);
const adminUsersLoading = ref(false);
const adminUsersError = ref("");
const updatingUserId = ref(null);
const projects = ref([]);
const personGroups = ref([]);
const projectsLoading = ref(false);
const organizationSaving = ref(false);
const organizationError = ref("");
const technicalDocuments = ref([]);
const technicalDocumentsLoading = ref(false);
const technicalDocumentSaving = ref(false);
const technicalDocumentError = ref("");
const technicalDocumentNotice = ref("");
const notifyingTechnicalDocumentId = ref(null);
const wordParseLoading = ref(false);
const wordParseError = ref("");
const wordParseResult = ref(null);
const wordPublishLoading = ref(false);
const wordPublishResult = ref(null);
const credentials = ref({
  username: "",
  email: "",
  password: "",
  passwordConfirm: ""
});

const menuTargets = {
  documents: "document-tools",
  results: "ai-results"
};

const menuOptions = computed(() => {
  const options = [
    {
      label: "Doküman Yönetimi",
      key: "document-management",
      children: [
        {
          label: "Teknik Dokümanlar",
          key: "technical-documents"
        }
      ]
    },
    {
      label: "Organizasyon",
      key: "organization",
      children: [
        {
          label: "Projeler ve Paneller",
          key: "organization-projects"
        }
      ]
    },
    {
      label: "Araçlar",
      key: "tools",
      children: [
        {
          label: "Belge İşleme",
          key: "documents"
        },
        {
          label: "AI Sonuçları",
          key: "results"
        },
        {
          label: "Toplantı Tutanağı Okuyucu",
          key: "word-to-jira"
        }
      ]
    }
  ];

  if (currentUser.value?.is_staff) {
    options.push({
      label: "Sistem",
      key: "system",
      children: [
        {
          label: "Kontrol Paneli",
          key: "system-dashboard"
        }
      ]
    });

    options.push({
      label: "Admin",
      key: "admin",
      children: [
        {
          label: "Organizasyon Yönetimi",
          key: "organization-admin"
        },
        {
          label: "Üyeler",
          key: "users"
        }
      ]
    });
  }

  return options;
});

const apiStatus = computed(() => {
  if (loading.value) return "Bağlantı kontrol ediliyor";
  if (error.value) return "Backend ulaşılamıyor";
  if (health.value?.status === "ok") return "Backend hazır";
  return "Henüz kontrol edilmedi";
});

const authTitle = computed(() => (authMode.value === "login" ? "Giriş Yap" : "Yeni Üyelik"));
const authButtonLabel = computed(() => (authMode.value === "login" ? "Giriş Yap" : "Üye Ol"));
const registerPasswordsMatch = computed(
  () => credentials.value.password && credentials.value.password === credentials.value.passwordConfirm
);
const authSubmitDisabled = computed(() => {
  if (!credentials.value.username || !credentials.value.password) return true;
  if (authMode.value === "login") return false;
  return !credentials.value.email || !credentials.value.passwordConfirm || !registerPasswordsMatch.value;
});

async function checkBackend() {
  loading.value = true;
  error.value = "";

  try {
    health.value = await apiFetch("/api/health/");
  } catch (err) {
    health.value = null;
    error.value = err instanceof Error ? err.message : "Bilinmeyen hata";
  } finally {
    loading.value = false;
  }
}

async function loadSession() {
  authChecking.value = true;
  authError.value = "";

  try {
    await ensureCsrfToken();
    const data = await apiFetch("/api/auth/me/");
    currentUser.value = data.authenticated ? data.user : null;
    if (currentUser.value) {
      await Promise.all([
        checkBackend(),
        loadDocuments(),
        loadProjects(),
        loadTechnicalDocuments(),
        loadAdminUsersIfNeeded()
      ]);
    }
  } catch (err) {
    authError.value = err instanceof Error ? err.message : "Oturum bilgisi alınamadı";
    currentUser.value = null;
  } finally {
    authChecking.value = false;
  }
}

async function submitAuth() {
  authLoading.value = true;
  authError.value = "";
  registerMessage.value = "";

  try {
    const payload =
      authMode.value === "login"
        ? {
            username: credentials.value.username,
            password: credentials.value.password
          }
        : {
            username: credentials.value.username,
            email: credentials.value.email,
            password: credentials.value.password,
            password_confirm: credentials.value.passwordConfirm
          };
    const data = await apiFetch(`/api/auth/${authMode.value}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (authMode.value === "register") {
      registerMessage.value = data.message || "Üyelik isteğiniz alındı. Admin onayı bekleniyor.";
      credentials.value = {
        username: "",
        email: "",
        password: "",
        passwordConfirm: ""
      };
      authMode.value = "login";
      return;
    }

    currentUser.value = data.user;
    resetCsrfToken();
    credentials.value.password = "";
    credentials.value.passwordConfirm = "";
    await Promise.all([
      checkBackend(),
      loadDocuments(),
      loadProjects(),
      loadTechnicalDocuments(),
      loadAdminUsersIfNeeded()
    ]);
  } catch (err) {
    authError.value = err instanceof Error ? err.message : "İşlem tamamlanamadı";
  } finally {
    authLoading.value = false;
  }
}

async function logoutUser() {
  authLoading.value = true;
  authError.value = "";

  try {
    await apiFetch("/api/auth/logout/", {
      method: "POST"
    });
    currentUser.value = null;
    documents.value = [];
    adminUsers.value = [];
    projects.value = [];
    technicalDocuments.value = [];
    activeDocument.value = null;
  } catch (err) {
    authError.value = err instanceof Error ? err.message : "Çıkış yapılamadı";
  } finally {
    authLoading.value = false;
  }
}

async function loadAdminUsersIfNeeded() {
  if (!currentUser.value?.is_staff) return;
  await loadAdminUsers();
}

async function loadAdminUsers() {
  adminUsersLoading.value = true;
  adminUsersError.value = "";

  try {
    const data = await apiFetch("/api/admin/users/");
    adminUsers.value = Array.isArray(data) ? data : [];
  } catch (err) {
    adminUsersError.value = err instanceof Error ? err.message : "Üyeler alınamadı";
  } finally {
    adminUsersLoading.value = false;
  }
}

async function updateUserStatus(user, isActive) {
  updatingUserId.value = user.id;
  adminUsersError.value = "";

  try {
    const updatedUser = await apiFetch(`/api/admin/users/${user.id}/status/`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ is_active: isActive })
    });
    adminUsers.value = adminUsers.value.map((item) => (item.id === updatedUser.id ? updatedUser : item));
  } catch (err) {
    adminUsersError.value = err instanceof Error ? err.message : "Kullanıcı durumu güncellenemedi";
  } finally {
    updatingUserId.value = null;
  }
}

async function loadProjects() {
  projectsLoading.value = true;
  organizationError.value = "";
  const [projectResult, groupResult] = await Promise.allSettled([
    apiFetch("/api/organization/projects/"),
    apiFetch("/api/organization/person-groups/")
  ]);

  if (projectResult.status === "fulfilled") {
    projects.value = Array.isArray(projectResult.value) ? projectResult.value : [];
  }

  if (groupResult.status === "fulfilled") {
    personGroups.value = Array.isArray(groupResult.value)
      ? groupResult.value.map((group) => ({
          ...group,
          people: Array.isArray(group.people) ? group.people : []
        }))
      : [];
  }

  const errors = [projectResult, groupResult]
    .filter((result) => result.status === "rejected")
    .map((result) =>
      result.reason instanceof Error ? result.reason.message : "Organizasyon bilgileri alınamadı"
    );
  if (errors.length) {
    organizationError.value = errors.join(" ");
  }

  projectsLoading.value = false;
}

async function refreshPersonGroups() {
  const groupData = await apiFetch("/api/organization/person-groups/");
  personGroups.value = Array.isArray(groupData)
    ? groupData.map((group) => ({
        ...group,
        people: Array.isArray(group.people) ? group.people : []
      }))
    : [];
}

async function refreshProjects() {
  const projectData = await apiFetch("/api/organization/projects/");
  projects.value = Array.isArray(projectData) ? projectData : [];
}

async function refreshOrganizationType(type) {
  if (type === "group" || type === "person") {
    await refreshPersonGroups();
  } else {
    await refreshProjects();
  }
}

async function saveOrganizationItem({ type, id, parentId, payload, done }) {
  organizationSaving.value = true;
  organizationError.value = "";
  const paths = {
    project: id ? `/api/organization/projects/${id}/` : "/api/organization/projects/",
    panel: id
      ? `/api/organization/panels/${id}/`
      : `/api/organization/projects/${parentId}/panels/`,
    responsible: id
      ? `/api/organization/responsibles/${id}/`
      : `/api/organization/panels/${parentId}/responsibles/`,
    group: id
      ? `/api/organization/person-groups/${id}/`
      : "/api/organization/person-groups/",
    person: id
      ? `/api/organization/people/${id}/`
      : `/api/organization/person-groups/${parentId}/people/`
  };
  try {
    await apiFetch(paths[type], {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await refreshOrganizationType(type);
    done?.();
  } catch (err) {
    organizationError.value = err instanceof Error ? err.message : "Kayıt kaydedilemedi";
  } finally {
    organizationSaving.value = false;
  }
}

async function deleteOrganizationItem({ type, item }) {
  organizationSaving.value = true;
  organizationError.value = "";
  const paths = {
    project: `/api/organization/projects/${item.id}/`,
    panel: `/api/organization/panels/${item.id}/`,
    responsible: `/api/organization/responsibles/${item.id}/`,
    group: `/api/organization/person-groups/${item.id}/`,
    person: `/api/organization/people/${item.id}/`
  };
  try {
    await apiFetch(paths[type], { method: "DELETE" });
    await refreshOrganizationType(type);
  } catch (err) {
    organizationError.value = err instanceof Error ? err.message : "Kayıt silinemedi";
  } finally {
    organizationSaving.value = false;
  }
}

async function reorderResponsibles({ items }) {
  organizationSaving.value = true;
  organizationError.value = "";
  try {
    await Promise.all(
      items.map((item) =>
        apiFetch(`/api/organization/responsibles/${item.id}/`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ order: item.order })
        })
      )
    );
    await loadProjects();
  } catch (err) {
    organizationError.value = err instanceof Error ? err.message : "Sorumlu sıralaması güncellenemedi";
    await loadProjects();
  } finally {
    organizationSaving.value = false;
  }
}

async function loadTechnicalDocuments() {
  technicalDocumentsLoading.value = true;
  technicalDocumentError.value = "";
  try {
    const data = await apiFetch("/api/technical-documents/");
    technicalDocuments.value = Array.isArray(data) ? data : [];
  } catch (err) {
    technicalDocumentError.value =
      err instanceof Error ? err.message : "Teknik dokümanlar alınamadı";
  } finally {
    technicalDocumentsLoading.value = false;
  }
}

async function saveTechnicalDocument({ id, payload, done }) {
  technicalDocumentSaving.value = true;
  technicalDocumentError.value = "";
  technicalDocumentNotice.value = "";
  try {
    const updated = await apiFetch(
      id ? `/api/technical-documents/${id}/` : "/api/technical-documents/",
      {
        method: id ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }
    );
    if (id) {
      technicalDocuments.value = technicalDocuments.value.map((document) =>
        document.id === updated.id ? updated : document
      );
    } else {
      technicalDocuments.value = [updated, ...technicalDocuments.value];
    }
    technicalDocumentNotice.value = id
      ? `${updated.code} güncellendi.`
      : `${updated.code} teknik dokümanı oluşturuldu.`;
    done?.();
  } catch (err) {
    technicalDocumentError.value =
      err instanceof Error ? err.message : "Teknik doküman kaydedilemedi";
  } finally {
    technicalDocumentSaving.value = false;
  }
}

async function deleteTechnicalDocument(document) {
  technicalDocumentSaving.value = true;
  technicalDocumentError.value = "";
  technicalDocumentNotice.value = "";
  try {
    await apiFetch(`/api/technical-documents/${document.id}/`, { method: "DELETE" });
    technicalDocuments.value = technicalDocuments.value.filter((item) => item.id !== document.id);
    technicalDocumentNotice.value = `${document.code} silindi.`;
  } catch (err) {
    technicalDocumentError.value =
      err instanceof Error ? err.message : "Teknik doküman silinemedi";
  } finally {
    technicalDocumentSaving.value = false;
  }
}

async function notifyTechnicalDocument({ document, payload, done }) {
  notifyingTechnicalDocumentId.value = document.id;
  technicalDocumentError.value = "";
  technicalDocumentNotice.value = "";
  try {
    const data = await apiFetch(`/api/technical-documents/${document.id}/notify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    technicalDocuments.value = technicalDocuments.value.map((item) =>
      item.id === data.document.id ? data.document : item
    );
    technicalDocumentNotice.value = data.message;
    done?.();
  } catch (err) {
    technicalDocumentError.value =
      err instanceof Error ? err.message : "Panel sorumlularına e-posta gönderilemedi";
  } finally {
    notifyingTechnicalDocumentId.value = null;
  }
}

async function loadDocuments() {
  documentsLoading.value = true;

  try {
    const data = await apiFetch("/api/documents/");
    documents.value = Array.isArray(data) ? data : [];
  } finally {
    documentsLoading.value = false;
  }
}

async function uploadDocument({ file, onFinish, onError }) {
  uploadError.value = "";
  const trimmedPrompt = prompt.value.trim();
  if (!trimmedPrompt) {
    uploadError.value = "Belgeyi işlemek için prompt girin.";
    onError();
    return;
  }

  const formData = new FormData();
  formData.append("file", file.file);
  formData.append("prompt", trimmedPrompt);

  try {
    const data = await apiFetch("/api/documents/upload/", {
      method: "POST",
      body: formData
    });

    activeDocument.value = data;
    await loadDocuments();
    onFinish();
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "Dosya yüklenemedi";
    onError();
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
  if (!window.confirm(`${document.original_name} silinsin mi?`)) {
    return;
  }

  deletingDocumentId.value = document.id;

  try {
    await apiFetch(`/api/documents/${document.id}/`, {
      method: "DELETE"
    });

    if (activeDocument.value?.id === document.id) {
      activeDocument.value = null;
    }

    await loadDocuments();
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "Belge silinemedi";
  } finally {
    deletingDocumentId.value = null;
  }
}

async function parseWordTable({ file, onFinish, onError }) {
  wordParseLoading.value = true;
  wordParseError.value = "";
  wordParseResult.value = null;
  wordPublishResult.value = null;
  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await apiFetch("/api/word-to-jira/parse/", {
      method: "POST",
      body: formData
    });
    wordParseResult.value = data;
    console.group(`[Word → Jira] ${data.file_name}`);
    data.cells.forEach((cell) => {
      console.log(
        `index=${cell.index} table=${cell.table_index} row=${cell.row_index} column=${cell.column_index}`,
        cell.text
      );
    });
    console.groupEnd();
    onFinish?.();
  } catch (err) {
    wordParseError.value = err instanceof Error ? err.message : "Word dosyası okunamadı";
    onError?.();
  } finally {
    wordParseLoading.value = false;
  }
}

async function publishWordToJira(draft) {
  wordPublishLoading.value = true;
  wordParseError.value = "";
  wordPublishResult.value = null;
  try {
    wordPublishResult.value = await apiFetch("/api/word-to-jira/publish/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(draft)
    });
  } catch (err) {
    wordParseError.value = err instanceof Error ? err.message : "Jira aktarımı başarısız";
  } finally {
    wordPublishLoading.value = false;
  }
}

function switchAuthMode(mode) {
  authMode.value = mode;
  authError.value = "";
  registerMessage.value = "";
}

async function handleMenuUpdate(key) {
  activeMenuKey.value = key;

  if (key === "system-dashboard") {
    await Promise.all([checkBackend(), loadDocuments(), loadAdminUsersIfNeeded()]);
    return;
  }

  if (key === "users") {
    await loadAdminUsersIfNeeded();
    return;
  }

  if (key === "technical-documents") {
    await Promise.all([loadProjects(), loadTechnicalDocuments()]);
    return;
  }

  if (key === "organization-projects" || key === "organization-admin") {
    await loadProjects();
    return;
  }

  const targetId = menuTargets[key];
  if (!targetId) return;

  await nextTick();
  document.getElementById(targetId)?.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}

onMounted(() => {
  loadSession();
});
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <n-dialog-provider>
      <AuthPanel
        v-if="authChecking || !currentUser"
        :checking="authChecking"
        :mode="authMode"
        :credentials="credentials"
        :title="authTitle"
        :button-label="authButtonLabel"
        :passwords-match="registerPasswordsMatch"
        :submit-disabled="authSubmitDisabled"
        :loading="authLoading"
        :error="authError"
        :register-message="registerMessage"
        @submit="submitAuth"
        @switch-mode="switchAuthMode"
      />

      <main v-else class="app-shell">
        <AppSidebar
          :user="currentUser"
          :menu-key="activeMenuKey"
          :menu-options="menuOptions"
          :loading="authLoading"
          @logout="logoutUser"
          @update:menu-key="handleMenuUpdate"
        />

        <section class="workspace">
          <TechnicalDocumentsView
            v-if="activeMenuKey === 'technical-documents'"
            :projects="projects"
            :documents="technicalDocuments"
            :loading="technicalDocumentsLoading"
            :saving="technicalDocumentSaving"
            :notifying-id="notifyingTechnicalDocumentId"
            :error="technicalDocumentError"
            :notice="technicalDocumentNotice"
            :can-edit="currentUser.is_staff"
            @refresh="loadTechnicalDocuments"
            @save="saveTechnicalDocument"
            @delete="deleteTechnicalDocument"
            @notify="notifyTechnicalDocument"
          />

          <OrganizationView
            v-else-if="activeMenuKey === 'organization-projects' || (activeMenuKey === 'organization-admin' && currentUser.is_staff)"
            :projects="projects"
            :person-groups="personGroups"
            :loading="projectsLoading"
            :saving="organizationSaving"
            :error="organizationError"
            :can-edit="activeMenuKey === 'organization-admin' && currentUser.is_staff"
            @refresh="loadProjects"
            @save="saveOrganizationItem"
            @delete="deleteOrganizationItem"
            @reorder-responsibles="reorderResponsibles"
          />

          <AdminMembershipView
            v-else-if="activeMenuKey === 'users' && currentUser.is_staff"
            :users="adminUsers"
            :loading="adminUsersLoading"
            :error="adminUsersError"
            :updating-user-id="updatingUserId"
            @refresh="loadAdminUsers"
            @update-status="updateUserStatus"
          />

          <SystemView
            v-else-if="activeMenuKey === 'system-dashboard' && currentUser.is_staff"
            :health="health"
            :api-status="apiStatus"
            :error="error"
            :loading="loading"
            :documents="documents"
            :documents-loading="documentsLoading"
            :admin-users="adminUsers"
            :admin-users-loading="adminUsersLoading"
            :admin-users-error="adminUsersError"
            :current-user="currentUser"
            :api-base-url="API_BASE_URL"
            @check-backend="checkBackend"
            @refresh-documents="loadDocuments"
            @refresh-users="loadAdminUsers"
          />

          <WordToJiraView
            v-else-if="activeMenuKey === 'word-to-jira'"
            :loading="wordParseLoading"
            :publishing="wordPublishLoading"
            :error="wordParseError"
            :result="wordParseResult"
            :publish-result="wordPublishResult"
            @parse="parseWordTable"
            @publish="publishWordToJira"
          />

          <DocumentProcessingView
            v-else
            v-model:prompt="prompt"
            :documents="documents"
            :loading="documentsLoading"
            :upload-error="uploadError"
            :active-document="activeDocument"
            :deleting-document-id="deletingDocumentId"
            @upload="uploadDocument"
            @open="openDocument"
            @delete="deleteDocument"
          />
        </section>
      </main>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
