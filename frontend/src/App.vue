<script setup>
import { computed, onMounted, ref } from "vue";

const loading = ref(false);
const error = ref("");
const health = ref(null);
const documents = ref([]);
const documentsLoading = ref(false);
const uploadError = ref("");
const activeDocument = ref(null);
const prompt = ref("Bu belgeyi incele ve önemli bilgileri kısa maddeler halinde çıkar.");
const deletingDocumentId = ref(null);

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

async function checkBackend() {
  loading.value = true;
  error.value = "";

  try {
    const response = await fetch("/api/health/");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    health.value = await response.json();
  } catch (err) {
    health.value = null;
    error.value = err instanceof Error ? err.message : "Bilinmeyen hata";
  } finally {
    loading.value = false;
  }
}

async function loadDocuments() {
  documentsLoading.value = true;

  try {
    const response = await fetch("/api/documents/");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
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
    const response = await fetch("/api/documents/upload/", {
      method: "POST",
      body: formData
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error_message || data.file?.[0] || data.detail || `HTTP ${response.status}`);
    }

    activeDocument.value = data;
    await loadDocuments();
    onFinish();
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "Dosya yüklenemedi";
    onError();
  }
}

async function openDocument(documentId) {
  const response = await fetch(`/api/documents/${documentId}/`);
  if (!response.ok) return;
  const data = await response.json();
  activeDocument.value = data;
}

async function deleteDocument(document) {
  if (!window.confirm(`${document.original_name} silinsin mi?`)) {
    return;
  }

  deletingDocumentId.value = document.id;

  try {
    const response = await fetch(`/api/documents/${document.id}/`, {
      method: "DELETE"
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

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

function formatBytes(size) {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

onMounted(() => {
  checkBackend();
  loadDocuments();
});
</script>

<template>
  <n-config-provider>
    <n-message-provider>
      <main class="app-shell">
        <section class="workspace">
          <div class="page-heading">
            <p>UAV Center</p>
            <h1>Yerel Belge İşleme Paneli</h1>
          </div>

          <div class="status-grid">
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

          <div class="document-layout">
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

            <section class="result-panel">
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
