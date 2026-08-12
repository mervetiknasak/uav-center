import { computed, reactive, ref, unref } from "vue";
import { useDialog } from "naive-ui";

import {
  buildFlightPermitPayload,
  createFlightPermitForm,
  flightPermitToForm,
  selectExistingFlightPermitDocument
} from "../model/form";
import {
  calculateFlightPermitMetrics,
  filterFlightPermits,
  selectSerialNumberOptions
} from "../model/selectors";
import { validateFlightPermitFile, validateFlightPermitForm } from "../model/validation";

export function useFlightPermitsController({ permits, onSave, onDelete }) {
  const dialog = useDialog();
  const filters = reactive({
    search: "",
    validityStatus: null,
    recommendation: null,
    serialNumber: null
  });
  const showEditor = ref(false);
  const editingId = ref(null);
  const formError = ref("");
  const fileList = ref([]);
  const existingDocument = ref(null);
  const removeDocument = ref(false);
  const form = reactive(createFlightPermitForm());

  const serialNumberOptions = computed(() => selectSerialNumberOptions(unref(permits)));
  const filteredPermits = computed(() => filterFlightPermits(unref(permits), filters));
  const metrics = computed(() => calculateFlightPermitMetrics(unref(permits)));

  function openDocument(permit) {
    if (!permit.document_url) return;
    const opened = window.open(permit.document_url, "_blank", "noopener,noreferrer");
    if (opened) opened.opener = null;
  }

  function downloadGeneratedPermit(permit) {
    const link = document.createElement("a");
    link.href = permit.generated_document_url;
    link.download = `Ucus_Izni_${permit.serial_number || "hava_araci"}_${permit.permit_number}.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  function openEditor(permit = null) {
    editingId.value = permit?.id ?? null;
    Object.assign(form, flightPermitToForm(permit));
    fileList.value = [];
    existingDocument.value = selectExistingFlightPermitDocument(permit);
    removeDocument.value = false;
    formError.value = "";
    showEditor.value = true;
  }

  function submitPermit() {
    const file = fileList.value[0]?.file || null;
    formError.value = validateFlightPermitForm(form) || validateFlightPermitFile(file);
    if (formError.value) return;
    onSave({
      id: editingId.value,
      payload: buildFlightPermitPayload(form),
      file,
      removeDocument: removeDocument.value,
      done: () => {
        showEditor.value = false;
      }
    });
  }

  function requestDelete(permit) {
    dialog.warning({
      title: "Uçuş iznini sil",
      content: `“${permit.permit_number} — ${permit.serial_number || "seri numarası yok"}” kaydı${permit.document_url ? " ve ekli dokümanı" : ""} kalıcı olarak silinecek.`,
      positiveText: "Sil",
      negativeText: "Vazgeç",
      positiveButtonProps: { type: "error" },
      onPositiveClick: () => onDelete(permit)
    });
  }

  function markDocumentForRemoval() {
    existingDocument.value = null;
    removeDocument.value = true;
  }

  function updateFileList(files) {
    fileList.value = files.slice(-1);
    if (fileList.value.length) removeDocument.value = false;
  }

  return {
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
  };
}
