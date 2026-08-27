<script setup>
import { Download, X } from "@lucide/vue";
import { onMounted, onUnmounted, ref } from "vue";

import { usePwaInstall } from "../pwa/usePwaInstall";

const showManualInstructions = ref(false);
const { shouldShow, isManualInstall, isInstalling, error, start, stop, dismiss, requestInstall } =
  usePwaInstall();

async function handleInstall() {
  if (isManualInstall.value) {
    showManualInstructions.value = true;
    return;
  }
  await requestInstall();
}

onMounted(start);
onUnmounted(stop);
</script>

<template>
  <aside v-if="shouldShow" class="pwa-install-prompt" aria-live="polite">
    <div class="pwa-install-icon" aria-hidden="true"><Download :size="22" /></div>
    <div class="pwa-install-copy">
      <strong>UAV Center’ı yükleyin</strong>
      <span v-if="showManualInstructions">
        Safari’de Paylaş menüsünü açıp “Ana Ekrana Ekle” seçeneğini kullanın.
      </span>
      <span v-else>Uygulamaya cihazınızdan hızlıca ve bağımsız bir pencerede erişin.</span>
      <small v-if="error">{{ error }}</small>
    </div>
    <n-button
      v-if="!error"
      size="small"
      type="primary"
      :loading="isInstalling"
      @click="handleInstall"
    >
      {{ isManualInstall ? "Nasıl yüklenir?" : "Uygulamayı yükle" }}
    </n-button>
    <n-button
      quaternary
      circle
      size="small"
      title="Yükleme önerisini kapat"
      aria-label="Yükleme önerisini kapat"
      @click="dismiss"
    >
      <template #icon><X :size="16" /></template>
    </n-button>
  </aside>
</template>
