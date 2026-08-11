import { computed, reactive, ref } from "vue";

import {
  canSubmitOrganizationEditor,
  createOrganizationEditorForm,
  createOrganizationSaveCommand,
  createResponsibleReorder,
  organizationDeletePrompt,
  organizationEditorTitle,
  selectResponsibleForRemoval
} from "../model/editor";

export function useOrganizationController({
  onSave,
  onDelete,
  onReorderResponsibles,
  confirmDelete = (message) => window.confirm(message)
}) {
  const showModal = ref(false);
  const editorType = ref("project");
  const editorId = ref(null);
  const parentId = ref(null);
  const form = reactive({});
  const activeSection = ref("projects");

  const modalTitle = computed(() => organizationEditorTitle(editorType.value, editorId.value));
  const canSubmit = computed(() => canSubmitOrganizationEditor(editorType.value, form));

  function openEditor(type, item = null, parent = null) {
    editorType.value = type;
    editorId.value = item?.id ?? null;
    parentId.value = parent?.id ?? null;
    Object.keys(form).forEach((key) => delete form[key]);
    Object.assign(form, createOrganizationEditorForm(type, item));
    showModal.value = true;
  }

  function updateFormField(field, value) {
    form[field] = value;
  }

  function submit() {
    onSave({
      ...createOrganizationSaveCommand({
        type: editorType.value,
        id: editorId.value,
        parentId: parentId.value,
        form
      }),
      done: () => {
        showModal.value = false;
      }
    });
  }

  function requestDelete(type, item) {
    if (confirmDelete(organizationDeletePrompt(item))) onDelete({ type, item });
  }

  function reorderResponsibles(panel, reorderedItems) {
    const command = createResponsibleReorder(panel, reorderedItems);
    if (command) onReorderResponsibles(command);
  }

  function removeResponsible(panel, index) {
    const item = selectResponsibleForRemoval(panel, index);
    if (item) onDelete({ type: "responsible", item });
  }

  return {
    showModal,
    editorType,
    editorId,
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
  };
}
