<script setup>
import { onMounted } from "vue";
import { Files } from "@lucide/vue";
import { useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import FlightPermitsScreen from "../../flight-permits/components/FlightPermitsScreen.vue";
import { useFlightPermits } from "../../flight-permits/composables/useFlightPermits";
import FormProcessesScreen from "../../form-processes/components/FormProcessesScreen.vue";
import { useFormProcesses } from "../../form-processes/composables/useFormProcesses";

const { api } = useAppContext();
const router = useRouter();
const formProcesses = useFormProcesses(api.apiFetch);
const flightPermits = useFlightPermits(api.apiFetch);

onMounted(() => {
  formProcesses.load();
  flightPermits.loadPermits();
});
</script>

<template>
  <div class="process-app-page">
    <n-page-header
      title="Formlar"
      subtitle="Mühendislik formlarını ve uçuş izinlerini tek çalışma alanından yönetin."
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
      @refresh="formProcesses.load"
      @create="router.push({ name: 'form-process-new' })"
      @edit="
        (record) => router.push({ name: 'form-process-edit', params: { recordId: record.id } })
      "
      @status="formProcesses.updateStatus"
      @delete="formProcesses.remove"
    />

    <FlightPermitsScreen
      :permits="flightPermits.permits.value"
      :templates="flightPermits.templates.value"
      :loading="flightPermits.loading.value"
      :saving="flightPermits.saving.value"
      :error="flightPermits.error.value"
      :notice="flightPermits.notice.value"
      @refresh="flightPermits.loadPermits"
      @save="flightPermits.savePermit"
      @delete="flightPermits.deletePermit"
    />
  </div>
</template>
