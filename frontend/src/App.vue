<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import AdminMembershipView from "./views/AdminMembershipView.vue";
import OrganizationView from "./views/OrganizationView.vue";
import SystemView from "./views/SystemView.vue";
import TechnicalDocumentsView from "./views/TechnicalDocumentsView.vue";
import WordToJiraView from "./views/WordToJiraView.vue";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS", "TRACE"]);

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
const csrfToken = ref("");
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

const documentStatus = computed(() => {
  if (!activeDocument.value) return "Henüz belge seçilmedi";
  if (activeDocument.value.status === "processed") return "Belge işlendi";
  if (activeDocument.value.status === "failed") return "Belge işlenemedi";
  return "Belge sırada";
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

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

async function readResponse(response) {
  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

function responseError(data, fallback) {
  if (!data) return fallback;
  if (typeof data === "string") return data || fallback;
  if (data.detail) return data.detail;
  if (data.non_field_errors?.length) return data.non_field_errors.join(" ");
  if (data.username?.length) return data.username.join(" ");
  if (data.email?.length) return data.email.join(" ");
  if (data.password?.length) return data.password.join(" ");
  if (data.password_confirm?.length) return data.password_confirm.join(" ");
  if (data.file?.length) return data.file.join(" ");
  if (data.error_message) return data.error_message;
  if (typeof data === "object") {
    const firstMessage = Object.values(data).flat().find((message) => typeof message === "string");
    if (firstMessage) return firstMessage;
  }
  return fallback;
}

async function ensureCsrfToken() {
  if (csrfToken.value) return csrfToken.value;

  const response = await fetch(apiUrl("/api/auth/csrf/"), {
    credentials: "include"
  });
  const data = await readResponse(response);

  if (!response.ok) {
    throw new Error(responseError(data, `CSRF hazırlanamadı: HTTP ${response.status}`));
  }

  csrfToken.value = data.csrfToken;
  return csrfToken.value;
}

async function apiFetch(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});

  if (!SAFE_METHODS.has(method)) {
    headers.set("X-CSRFToken", await ensureCsrfToken());
  }

  const response = await fetch(apiUrl(path), {
    ...options,
    method,
    credentials: "include",
    headers
  });
  const data = await readResponse(response);

  if (!response.ok) {
    throw new Error(responseError(data, `HTTP ${response.status}`));
  }

  return data;
}

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
    csrfToken.value = "";
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
  try {
    const data = await apiFetch("/api/organization/projects/");
    projects.value = Array.isArray(data) ? data : [];
  } catch (err) {
    organizationError.value = err instanceof Error ? err.message : "Organizasyon bilgileri alınamadı";
  } finally {
    projectsLoading.value = false;
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
      : `/api/organization/panels/${parentId}/responsibles/`
  };
  try {
    await apiFetch(paths[type], {
      method: id ? "PATCH" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    await loadProjects();
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
    responsible: `/api/organization/responsibles/${item.id}/`
  };
  try {
    await apiFetch(paths[type], { method: "DELETE" });
    await loadProjects();
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

function formatBytes(size) {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

onMounted(() => {
  loadSession();
});
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <n-dialog-provider>
      <main v-if="authChecking" class="auth-shell">
        <n-spin size="large" />
      </main>

      <main v-else-if="!currentUser" class="auth-shell">
        <section class="auth-panel">
          <div class="auth-heading">
            <p>UAV Center</p>
            <h1>{{ authTitle }}</h1>
          </div>

          <n-tabs :value="authMode" type="segment" @update:value="switchAuthMode">
            <n-tab-pane name="login" tab="Giriş" />
            <n-tab-pane name="register" tab="Üyelik" />
          </n-tabs>

          <n-form class="auth-form" @submit.prevent="submitAuth">
            <n-form-item label="Kullanıcı adı">
              <n-input
                v-model:value="credentials.username"
                autocomplete="username"
                placeholder="kullanici_adi"
              />
            </n-form-item>

            <n-form-item v-if="authMode === 'register'" label="E-posta">
              <n-input
                v-model:value="credentials.email"
                autocomplete="email"
                placeholder="operator@example.com"
              />
            </n-form-item>

            <n-form-item label="Şifre">
              <n-input
                v-model:value="credentials.password"
                type="password"
                show-password-on="click"
                :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'"
                placeholder="••••••••"
              />
            </n-form-item>

            <n-form-item v-if="authMode === 'register'" label="Şifre Tekrarı">
              <n-input
                v-model:value="credentials.passwordConfirm"
                type="password"
                show-password-on="click"
                autocomplete="new-password"
                placeholder="••••••••"
              />
            </n-form-item>

            <n-alert
              v-if="authMode === 'register' && credentials.passwordConfirm && !registerPasswordsMatch"
              type="warning"
              title="Şifre kontrolü"
            >
              Şifreler aynı olmalı.
            </n-alert>

            <n-alert v-if="authError" type="error" title="Oturum hatası">
              {{ authError }}
            </n-alert>

            <n-alert v-if="registerMessage" type="success" title="Üyelik isteği alındı">
              {{ registerMessage }}
            </n-alert>

            <n-button
              attr-type="submit"
              type="primary"
              block
              :loading="authLoading"
              :disabled="authSubmitDisabled"
            >
              {{ authButtonLabel }}
            </n-button>
          </n-form>
        </section>
      </main>

      <main v-else class="app-shell">
        <aside class="toolbox-sidebar">
          <div class="toolbox-brand">
            <span>UAV Center</span>
            <strong>Toolbox</strong>
          </div>

          <div class="session-box">
            <span>Oturum</span>
            <strong>{{ currentUser.username }}</strong>
            <small v-if="currentUser.is_staff">Admin</small>
            <n-button size="small" secondary :loading="authLoading" @click="logoutUser">
              Çıkış Yap
            </n-button>
          </div>

          <n-menu
            class="toolbox-menu"
            :value="activeMenuKey"
            :options="menuOptions"
            :indent="18"
            :default-expanded-keys="currentUser.is_staff ? ['document-management', 'organization', 'tools', 'system', 'admin'] : ['document-management', 'organization', 'tools']"
            @update:value="handleMenuUpdate"
          />
        </aside>

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
            :error="wordParseError"
            :result="wordParseResult"
            @parse="parseWordTable"
          />

          <template v-else>
            <div class="page-heading">
              <p>UAV Center</p>
              <h1>Yerel Belge İşleme Paneli</h1>
            </div>

            <div id="document-tools" class="document-layout">
            <section class="upload-panel">
              <n-card title="Belge Yükle" size="small">
                <n-space vertical :size="16">
                  <n-upload
                    directory-dnd
                    :max="1"
                    :custom-request="uploadDocument"
                    accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv,.md"
                  >
                    <n-upload-dragger>
                      <div class="upload-title">Dosyayı buraya bırakın</div>
                      <div class="upload-subtitle">veya yerel dosya seçiciyi açmak için tıklayın</div>
                    </n-upload-dragger>
                  </n-upload>

                  <n-input
                    v-model:value="prompt"
                    type="textarea"
                    :autosize="{ minRows: 4, maxRows: 8 }"
                    placeholder="Belge için prompt girin"
                  />

                  <n-alert v-if="uploadError" type="error" title="Yükleme hatası">
                    {{ uploadError }}
                  </n-alert>
                </n-space>
              </n-card>

              <n-card title="Son Belgeler" size="small">
                <n-spin :show="documentsLoading">
                  <n-empty v-if="documents.length === 0" description="Henüz belge yok" />
                  <n-list v-else hoverable clickable>
                    <n-list-item
                      v-for="document in documents"
                      :key="document.id"
                      class="document-list-item"
                      @click="openDocument(document.id)"
                    >
                      <div class="document-row">
                        <n-thing
                          :title="document.original_name"
                          :description="`${formatBytes(document.size)} · ${document.status}`"
                        />
                        <n-button
                          size="small"
                          type="error"
                          secondary
                          :loading="deletingDocumentId === document.id"
                          @click.stop="deleteDocument(document)"
                        >
                          Sil
                        </n-button>
                      </div>
                    </n-list-item>
                  </n-list>
                </n-spin>
              </n-card>
            </section>

            <section id="ai-results" class="result-panel">
              <n-card title="AI İşleme Sonucu" size="small">
                <n-empty v-if="!activeDocument" description="Bir belge yükleyin veya listeden seçin" />

                <n-space v-else vertical :size="16">
                  <n-alert
                    :type="activeDocument.status === 'processed' ? 'success' : 'error'"
                    :title="documentStatus"
                  >
                    <span v-if="activeDocument.status === 'failed'">
                      {{ activeDocument.error_message }}
                    </span>
                    <span v-else>
                      {{ activeDocument.original_name }} içeriği yerelde çıkarıldı ve işlendi.
                    </span>
                  </n-alert>

                  <n-descriptions :column="2" bordered size="small">
                    <n-descriptions-item label="Karakter">
                      {{ activeDocument.ai_result?.metrics?.characters ?? activeDocument.text_length }}
                    </n-descriptions-item>
                    <n-descriptions-item label="Kelime">
                      {{ activeDocument.ai_result?.metrics?.words ?? "-" }}
                    </n-descriptions-item>
                    <n-descriptions-item label="Sağlayıcı">
                      {{ activeDocument.ai_result?.provider ?? "local" }}
                    </n-descriptions-item>
                    <n-descriptions-item label="Boyut">
                      {{ formatBytes(activeDocument.size) }}
                    </n-descriptions-item>
                  </n-descriptions>

                  <div>
                    <h2>Prompt</h2>
                    <p class="summary-text">{{ activeDocument.prompt || activeDocument.ai_result?.prompt || "-" }}</p>
                  </div>

                  <div>
                    <h2>Model Yanıtı</h2>
                    <p class="summary-text">
                      {{
                        activeDocument.ai_result?.response ||
                        activeDocument.ai_result?.summary ||
                        "-"
                      }}
                    </p>
                  </div>

                  <div v-if="activeDocument.ai_result?.preview">
                    <h2>Metin Ön İzleme</h2>
                    <p class="summary-text">{{ activeDocument.ai_result.preview }}</p>
                  </div>

                  <div v-if="activeDocument.ai_result?.keywords?.length">
                    <h2>Anahtar Kelimeler</h2>
                    <n-space>
                      <n-tag
                        v-for="keyword in activeDocument.ai_result.keywords"
                        :key="keyword"
                        type="info"
                      >
                        {{ keyword }}
                      </n-tag>
                    </n-space>
                  </div>

                  <n-collapse>
                    <n-collapse-item title="Çıkarılan metin" name="text">
                      <pre class="extracted-text">{{ activeDocument.extracted_text }}</pre>
                    </n-collapse-item>
                  </n-collapse>
                </n-space>
              </n-card>
            </section>
            </div>
          </template>
        </section>
      </main>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
