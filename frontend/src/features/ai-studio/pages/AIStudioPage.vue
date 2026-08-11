<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import { useOllama } from "../../../composables/useOllama";
import AIStudioView from "../../../views/AIStudioView.vue";

const { api, auth } = useAppContext();
const ollama = useOllama({
  apiFetch: api.apiFetch,
  ensureCsrfToken: api.ensureCsrfToken,
  API_BASE_URL: api.API_BASE_URL
});
const canManage = computed(() => Boolean(auth.currentUser.value?.is_staff));

onMounted(ollama.loadStatus);
onBeforeUnmount(ollama.dispose);
</script>

<template>
  <AIStudioView
    :status="ollama.status.value"
    :loading-status="ollama.loadingStatus.value"
    :installing="ollama.installing.value"
    :unloading="ollama.unloading.value"
    :generating="ollama.generating.value"
    :error="ollama.error.value"
    :notice="ollama.notice.value"
    :input="ollama.input.value"
    :system-prompt="ollama.systemPrompt.value"
    :images="ollama.images.value"
    :messages="ollama.messages.value"
    :tools-text="ollama.toolsText.value"
    :settings="ollama.settings.value"
    :can-manage="canManage"
    @refresh="ollama.loadStatus"
    @install="ollama.installModel"
    @unload="ollama.unloadModel"
    @send="ollama.sendMessage"
    @stop="ollama.stopGeneration"
    @clear="ollama.clearConversation"
    @add-images="ollama.addImages"
    @remove-image="ollama.removeImage"
    @update:input="ollama.input.value = $event"
    @update:system-prompt="ollama.systemPrompt.value = $event"
    @update:tools-text="ollama.toolsText.value = $event"
  />
</template>
