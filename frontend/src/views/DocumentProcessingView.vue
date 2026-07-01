<script setup>
import { computed } from "vue";

const props = defineProps({
  documents: { type: Array, required: true },
  loading: Boolean,
  prompt: { type: String, required: true },
  uploadError: { type: String, default: "" },
  activeDocument: { type: Object, default: null },
  deletingDocumentId: { type: Number, default: null }
});

const emit = defineEmits(["update:prompt", "upload", "open", "delete"]);
const documentStatus = computed(() => {
  if (!props.activeDocument) return "Henüz belge seçilmedi";
  if (props.activeDocument.status === "processed") return "Belge işlendi";
  if (props.activeDocument.status === "failed") return "Belge işlenemedi";
  return "Belge sırada";
});

function formatBytes(size) {
  if (!size) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
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
          <n-upload directory-dnd :max="1" :custom-request="(options) => emit('upload', options)" accept=".pdf,.docx,.xlsx,.pptx,.txt,.csv,.md">
            <n-upload-dragger>
              <div class="upload-title">Dosyayı buraya bırakın</div>
              <div class="upload-subtitle">veya yerel dosya seçiciyi açmak için tıklayın</div>
            </n-upload-dragger>
          </n-upload>
          <n-input
            :value="prompt"
            type="textarea"
            :autosize="{ minRows: 4, maxRows: 8 }"
            placeholder="Belge için prompt girin"
            @update:value="emit('update:prompt', $event)"
          />
          <n-alert v-if="uploadError" type="error" title="Yükleme hatası">{{ uploadError }}</n-alert>
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
    </section>

    <section id="ai-results" class="result-panel">
      <n-card title="AI İşleme Sonucu" size="small">
        <n-empty v-if="!activeDocument" description="Bir belge yükleyin veya listeden seçin" />
        <n-space v-else vertical :size="16">
          <n-alert :type="activeDocument.status === 'processed' ? 'success' : 'error'" :title="documentStatus">
            <span v-if="activeDocument.status === 'failed'">{{ activeDocument.error_message }}</span>
            <span v-else>{{ activeDocument.original_name }} içeriği yerelde çıkarıldı ve işlendi.</span>
          </n-alert>
          <n-descriptions :column="2" bordered size="small">
            <n-descriptions-item label="Karakter">{{ activeDocument.ai_result?.metrics?.characters ?? activeDocument.text_length }}</n-descriptions-item>
            <n-descriptions-item label="Kelime">{{ activeDocument.ai_result?.metrics?.words ?? "-" }}</n-descriptions-item>
            <n-descriptions-item label="Sağlayıcı">{{ activeDocument.ai_result?.provider ?? "local" }}</n-descriptions-item>
            <n-descriptions-item label="Boyut">{{ formatBytes(activeDocument.size) }}</n-descriptions-item>
          </n-descriptions>
          <div><h2>Prompt</h2><p class="summary-text">{{ activeDocument.prompt || activeDocument.ai_result?.prompt || "-" }}</p></div>
          <div><h2>Model Yanıtı</h2><p class="summary-text">{{ activeDocument.ai_result?.response || activeDocument.ai_result?.summary || "-" }}</p></div>
          <div v-if="activeDocument.ai_result?.preview"><h2>Metin Ön İzleme</h2><p class="summary-text">{{ activeDocument.ai_result.preview }}</p></div>
          <div v-if="activeDocument.ai_result?.keywords?.length">
            <h2>Anahtar Kelimeler</h2>
            <n-space><n-tag v-for="keyword in activeDocument.ai_result.keywords" :key="keyword" type="info">{{ keyword }}</n-tag></n-space>
          </div>
          <n-collapse><n-collapse-item title="Çıkarılan metin" name="text"><pre class="extracted-text">{{ activeDocument.extracted_text }}</pre></n-collapse-item></n-collapse>
        </n-space>
      </n-card>
    </section>
  </div>
</template>
