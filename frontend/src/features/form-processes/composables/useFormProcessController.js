import { computed, reactive, ref, unref } from "vue";
import { useDialog } from "naive-ui";

import {
  buildFormProcessPayload,
  createFormProcessForm,
  flattenFormTemplates,
  formProcessRecordToForm,
  selectFormProcessTemplate
} from "../model/form";
import { filterFormProcessRecords } from "../model/selectors";
import { validateFormProcessForm } from "../model/validation";

export function useFormProcessController({ records, processes, onSave, onDelete }) {
  const dialog = useDialog();
  const filters = reactive({ search: "", process: null, template: null, status: null });
  const showEditor = ref(false);
  const editingId = ref(null);
  const formError = ref("");
  const form = reactive(createFormProcessForm());
  const templates = computed(() => flattenFormTemplates(unref(processes)));
  const filteredRecords = computed(() => filterFormProcessRecords(unref(records), filters));

  function openEditor(record = null) {
    const availableTemplates = templates.value;
    editingId.value = record?.id ?? null;
    Object.assign(
      form,
      record
        ? formProcessRecordToForm(record, availableTemplates)
        : createFormProcessForm(availableTemplates[0])
    );
    formError.value = "";
    showEditor.value = true;
  }

  function changeTemplate(templateCode) {
    const template = templates.value.find((item) => item.code === templateCode);
    if (template) selectFormProcessTemplate(form, template);
  }

  function submit() {
    formError.value = validateFormProcessForm(form, templates.value);
    if (formError.value) return;
    onSave({
      id: editingId.value,
      payload: buildFormProcessPayload(form),
      done: () => {
        showEditor.value = false;
      }
    });
  }

  function download(record) {
    const link = document.createElement("a");
    link.href = record.generated_document_url;
    link.download = `${record.template_code}_${record.record_number}.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  function requestDelete(record) {
    dialog.warning({
      title: "Form kaydını sil",
      content: `“${record.record_number} — ${record.title}” kaydı kalıcı olarak silinecek.`,
      positiveText: "Sil",
      negativeText: "Vazgeç",
      positiveButtonProps: { type: "error" },
      onPositiveClick: () => onDelete(record)
    });
  }

  return {
    filters,
    showEditor,
    editingId,
    formError,
    form,
    templates,
    filteredRecords,
    openEditor,
    changeTemplate,
    submit,
    download,
    requestDelete
  };
}
