<script setup>
import { toRef } from "vue";
import { FileText, Plus, RefreshCw } from "@lucide/vue";

import { useTechnicalDocumentsController } from "../composables/useTechnicalDocumentsController";
import TechnicalDocumentDetails from "./TechnicalDocumentDetails.vue";
import TechnicalDocumentEditor from "./TechnicalDocumentEditor.vue";
import TechnicalDocumentMetrics from "./TechnicalDocumentMetrics.vue";
import TechnicalDocumentNotification from "./TechnicalDocumentNotification.vue";
import TechnicalDocumentTable from "./TechnicalDocumentTable.vue";

const props = defineProps({
  projects: { type: Array, required: true },
  documents: { type: Array, required: true },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  notifyingId: { type: Number, default: null },
  error: { type: String, default: "" },
  notice: { type: String, default: "" },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "save", "delete", "notify"]);
const {
  activeProjectId,
  filters,
  showEditor,
  showDetail,
  showNotify,
  editingId,
  detailDocument,
  notifyDocument,
  formError,
  notifyForm,
  form,
  activeProject,
  panelOptions,
  categoryOptions,
  filteredDocuments,
  metrics,
  projectDocumentCount,
  isOverdue,
  selectProject,
  openEditor,
  submitDocument,
  requestDelete,
  openDetails,
  openNotification,
  submitNotification,
  updateStatus
} = useTechnicalDocumentsController({
  projects: toRef(props, "projects"),
  documents: toRef(props, "documents"),
  onSave: (payload) => emit("save", payload),
  onDelete: (document) => emit("delete", document),
  onNotify: (payload) => emit("notify", payload)
});
</script>

<template>
  <section class="technical-documents-view">
    <n-page-header
      class="td-page-header"
      title="Teknik Dokümanlar"
      subtitle="Yayın, revizyon ve panel sorumluluklarını proje bazında tek merkezden takip edin."
    >
      <template #header>
        <n-space align="center" :size="6">
          <n-icon :size="15"><FileText /></n-icon>
          <n-text type="primary" strong>Doküman Yönetimi</n-text>
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
          <n-button v-if="canEdit" type="primary" :disabled="!activeProject" @click="openEditor()">
            <template #icon
              ><n-icon><Plus /></n-icon
            ></template>
            Yeni doküman
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-alert v-if="error" type="error" title="Teknik dokümanlar alınamadı">{{ error }}</n-alert>
    <n-alert v-if="notice" type="success" :show-icon="true">{{ notice }}</n-alert>

    <n-empty
      v-if="!projects.length"
      description="Önce Organizasyon Yönetimi alanından bir proje oluşturun."
    />

    <template v-else>
      <n-tabs
        class="td-project-tabs"
        type="segment"
        :value="activeProjectId"
        @update:value="selectProject"
      >
        <n-tab v-for="project in projects" :key="project.id" :name="project.id">
          <n-space align="center" :size="8">
            <n-tag size="small" type="primary" :bordered="false">{{ project.code }}</n-tag>
            <n-text strong>{{ project.name }}</n-text>
            <n-badge :value="projectDocumentCount(project.id)" :max="99" />
          </n-space>
        </n-tab>
      </n-tabs>

      <n-spin :show="loading">
        <TechnicalDocumentMetrics :metrics="metrics" :project-code="activeProject?.code || ''" />
        <TechnicalDocumentTable
          :documents="filteredDocuments"
          :filters="filters"
          :panel-options="panelOptions"
          :category-options="categoryOptions"
          :project-name="activeProject?.name || ''"
          :loading="loading"
          :can-edit="canEdit"
          :notifying-id="notifyingId"
          :is-overdue="isOverdue"
          @open-detail="openDetails"
          @open-notification="openNotification"
          @open-editor="openEditor"
          @request-delete="requestDelete"
          @update-status="updateStatus"
        />
      </n-spin>
    </template>

    <TechnicalDocumentEditor
      v-model:show="showEditor"
      :editing-id="editingId"
      :form="form"
      :projects="projects"
      :panel-options="panelOptions"
      :form-error="formError"
      :saving="saving"
      @submit="submitDocument"
    />
    <TechnicalDocumentDetails v-model:show="showDetail" :document="detailDocument" />
    <TechnicalDocumentNotification
      v-model:show="showNotify"
      :document="notifyDocument"
      :form="notifyForm"
      :notifying-id="notifyingId"
      @submit="submitNotification"
    />
  </section>
</template>
