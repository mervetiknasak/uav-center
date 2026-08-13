<script setup>
import { onMounted } from "vue";

import { useAppContext } from "../../../app/bootstrap";
import FormProcessesScreen from "../components/FormProcessesScreen.vue";
import { useFormProcesses } from "../composables/useFormProcesses";

const { api } = useAppContext();
const formProcesses = useFormProcesses(api.apiFetch);

onMounted(formProcesses.load);
</script>

<template>
  <FormProcessesScreen
    :records="formProcesses.records.value"
    :processes="formProcesses.processes.value"
    :loading="formProcesses.loading.value"
    :saving="formProcesses.saving.value"
    :error="formProcesses.error.value"
    :notice="formProcesses.notice.value"
    @refresh="formProcesses.load"
    @save="formProcesses.save"
    @delete="formProcesses.remove"
  />
</template>
