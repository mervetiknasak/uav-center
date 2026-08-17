<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";

import { useAppContext } from "../../../app/bootstrap";
import ProcessAppNavigation from "../../processes/components/ProcessAppNavigation.vue";
import FormProcessesScreen from "../components/FormProcessesScreen.vue";
import { useFormProcesses } from "../composables/useFormProcesses";

const { api } = useAppContext();
const router = useRouter();
const formProcesses = useFormProcesses(api.apiFetch);

onMounted(formProcesses.load);
</script>

<template>
  <div class="process-app-page">
    <ProcessAppNavigation />
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
  </div>
</template>
