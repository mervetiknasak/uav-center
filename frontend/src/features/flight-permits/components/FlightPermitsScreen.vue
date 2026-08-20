<script setup>
import { toRef } from "vue";
import { Plane, Plus, RefreshCw } from "@lucide/vue";

import { useFlightPermitsController } from "../composables/useFlightPermitsController";
import FlightPermitEditor from "./FlightPermitEditor.vue";
import FlightPermitMetrics from "./FlightPermitMetrics.vue";
import FlightPermitTable from "./FlightPermitTable.vue";

const props = defineProps({
  permits: { type: Array, required: true },
  templates: { type: Array, required: true },
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
  serialNumberOptions,
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
  templates: toRef(props, "templates"),
  onSave: (payload) => emit("save", payload),
  onDelete: (permit) => emit("delete", permit)
});

function openDocumentUrl(url) {
  openDocument({ document_url: url });
}
</script>

<template>
  <section class="flight-permits-view">
    <header class="process-section-header">
      <div>
        <n-space align="center" :size="6">
          <n-icon :size="18"><Plane /></n-icon>
          <n-text class="process-section-title" strong>Uçuş İzinleri</n-text>
        </n-space>
        <n-text depth="3">
          Uçuş izni ve tavsiye kayıtlarını, hava aracı bilgilerini ve resmi dokümanlarını yönetin.
        </n-text>
      </div>
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
    </header>

    <n-alert v-if="error" type="error" title="Uçuş izinleri alınamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success" :show-icon="true">{{ notice }}</n-alert>

    <FlightPermitMetrics :metrics="metrics" />
    <FlightPermitTable
      :permits="filteredPermits"
      :filters="filters"
      :serial-number-options="serialNumberOptions"
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
      :templates="templates"
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
