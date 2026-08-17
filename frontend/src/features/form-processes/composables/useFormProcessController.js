import { computed, reactive, unref } from "vue";
import { useDialog } from "naive-ui";

import { flattenFormTemplates } from "../model/form";
import { filterFormProcessRecords } from "../model/selectors";

export function useFormProcessController({ records, processes, onEdit, onDelete, onStatus }) {
  const dialog = useDialog();
  const filters = reactive({ search: "", process: null, template: null, status: null });
  const templates = computed(() => flattenFormTemplates(unref(processes)));
  const filteredRecords = computed(() => filterFormProcessRecords(unref(records), filters));

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

  function requestArchive(record) {
    dialog.warning({
      title: "Form kaydını arşivle",
      content: `“${record.record_number} — ${record.title}” kaydı arşivlenecek.`,
      positiveText: "Arşivle",
      negativeText: "Vazgeç",
      onPositiveClick: () => onStatus(record, "archived")
    });
  }

  return {
    filters,
    templates,
    filteredRecords,
    edit: onEdit,
    download,
    requestDelete,
    requestArchive,
    reopen: (record) => onStatus(record, "draft")
  };
}
