<script setup>
import { toRef } from "vue";
import { Plane, Plus, RefreshCw } from "@lucide/vue";

import { useFlightPermitsController } from "../composables/useFlightPermitsController";
import FlightPermitEditor from "./FlightPermitEditor.vue";
import FlightPermitMetrics from "./FlightPermitMetrics.vue";
import FlightPermitTable from "./FlightPermitTable.vue";

const props = defineProps({
  permits: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  notice: { type: String, default: "" }
});

const emit = defineEmits(["refresh", "save", "delete"]);
const {
  filters,
  showEditor,
  editingId,
  formError,
  fileList,
  existingDocument,
  form,
  aircraftOptions,
  filteredPermits,
  metrics,
  openDocument,
  downloadGeneratedPermit,
  openEditor,
  submitPermit,
  requestDelete,
  markDocumentForRemoval,
  updateFileList
} = useFlightPermitsController({
  permits: toRef(props, "permits"),
  onSave: (payload) => emit("save", payload),
  onDelete: (permit) => emit("delete", permit)
});

function openDocumentUrl(url) {
  openDocument({ document_url: url });
}
</script>

<template>
  <section class="flight-permits-view">
    <n-page-header
      title="Uçuş İzinleri"
      subtitle="Uçak bazlı izinleri, geçerlilik sürelerini ve resmi dokümanlarını tek merkezden yönetin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="16"><Plane /></n-icon>
          <n-text type="primary" strong>Uçuş Operasyonları</n-text>
        </n-space>
      </template>
      <template #extra>
        <n-space>
          <n-button secondary :loading="loading" @click="emit('refresh')">
            <template #icon
              ><n-icon><RefreshCw /></n-icon
            ></template>
            Yenile
          </n-button>
          <n-button type="primary" @click="openEditor()">
            <template #icon
              ><n-icon><Plus /></n-icon
            ></template>
            Yeni uçuş izni
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="Uçuş izinleri alınamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success" :show-icon="true">{{ notice }}</n-alert>

    <FlightPermitMetrics :metrics="metrics" />
    <FlightPermitTable
      :permits="filteredPermits"
      :filters="filters"
      :aircraft-options="aircraftOptions"
      :loading="loading"
      @open-document="openDocument"
      @download="downloadGeneratedPermit"
      @open-editor="openEditor"
      @request-delete="requestDelete"
    />
    <FlightPermitEditor
      v-model:show="showEditor"
      :editing-id="editingId"
      :form="form"
      :form-error="formError"
      :file-list="fileList"
      :existing-document="existingDocument"
      :saving="saving"
      @submit="submitPermit"
      @open-document="openDocumentUrl"
      @remove-document="markDocumentForRemoval"
      @update:file-list="updateFileList"
    />
  </section>
</template>
