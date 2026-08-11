<script setup>
import { useOrganizationController } from "../composables/useOrganizationController";
import OrganizationEditorModal from "./OrganizationEditorModal.vue";
import OrganizationPersonGroupsSection from "./OrganizationPersonGroupsSection.vue";
import OrganizationProjectsSection from "./OrganizationProjectsSection.vue";

defineProps({
  projects: { type: Array, required: true },
  personGroups: { type: Array, default: () => [] },
  loading: { type: Boolean, required: true },
  saving: { type: Boolean, required: true },
  error: { type: String, default: "" },
  canEdit: { type: Boolean, default: false }
});

const emit = defineEmits(["refresh", "save", "delete", "reorder-responsibles"]);
const {
  showModal,
  editorType,
  form,
  activeSection,
  modalTitle,
  canSubmit,
  openEditor,
  updateFormField,
  submit,
  requestDelete,
  reorderResponsibles,
  removeResponsible
} = useOrganizationController({
  onSave: (payload) => emit("save", payload),
  onDelete: (payload) => emit("delete", payload),
  onReorderResponsibles: (payload) => emit("reorder-responsibles", payload)
});
</script>

<template>
  <section class="organization-view">
    <div class="page-heading organization-heading">
      <div>
        <p>{{ canEdit ? "Yönetim" : "Organizasyon" }}</p>
        <h1>Organizasyon</h1>
        <span>Projeleri, panelleri ve kişi gruplarını tek yerden yönetin.</span>
      </div>
    </div>

    <n-alert v-if="error" type="error" title="Organizasyon bilgileri alınamadı">
      {{ error }}
    </n-alert>

    <n-tabs v-model:value="activeSection" type="segment" animated>
      <n-tab-pane name="projects" tab="Projeler ve Paneller">
        <OrganizationProjectsSection
          :projects="projects"
          :loading="loading"
          :can-edit="canEdit"
          @refresh="emit('refresh')"
          @open-editor="openEditor"
          @request-delete="requestDelete"
          @reorder-responsibles="reorderResponsibles"
          @remove-responsible="removeResponsible"
        />
      </n-tab-pane>

      <n-tab-pane name="groups" tab="Kişi Grupları">
        <OrganizationPersonGroupsSection
          :person-groups="personGroups"
          :loading="loading"
          :can-edit="canEdit"
          @refresh="emit('refresh')"
          @open-editor="openEditor"
          @request-delete="requestDelete"
        />
      </n-tab-pane>
    </n-tabs>

    <OrganizationEditorModal
      v-model:show="showModal"
      :title="modalTitle"
      :editor-type="editorType"
      :form="form"
      :saving="saving"
      :can-submit="canSubmit"
      @update-field="updateFormField"
      @submit="submit"
    />
  </section>
</template>
