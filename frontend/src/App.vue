<script setup>
import { computed, onMounted, ref } from "vue";

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
const activeMenuKey = ref("documents");
const csrfToken = ref("");
const authChecking = ref(true);
const authLoading = ref(false);
const authMode = ref("login");
const authError = ref("");
const currentUser = ref(null);
const credentials = ref({
  username: "",
  password: ""
});

const menuTargets = {
  status: "system-status",
  documents: "document-tools",
  results: "ai-results"
};

const menuOptions = [
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
      }
    ]
  },
  {
    label: "Sistem",
    key: "system",
    children: [
      {
        label: "Durum Kontrolü",
        key: "status"
      }
    ]
  }
];

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
  if (data.password?.length) return data.password.join(" ");
  if (data.file?.length) return data.file.join(" ");
  if (data.error_message) return data.error_message;
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
      await Promise.all([checkBackend(), loadDocuments()]);
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

  try {
    const data = await apiFetch(`/api/auth/${authMode.value}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(credentials.value)
    });
    currentUser.value = data.user;
    csrfToken.value = "";
    credentials.value.password = "";
    await Promise.all([checkBackend(), loadDocuments()]);
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
    activeDocument.value = null;
  } catch (err) {
    authError.value = err instanceof Error ? err.message : "Çıkış yapılamadı";
  } finally {
    authLoading.value = false;
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

function switchAuthMode(mode) {
  authMode.value = mode;
  authError.value = "";
}

function handleMenuUpdate(key) {
  activeMenuKey.value = key;

  const targetId = menuTargets[key];
  if (!targetId) return;

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

            <n-form-item label="Şifre">
              <n-input
                v-model:value="credentials.password"
                type="password"
                show-password-on="click"
                :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'"
                placeholder="••••••••"
              />
            </n-form-item>

            <n-alert v-if="authError" type="error" title="Oturum hatası">
              {{ authError }}
            </n-alert>

            <n-button
              attr-type="submit"
              type="primary"
              block
              :loading="authLoading"
              :disabled="!credentials.username || !credentials.password"
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
            <n-button size="small" secondary :loading="authLoading" @click="logoutUser">
              Çıkış Yap
            </n-button>
          </div>

          <n-menu
            class="toolbox-menu"
            :value="activeMenuKey"
            :options="menuOptions"
            :indent="18"
            :default-expanded-keys="['tools', 'system']"
            @update:value="handleMenuUpdate"
          />
        </aside>

        <section class="workspace">
          <div class="page-heading">
            <p>UAV Center</p>
            <h1>Yerel Belge İşleme Paneli</h1>
          </div>

          <div id="system-status" class="status-grid">
            <n-card title="Sistem Durumu" size="small">
              <n-space vertical :size="16">
                <n-alert
                  :type="error ? 'error' : health ? 'success' : 'info'"
                  :title="apiStatus"
                >
                  <span v-if="error">Hata: {{ error }}</span>
                  <span v-else-if="health">
                    {{ health.service }} servisi {{ health.timestamp }} zamanında yanıt verdi.
                  </span>
                  <span v-else>Backend bağlantısı için kontrol başlatılabilir.</span>
                </n-alert>

                <n-button type="primary" :loading="loading" @click="checkBackend">
                  Backend'i Test Et
                </n-button>
              </n-space>
            </n-card>

            <n-card title="Desteklenen Dosyalar" size="small">
              <n-descriptions :column="1" bordered size="small">
                <n-descriptions-item label="PDF">.pdf</n-descriptions-item>
                <n-descriptions-item label="Office">.docx, .xlsx, .pptx</n-descriptions-item>
                <n-descriptions-item label="Metin">.txt, .csv, .md</n-descriptions-item>
              </n-descriptions>
            </n-card>
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
        </section>
      </main>
    </n-message-provider>
  </n-config-provider>
</template>
