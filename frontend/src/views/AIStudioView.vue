<script setup>
import { computed, nextTick, ref, watch } from "vue";

const props = defineProps({
  status: { type: Object, default: null },
  loadingStatus: Boolean,
  installing: Boolean,
  unloading: Boolean,
  generating: Boolean,
  error: { type: String, default: "" },
  notice: { type: String, default: "" },
  input: { type: String, default: "" },
  systemPrompt: { type: String, default: "" },
  images: { type: Array, required: true },
  messages: { type: Array, required: true },
  toolsText: { type: String, default: "" },
  settings: { type: Object, required: true },
  canManage: Boolean
});

const emit = defineEmits([
  "refresh",
  "install",
  "unload",
  "send",
  "stop",
  "clear",
  "add-images",
  "remove-image",
  "update:input",
  "update:system-prompt",
  "update:tools-text"
]);

const chatEnd = ref(null);
const connectionType = computed(() => {
  if (!props.status?.connected) return "error";
  if (!props.status?.installed) return "warning";
  return "success";
});
const connectionLabel = computed(() => {
  if (!props.status?.connected) return "Ollama çevrimdışı";
  if (!props.status?.installed) return "Model kurulmalı";
  return props.status.loaded ? "Model bellekte" : "Model hazır";
});

watch(
  () => props.messages.map((message) => `${message.content?.length}:${message.thinking?.length}`),
  () => nextTick(() => chatEnd.value?.scrollIntoView({ behavior: "smooth" }))
);

function onFiles(event) {
  emit("add-images", event.target.files);
  event.target.value = "";
}

function submit() {
  emit("send");
}

function onComposerKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    submit();
  }
}

function speed(stats) {
  if (!stats?.evalDuration) return "—";
  return `${(stats.outputTokens / (stats.evalDuration / 1e9)).toFixed(1)} tok/sn`;
}

function duration(stats) {
  return stats?.totalDuration ? `${(stats.totalDuration / 1e9).toFixed(1)} sn` : "—";
}
</script>

<template>
  <section class="ai-studio-view">
    <header class="ai-studio-header">
      <div class="page-heading">
        <p>Yerel AI</p>
        <h1>Gemma 4 Studio</h1>
        <span>Metin, görsel, düşünme, yapılandırılmış çıktı ve araç çağrılarını tek alanda test edin.</span>
      </div>
      <n-space align="center">
        <n-tag :type="connectionType" round>{{ connectionLabel }}</n-tag>
        <n-button secondary :loading="loadingStatus" @click="emit('refresh')">Yenile</n-button>
      </n-space>
    </header>

    <n-alert v-if="error" type="error" title="AI Studio hatası" closable>{{ error }}</n-alert>
    <n-alert v-else-if="notice" type="success" title="İşlem bilgisi">{{ notice }}</n-alert>

    <div class="ai-studio-layout">
      <aside class="ai-control-panel">
        <n-card title="Model durumu" size="small">
          <n-descriptions :column="1" bordered size="small">
            <n-descriptions-item label="Model">{{ status?.configured_model || "gemma4:e4b" }}</n-descriptions-item>
            <n-descriptions-item label="Ollama">{{ status?.version || "—" }}</n-descriptions-item>
            <n-descriptions-item label="Adres">{{ status?.base_url || "—" }}</n-descriptions-item>
            <n-descriptions-item label="Kurulum">{{ status?.installed ? "Kurulu" : "Eksik" }}</n-descriptions-item>
            <n-descriptions-item label="Bellek">{{ status?.loaded ? "Yüklü" : "Boşta" }}</n-descriptions-item>
          </n-descriptions>
          <n-space class="ai-model-actions">
            <n-button
              v-if="canManage && !status?.installed"
              type="primary"
              :loading="installing"
              :disabled="!status?.connected"
              @click="emit('install')"
            >
              Modeli Kur
            </n-button>
            <n-button
              v-if="canManage && status?.loaded"
              secondary
              :loading="unloading"
              @click="emit('unload')"
            >
              Bellekten Çıkar
            </n-button>
          </n-space>
        </n-card>

        <n-card title="Çalışma ayarları" size="small">
          <n-form label-placement="top" size="small">
            <n-form-item label="Sistem prompt'u">
              <n-input
                :value="systemPrompt"
                type="textarea"
                :autosize="{ minRows: 3, maxRows: 7 }"
                @update:value="emit('update:system-prompt', $event)"
              />
            </n-form-item>
            <div class="ai-form-grid">
              <n-form-item label="Temperature">
                <n-input-number v-model:value="settings.temperature" :min="0" :max="2" :step="0.05" />
              </n-form-item>
              <n-form-item label="Top P">
                <n-input-number v-model:value="settings.topP" :min="0" :max="1" :step="0.05" />
              </n-form-item>
              <n-form-item label="Top K">
                <n-input-number v-model:value="settings.topK" :min="0" :max="200" />
              </n-form-item>
              <n-form-item label="Çıktı token">
                <n-input-number v-model:value="settings.numPredict" :min="-1" :max="32768" />
              </n-form-item>
              <n-form-item label="Bağlam">
                <n-select
                  v-model:value="settings.numCtx"
                  :options="[
                    { label: '8K', value: 8192 },
                    { label: '32K', value: 32768 },
                    { label: '64K', value: 65536 },
                    { label: '128K', value: 131072 }
                  ]"
                />
              </n-form-item>
              <n-form-item label="Keep alive">
                <n-select
                  v-model:value="settings.keepAlive"
                  :options="[
                    { label: 'Kapalı', value: '0' },
                    { label: '5 dakika', value: '5m' },
                    { label: '30 dakika', value: '30m' },
                    { label: '1 saat', value: '1h' }
                  ]"
                />
              </n-form-item>
            </div>
            <n-space vertical>
              <n-checkbox v-model:checked="settings.think">Düşünme modunu kullan</n-checkbox>
              <n-checkbox
                :checked="settings.responseFormat === 'json'"
                @update:checked="settings.responseFormat = $event ? 'json' : 'text'"
              >
                JSON çıktı zorla
              </n-checkbox>
            </n-space>
            <n-collapse class="ai-advanced-tools">
              <n-collapse-item title="Araç şemaları (ileri seviye)" name="tools">
                <n-input
                  :value="toolsText"
                  type="textarea"
                  placeholder='[{"type":"function","function":{"name":"...","description":"...","parameters":{...}}}]'
                  :autosize="{ minRows: 4, maxRows: 10 }"
                  @update:value="emit('update:tools-text', $event)"
                />
                <small>Modelin araç çağrısı üretmesini sınar; uygulama çağrıyı otomatik çalıştırmaz.</small>
              </n-collapse-item>
            </n-collapse>
          </n-form>
        </n-card>
      </aside>

      <main class="ai-chat-panel">
        <div class="ai-chat-toolbar">
          <div>
            <strong>Test oturumu</strong>
            <span>{{ messages.length ? `${messages.length} mesaj` : "Yeni konuşma" }}</span>
          </div>
          <n-button text :disabled="!messages.length" @click="emit('clear')">Konuşmayı Temizle</n-button>
        </div>

        <div class="ai-message-list">
          <div v-if="!messages.length" class="ai-empty-state">
            <div class="ai-orbit">G4</div>
            <h2>Gemma 4 E4B hazır</h2>
            <p>Bir teknik soru sorun, görsel yükleyin veya yapılandırılmış çıktı deneyin.</p>
            <div class="ai-prompt-chips">
              <button @click="emit('update:input', 'Bir İHA uçuş kontrol sistemi için emniyet gereksinimlerini listele.')">Gereksinim üret</button>
              <button @click="emit('update:input', 'Bu Python fonksiyonunu daha güvenli ve hızlı hale getirmek için nasıl incelemeliyim?')">Kod analizi</button>
              <button @click="emit('update:input', 'Karmaşık bir teknik dokümanı yönetici özeti biçiminde nasıl yapılandırmalıyım?')">Doküman özeti</button>
            </div>
          </div>

          <article
            v-for="(message, index) in messages"
            :key="index"
            class="ai-message"
            :class="`ai-message-${message.role}`"
          >
            <div class="ai-message-avatar">{{ message.role === "user" ? "Siz" : "G4" }}</div>
            <div class="ai-message-body">
              <div class="ai-message-label">{{ message.role === "user" ? "Kullanıcı" : "Gemma 4" }}</div>
              <div v-if="message.imageNames?.length" class="ai-message-images">
                <n-tag v-for="name in message.imageNames" :key="name" size="small">{{ name }}</n-tag>
              </div>
              <n-collapse v-if="message.thinking" class="ai-thinking">
                <n-collapse-item title="Düşünme izi" name="thinking">
                  <pre>{{ message.thinking }}</pre>
                </n-collapse-item>
              </n-collapse>
              <div v-if="message.content" class="ai-message-content">{{ message.content }}</div>
              <n-spin v-else-if="generating && index === messages.length - 1" size="small" />
              <div v-if="message.toolCalls?.length" class="ai-tool-calls">
                <strong>Araç çağrıları</strong>
                <pre>{{ JSON.stringify(message.toolCalls, null, 2) }}</pre>
              </div>
              <n-alert v-if="message.error" type="error" size="small">{{ message.error }}</n-alert>
              <div v-if="message.stats" class="ai-message-stats">
                <span>{{ message.stats.promptTokens }} giriş</span>
                <span>{{ message.stats.outputTokens }} çıkış</span>
                <span>{{ speed(message.stats) }}</span>
                <span>{{ duration(message.stats) }}</span>
              </div>
              <small v-if="message.stopped">Üretim kullanıcı tarafından durduruldu.</small>
            </div>
          </article>
          <div ref="chatEnd"></div>
        </div>

        <div class="ai-composer">
          <div v-if="images.length" class="ai-image-queue">
            <div v-for="(image, index) in images" :key="image.name" class="ai-image-preview">
              <img :src="image.dataUrl" :alt="image.name" />
              <span>{{ image.name }}</span>
              <n-button text size="tiny" @click="emit('remove-image', index)">Kaldır</n-button>
            </div>
          </div>
          <n-input
            :value="input"
            type="textarea"
            placeholder="Gemma 4'e mesaj yazın…"
            :autosize="{ minRows: 3, maxRows: 8 }"
            :disabled="generating"
            @update:value="emit('update:input', $event)"
            @keydown="onComposerKeydown"
          />
          <div class="ai-composer-actions">
            <label class="ai-file-button">
              Görsel Ekle
              <input type="file" accept="image/*" multiple :disabled="generating" @change="onFiles" />
            </label>
            <span>⌘/Ctrl + Enter ile gönder</span>
            <n-button v-if="generating" type="error" @click="emit('stop')">Durdur</n-button>
            <n-button
              v-else
              type="primary"
              :disabled="(!input.trim() && !images.length) || !status?.installed"
              @click="submit"
            >
              Gönder
            </n-button>
          </div>
        </div>
      </main>
    </div>
  </section>
</template>
