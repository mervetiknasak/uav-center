<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  documents: { type: Array, required: true },
  loading: Boolean,
  prompt: { type: String, required: true },
  useOcr: Boolean,
  useAi: { type: Boolean, default: true },
  uploadError: { type: String, default: "" },
  uploadNotice: { type: String, default: "" },
  activeDocument: { type: Object, default: null },
  deletingDocumentId: { type: Number, default: null },
  controls: { type: Array, default: () => [] },
  selectedControlIds: { type: Array, default: () => [] },
  ragQuery: { type: String, default: "" },
  ragResult: { type: Object, default: null },
  controlResult: { type: Object, default: null },
  analysisLoading: Boolean,
  controlsLoading: Boolean,
  analysisError: { type: String, default: "" }
});

const emit = defineEmits([
  "update:prompt", "update:use-ocr", "update:use-ai", "update:rag-query",
  "update:selected-control-ids", "upload", "open", "delete", "ask-document",
  "run-controls", "save-control", "delete-control"
]);
const copied = ref(false);
const controlForm = ref({ database_id: null, name: "", description: "", instructions: "", severity: "warning", is_active: true });
const severityOptions = [
  { label: "Bilgi", value: "info" },
  { label: "Uyarı", value: "warning" },
  { label: "Kritik", value: "critical" }
];
const emailAddresses = computed(() => props.activeDocument?.ai_result?.ocr?.email_addresses || []);
const documentStatus = computed(() => {
  if (!props.activeDocument) return "Henüz belge seçilmedi";
  if (props.activeDocument.status === "processed") return "Belge işlendi";
  if (props.activeDocument.status === "failed") return "Belge işlenemedi";
  return "Belge sırada";
});
const documentReady = computed(() => props.activeDocument?.status === "processed");

function formatBytes(size) {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

async function copyEmailAddresses() {
  if (!emailAddresses.value.length) return;
  const text = emailAddresses.value.join("; ");
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
  } else {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  copied.value = true;
  window.setTimeout(() => (copied.value = false), 1600);
}

function editControl(control) {
  controlForm.value = {
    database_id: control.database_id,
    name: control.name,
    description: control.description || "",
    instructions: control.instructions || "",
    severity: control.severity,
    is_active: control.is_active
  };
}

function resetControlForm() {
  controlForm.value = { database_id: null, name: "", description: "", instructions: "", severity: "warning", is_active: true };
}

function submitControl() {
  if (!controlForm.value.name.trim() || controlForm.value.instructions.trim().length < 10) return;
  emit("save-control", { ...controlForm.value });
  resetControlForm();
}

function outcomeType(outcome) {
  return { passed: "success", failed: "error", review: "warning" }[outcome] || "default";
}
</script>

<template>
  <div class="page-heading">
    <p>UAV Center</p>
    <h1>Yerel Belge İşleme Paneli</h1>
  </div>
  <div id="document-tools" class="document-layout">
    <section class="upload-panel">
      <n-card title="Belge Yükle" size="small">
        <n-space vertical :size="16">
          <n-upload directory-dnd :max="1" :custom-request="(options) => emit('upload', options)" accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv,.md,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff">
            <n-upload-dragger>
              <div class="upload-title">Dosyayı buraya bırakın</div>
              <div class="upload-subtitle">veya yerel dosya seçiciyi açmak için tıklayın</div>
            </n-upload-dragger>
          </n-upload>
          <div class="processing-options">
            <div>
              <strong>OCR ile metin çıkar</strong>
              <span>Resimler, taranmış PDF sayfaları ve belgelere gömülü görseller</span>
            </div>
            <n-switch :value="useOcr" @update:value="emit('update:use-ocr', $event)" />
          </div>
          <div class="processing-options">
            <div>
              <strong>AI ile işle</strong>
              <span>Çıkarılan metni aşağıdaki prompt ile analiz eder</span>
            </div>
            <n-switch :value="useAi" @update:value="emit('update:use-ai', $event)" />
          </div>
          <n-input
            :value="prompt"
            type="textarea"
            :disabled="!useAi"
            :autosize="{ minRows: 4, maxRows: 8 }"
            :placeholder="useAi ? 'Belge için prompt girin' : 'AI işlemi kapalı'"
            @update:value="emit('update:prompt', $event)"
          />
          <n-alert v-if="uploadError" type="error" title="Yükleme hatası">{{ uploadError }}</n-alert>
          <n-alert v-if="uploadNotice" type="info" title="İşlem sıraya alındı">{{ uploadNotice }}</n-alert>
        </n-space>
      </n-card>
      <n-card title="Son Belgeler" size="small">
        <n-spin :show="loading">
          <n-empty v-if="documents.length === 0" description="Henüz belge yok" />
          <n-list v-else hoverable clickable>
            <n-list-item v-for="document in documents" :key="document.id" class="document-list-item" @click="emit('open', document.id)">
              <div class="document-row">
                <n-thing :title="document.original_name" :description="`${formatBytes(document.size)} · ${document.status}`" />
                <n-button size="small" type="error" secondary :loading="deletingDocumentId === document.id" @click.stop="emit('delete', document)">Sil</n-button>
              </div>
            </n-list-item>
          </n-list>
        </n-spin>
      </n-card>
      <n-card title="Doküman Kontrolleri" size="small">
        <n-spin :show="controlsLoading">
          <n-space vertical :size="12">
            <n-checkbox-group
              :value="selectedControlIds"
              @update:value="emit('update:selected-control-ids', $event)"
            >
              <n-space vertical>
                <div v-for="control in controls" :key="control.id" class="control-row">
                  <n-checkbox :value="control.id" :disabled="!control.is_active">
                    {{ control.name }} · {{ control.kind === "system" ? "Sunucu" : "Kullanıcı" }}
                  </n-checkbox>
                  <n-space v-if="control.kind === 'custom'" :size="4">
                    <n-button size="tiny" quaternary @click="editControl(control)">Düzenle</n-button>
                    <n-button size="tiny" quaternary type="error" @click="emit('delete-control', control)">Sil</n-button>
                  </n-space>
                  <small>{{ control.description }}</small>
                </div>
              </n-space>
            </n-checkbox-group>
            <n-divider>Kullanıcı kontrolü ekle</n-divider>
            <n-input v-model:value="controlForm.name" placeholder="Kontrol adı" maxlength="120" />
            <n-input v-model:value="controlForm.description" placeholder="Kısa açıklama" type="textarea" :rows="2" />
            <n-input
              v-model:value="controlForm.instructions"
              placeholder="Model neyi, hangi koşula göre kontrol etmeli?"
              type="textarea"
              :rows="3"
            />
            <n-select v-model:value="controlForm.severity" :options="severityOptions" />
            <n-space justify="end">
              <n-button v-if="controlForm.database_id" @click="resetControlForm">Vazgeç</n-button>
              <n-button type="primary" :disabled="!controlForm.name.trim() || controlForm.instructions.trim().length < 10" @click="submitControl">
                {{ controlForm.database_id ? "Kontrolü güncelle" : "Kontrol ekle" }}
              </n-button>
            </n-space>
          </n-space>
        </n-spin>
      </n-card>
    </section>

    <section id="ai-results" class="result-panel">
      <n-card title="AI İşleme Sonucu" size="small">
        <n-empty v-if="!activeDocument" description="Bir belge yükleyin veya listeden seçin" />
        <n-space v-else vertical :size="16">
          <n-alert :type="activeDocument.status === 'processed' ? 'success' : activeDocument.status === 'failed' ? 'error' : 'info'" :title="documentStatus">
            <span v-if="activeDocument.status === 'failed'">{{ activeDocument.error_message }}</span>
            <span v-else-if="activeDocument.status === 'pending'">{{ activeDocument.original_name }} arka planda işlenmek üzere sıraya alındı.</span>
            <span v-else>{{ activeDocument.original_name }} içeriği yerelde çıkarıldı{{ activeDocument.ai_result?.ai_enabled ? " ve AI ile işlendi" : "" }}.</span>
          </n-alert>
          <n-descriptions :column="2" bordered size="small">
            <n-descriptions-item label="Karakter">{{ activeDocument.ai_result?.metrics?.characters ?? activeDocument.text_length }}</n-descriptions-item>
            <n-descriptions-item label="Kelime">{{ activeDocument.ai_result?.metrics?.words ?? "-" }}</n-descriptions-item>
            <n-descriptions-item label="Sağlayıcı">{{ activeDocument.ai_result?.ai_enabled === false ? "Devre dışı" : (activeDocument.ai_result?.provider ?? "local") }}</n-descriptions-item>
            <n-descriptions-item label="Boyut">{{ formatBytes(activeDocument.size) }}</n-descriptions-item>
          </n-descriptions>
          <template v-if="activeDocument.ai_result?.ai_enabled !== false">
            <div><h2>Prompt</h2><p class="summary-text">{{ activeDocument.prompt || activeDocument.ai_result?.prompt || "-" }}</p></div>
            <div><h2>Model Yanıtı</h2><p class="summary-text">{{ activeDocument.ai_result?.response || activeDocument.ai_result?.summary || "-" }}</p></div>
          </template>
          <div v-if="activeDocument.ai_result?.preview"><h2>Metin Ön İzleme</h2><p class="summary-text">{{ activeDocument.ai_result.preview }}</p></div>
          <div v-if="activeDocument.ai_result?.keywords?.length">
            <h2>Anahtar Kelimeler</h2>
            <n-space><n-tag v-for="keyword in activeDocument.ai_result.keywords" :key="keyword" type="info">{{ keyword }}</n-tag></n-space>
          </div>
          <n-card v-if="activeDocument.ai_result?.ocr?.enabled" title="OCR Sonucu" size="small" embedded>
            <n-space vertical :size="12">
              <n-descriptions :column="2" bordered size="small">
                <n-descriptions-item label="Motor">EasyOCR</n-descriptions-item>
                <n-descriptions-item label="Diller">{{ activeDocument.ai_result.ocr.languages.join(", ").toUpperCase() }}</n-descriptions-item>
                <n-descriptions-item label="Görsel">{{ activeDocument.ai_result.ocr.processed_images }}</n-descriptions-item>
                <n-descriptions-item label="PDF sayfası">{{ activeDocument.ai_result.ocr.processed_pages }}</n-descriptions-item>
              </n-descriptions>
              <div class="email-heading">
                <h2>Bulunan e-posta adresleri</h2>
                <n-button v-if="emailAddresses.length" size="small" secondary @click="copyEmailAddresses">
                  {{ copied ? "Kopyalandı" : "Tümünü kopyala" }}
                </n-button>
              </div>
              <n-empty v-if="!emailAddresses.length" description="E-posta adresi bulunamadı" size="small" />
              <n-space v-else>
                <n-tag v-for="address in emailAddresses" :key="address" type="success">{{ address }}</n-tag>
              </n-space>
              <n-alert v-if="activeDocument.ai_result.ocr.warnings.length" type="warning" title="Bazı içerikler OCR ile okunamadı">
                <ul class="ocr-warning-list">
                  <li v-for="warning in activeDocument.ai_result.ocr.warnings" :key="warning">{{ warning }}</li>
                </ul>
              </n-alert>
            </n-space>
          </n-card>
          <n-collapse><n-collapse-item title="Çıkarılan metin" name="text"><pre class="extracted-text">{{ activeDocument.extracted_text }}</pre></n-collapse-item></n-collapse>
          <n-divider>Kaynaklı RAG analizi</n-divider>
          <n-input
            :value="ragQuery"
            type="textarea"
            :rows="3"
            placeholder="Bu doküman hakkında bir soru sorun"
            @update:value="emit('update:rag-query', $event)"
            @keydown.ctrl.enter="emit('ask-document')"
          />
          <n-space justify="end">
            <n-button type="primary" :loading="analysisLoading" :disabled="!documentReady || !ragQuery.trim()" @click="emit('ask-document')">
              Kaynaklarla yanıtla
            </n-button>
            <n-button :loading="analysisLoading" :disabled="!documentReady" @click="emit('run-controls')">Seçili kontrolleri çalıştır</n-button>
          </n-space>
          <n-alert v-if="analysisError" type="error" title="Analiz hatası">{{ analysisError }}</n-alert>
          <n-card v-if="ragResult" title="RAG yanıtı" embedded size="small">
            <p class="summary-text">{{ ragResult.answer }}</p>
            <n-collapse v-if="ragResult.sources?.length">
              <n-collapse-item :title="`Kaynaklar (${ragResult.sources.length})`" name="rag-sources">
                <n-list>
                  <n-list-item v-for="source in ragResult.sources" :key="source.id">
                    <n-thing :title="`${source.id} · ${source.document_name}`" :description="source.text" />
                  </n-list-item>
                </n-list>
              </n-collapse-item>
            </n-collapse>
          </n-card>
          <n-card v-if="controlResult?.controls" title="Kontrol sonuçları" embedded size="small">
            <n-list>
              <n-list-item v-for="result in controlResult.controls" :key="result.id">
                <n-thing :title="result.name" :description="result.summary">
                  <template #header-extra><n-tag :type="outcomeType(result.outcome)">{{ result.outcome }}</n-tag></template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>
        </n-space>
      </n-card>
    </section>
  </div>
</template>
