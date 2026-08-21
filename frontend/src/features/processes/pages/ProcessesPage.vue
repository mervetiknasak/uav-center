<script setup>
import { onMounted, ref } from "vue";
import { Files } from "@lucide/vue";
import { useRoute, useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import FormProcessesScreen from "../../form-processes/components/FormProcessesScreen.vue";
import { useFormProcesses } from "../../form-processes/composables/useFormProcesses";
import { resolveFlightPermitDeepLink } from "../model/flightPermitDeepLink";

const { api } = useAppContext();
const route = useRoute();
const router = useRouter();
const formProcesses = useFormProcesses(api.apiFetch);
const deepLinkError = ref("");

async function loadPage() {
  deepLinkError.value = "";
  await formProcesses.load();
  if (formProcesses.error.value) return;

  const target = resolveFlightPermitDeepLink(route.query.flightPermit, formProcesses.records.value);
  deepLinkError.value = target.error;
  if (target.record) {
    await router.replace({
      name: "form-process-edit",
      params: { recordId: target.record.id }
    });
  }
}

onMounted(loadPage);
</script>

<template>
  <div class="process-app-page">
    <n-page-header
      title="Formlar"
      subtitle="Mühendislik formlarını ve uçuş izni kayıtlarını tek katalogdan yönetin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="16"><Files /></n-icon>
          <n-text type="primary" strong>Süreçler</n-text>
        </n-space>
      </template>
    </n-page-header>

    <FormProcessesScreen
      :records="formProcesses.records.value"
      :processes="formProcesses.processes.value"
      :loading="formProcesses.loading.value"
      :error="formProcesses.error.value"
      :notice="formProcesses.notice.value"
      :deep-link-error="deepLinkError"
      @refresh="loadPage"
      @create="router.push({ name: 'form-process-new' })"
      @edit="
        (record) => router.push({ name: 'form-process-edit', params: { recordId: record.id } })
      "
      @status="formProcesses.updateStatus"
      @delete="formProcesses.remove"
    />
  </div>
</template>
