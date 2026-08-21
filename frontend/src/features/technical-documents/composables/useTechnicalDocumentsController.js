import { computed, reactive, ref, unref, watch } from "vue";
import { useDialog } from "naive-ui";

import { isoDateKey } from "../model/formatters";
import {
  buildTechnicalDocumentPayload,
  createTechnicalDocumentForm,
  createTechnicalDocumentNotification,
  technicalDocumentToForm,
  validateTechnicalDocumentForm
} from "../model/form";
import {
  calculateTechnicalDocumentMetrics,
  countTechnicalDocumentsForProject,
  filterTechnicalDocuments,
  isTechnicalDocumentOverdue,
  selectProjectDocuments,
  selectTechnicalDocumentCategories
} from "../model/selectors";

export function useTechnicalDocumentsController({
  projects,
  documents,
  deepLinkReady,
  deepLinkRequested,
  deepLinkDocumentId,
  deepLinkAction,
  canNotify,
  onSave,
  onDelete,
  onNotify
}) {
  const dialog = useDialog();
  const activeProjectId = ref(null);
  const filters = reactive({
    search: "",
    status: null,
    panelId: null,
    category: null
  });
  const showEditor = ref(false);
  const showDetail = ref(false);
  const showNotify = ref(false);
  const editingId = ref(null);
  const detailDocument = ref(null);
  const notifyDocument = ref(null);
  const deepLinkWarning = ref("");
  const formError = ref("");
  const notifyForm = reactive({ subject: "", message: "" });
  const form = reactive(createTechnicalDocumentForm());
  const today = isoDateKey();
  let handledDeepLink = "";

  watch(
    () => unref(projects),
    (items) => {
      if (!items.length) {
        activeProjectId.value = null;
        return;
      }
      if (!items.some((project) => project.id === activeProjectId.value)) {
        activeProjectId.value = items[0].id;
      }
    },
    { immediate: true }
  );

  const activeProject = computed(
    () => unref(projects).find((project) => project.id === activeProjectId.value) || null
  );
  const projectDocuments = computed(() =>
    selectProjectDocuments(unref(documents), activeProjectId.value)
  );
  const panelOptions = computed(() =>
    (activeProject.value?.panels || []).map((panel) => ({ label: panel.name, value: panel.id }))
  );
  const categoryOptions = computed(() => selectTechnicalDocumentCategories(projectDocuments.value));
  const filteredDocuments = computed(() =>
    filterTechnicalDocuments(projectDocuments.value, filters)
  );
  const metrics = computed(() => calculateTechnicalDocumentMetrics(projectDocuments.value, today));

  function projectDocumentCount(projectId) {
    return countTechnicalDocumentsForProject(unref(documents), projectId);
  }

  function isOverdue(document) {
    return isTechnicalDocumentOverdue(document, today);
  }

  function selectProject(projectId) {
    activeProjectId.value = projectId;
    Object.assign(filters, { search: "", status: null, panelId: null, category: null });
  }

  function openEditor(document = null) {
    editingId.value = document?.id ?? null;
    Object.assign(form, technicalDocumentToForm(document, activeProjectId.value));
    formError.value = "";
    showEditor.value = true;
  }

  function submitDocument() {
    formError.value = validateTechnicalDocumentForm(form);
    if (formError.value) return;
    onSave({
      id: editingId.value,
      payload: buildTechnicalDocumentPayload(form),
      done: () => {
        showEditor.value = false;
      }
    });
  }

  function requestDelete(document) {
    dialog.warning({
      title: "Teknik dokümanı sil",
      content: `“${document.code} — ${document.title}” dokümanı ve denetim geçmişi silinecek.`,
      positiveText: "Sil",
      negativeText: "Vazgeç",
      positiveButtonProps: { type: "error" },
      onPositiveClick: () => onDelete(document)
    });
  }

  function openDetails(document) {
    detailDocument.value = document;
    showDetail.value = true;
  }

  function openNotification(document) {
    notifyDocument.value = document;
    Object.assign(notifyForm, createTechnicalDocumentNotification(document));
    showNotify.value = true;
  }

  function submitNotification() {
    if (!notifyDocument.value) return;
    onNotify({
      document: notifyDocument.value,
      payload: { ...notifyForm },
      done: () => {
        showNotify.value = false;
      }
    });
  }

  function updateStatus(document, status) {
    if (status === document.status) return;
    if (status === "published" && !document.publication_date) {
      openEditor({ ...document, status: "published", publication_date: today });
      return;
    }
    onSave({
      id: document.id,
      payload: { status, status_note: "Doküman tablosundan durum güncellendi." }
    });
  }

  watch(
    () => [
      Boolean(unref(deepLinkReady)),
      Boolean(unref(deepLinkRequested)),
      unref(deepLinkDocumentId),
      unref(deepLinkAction),
      Boolean(unref(canNotify)),
      unref(documents),
      unref(projects)
    ],
    ([ready, requested, documentId, action, notificationAllowed]) => {
      if (!requested) {
        handledDeepLink = "";
        deepLinkWarning.value = "";
        return;
      }
      if (!ready) {
        handledDeepLink = "";
        return;
      }

      const deepLinkKey = `${documentId || "invalid"}:${action}`;
      if (handledDeepLink === deepLinkKey) return;
      handledDeepLink = deepLinkKey;
      deepLinkWarning.value = "";

      if (!documentId) {
        deepLinkWarning.value = "Teknik doküman bağlantısı geçersiz. Kayıt listesi gösteriliyor.";
        return;
      }
      const document = unref(documents).find((item) => item.id === documentId);
      if (!document) {
        deepLinkWarning.value =
          "İstenen teknik doküman bulunamadı veya bu kaydı görüntüleme yetkiniz yok. Kayıt listesi gösteriliyor.";
        return;
      }

      selectProject(document.project);
      if (action === "notify") {
        if (!notificationAllowed) {
          deepLinkWarning.value =
            "Bu teknik doküman için bildirim hazırlama yetkiniz yok. Kayıt listesi gösteriliyor.";
          return;
        }
        openNotification(document);
        return;
      }
      openDetails(document);
    },
    { immediate: true }
  );

  return {
    activeProjectId,
    filters,
    showEditor,
    showDetail,
    showNotify,
    editingId,
    detailDocument,
    notifyDocument,
    deepLinkWarning,
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
  };
}
