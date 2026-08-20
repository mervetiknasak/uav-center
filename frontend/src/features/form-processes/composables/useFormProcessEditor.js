import { computed, reactive, ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";
import {
  buildFormProcessPayload,
  buildFormProcessRequestBody,
  createFormProcessForm,
  flattenFormTemplates,
  formProcessRecordToForm,
  selectFormProcessTemplate
} from "../model/form";
import { apiFormProcessErrors, collectFormProcessErrors } from "../model/validation";
import { existingFormAttachment, validateFormAttachment } from "../model/attachment";

function formSnapshot(form) {
  return JSON.stringify({
    process_code: form.process_code,
    template_code: form.template_code,
    record_number: form.record_number,
    title: form.title,
    data: form.data,
    notes: form.notes
  });
}

export function useFormProcessEditor({ apiFetch, router, recordId = null }) {
  const processes = ref([]);
  const record = ref(null);
  const form = reactive(createFormProcessForm());
  const currentStep = ref(1);
  const loading = ref(false);
  const saving = ref(false);
  const ready = ref(false);
  const error = ref("");
  const notice = ref("");
  const validationErrors = ref({});
  const fileList = ref([]);
  const existingAttachment = ref(null);
  const attachmentWasPresent = ref(false);
  const removeAttachment = ref(false);
  const attachmentDirty = ref(false);
  const savedSnapshot = ref(formSnapshot(form));
  const templates = computed(() => flattenFormTemplates(processes.value));
  const selectedTemplate = computed(() =>
    templates.value.find((template) => template.code === form.template_code)
  );
  const templateLocked = computed(() => Boolean(record.value?.id));
  const archived = computed(() => record.value?.status === "archived");
  const dirty = computed(
    () => ready.value && (formSnapshot(form) !== savedSnapshot.value || attachmentDirty.value)
  );
  const reviewAttachment = computed(() => {
    const file = fileList.value[0]?.file;
    return file ? { name: file.name, size: file.size } : existingAttachment.value;
  });

  function syncSavedForm(saved) {
    record.value = saved;
    Object.assign(form, formProcessRecordToForm(saved, templates.value));
    fileList.value = [];
    existingAttachment.value = existingFormAttachment(saved);
    attachmentWasPresent.value = Boolean(existingAttachment.value);
    removeAttachment.value = false;
    attachmentDirty.value = false;
    savedSnapshot.value = formSnapshot(form);
  }

  async function load() {
    loading.value = true;
    ready.value = false;
    error.value = "";
    try {
      const [catalog, existing] = await Promise.all([
        apiFetch("/api/form-processes/templates/"),
        recordId ? apiFetch(`/api/form-processes/${recordId}/`) : Promise.resolve(null)
      ]);
      processes.value = Array.isArray(catalog) ? catalog : [];
      if (existing) {
        syncSavedForm(existing);
        currentStep.value = 2;
      } else {
        Object.assign(form, createFormProcessForm());
        fileList.value = [];
        existingAttachment.value = null;
        attachmentWasPresent.value = false;
        removeAttachment.value = false;
        attachmentDirty.value = false;
        savedSnapshot.value = formSnapshot(form);
        currentStep.value = 1;
      }
    } catch (err) {
      error.value = errorMessage(err, "Form kaydı yüklenemedi");
    } finally {
      ready.value = true;
      loading.value = false;
    }
  }

  function selectProcess(processCode) {
    if (templateLocked.value || form.process_code === processCode) return;
    Object.assign(form, createFormProcessForm());
    form.process_code = processCode;
    validationErrors.value = {};
  }

  function selectTemplate(templateCode) {
    if (templateLocked.value) return;
    const template = templates.value.find((item) => item.code === templateCode);
    if (template) selectFormProcessTemplate(form, template);
    validationErrors.value = {};
  }

  function goToFields() {
    if (!selectedTemplate.value) {
      validationErrors.value = {
        template_code: "Devam etmek için bir süreç ve FM şablonu seçin."
      };
      return;
    }
    validationErrors.value = {};
    currentStep.value = 2;
  }

  function updateIdentity(field, value) {
    form[field] = value;
    const next = { ...validationErrors.value };
    delete next[field];
    validationErrors.value = next;
  }

  function updateField(key, value) {
    form.data[key] = value;
    const next = { ...validationErrors.value };
    delete next[key];
    validationErrors.value = next;
  }

  function updateNotes(value) {
    form.notes = value;
  }

  function updateFileList(files) {
    fileList.value = files.slice(-1);
    removeAttachment.value = fileList.value.length
      ? false
      : attachmentWasPresent.value && !existingAttachment.value;
    attachmentDirty.value = Boolean(fileList.value.length || removeAttachment.value);
    const next = { ...validationErrors.value };
    delete next.attachment;
    validationErrors.value = next;
  }

  function markAttachmentForRemoval() {
    existingAttachment.value = null;
    fileList.value = [];
    removeAttachment.value = true;
    attachmentDirty.value = true;
  }

  function openAttachment() {
    if (!existingAttachment.value?.url) return;
    window.open(existingAttachment.value.url, "_blank", "noopener,noreferrer");
  }

  function validate(requireRequired) {
    validationErrors.value = collectFormProcessErrors(form, templates.value, {
      requireRequired
    });
    const attachmentError = validateFormAttachment(fileList.value[0]?.file);
    if (attachmentError) validationErrors.value.attachment = attachmentError;
    if (Object.keys(validationErrors.value).length) {
      error.value = "Formdaki hataları düzelttikten sonra yeniden deneyin.";
      if (validationErrors.value.template_code) currentStep.value = 1;
      else currentStep.value = 2;
      return false;
    }
    error.value = "";
    return true;
  }

  function review() {
    if (!validate(true)) return;
    currentStep.value = 3;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function save(status) {
    if (saving.value || archived.value) return null;
    const requireRequired = status !== "draft";
    if (!validate(requireRequired)) return null;
    saving.value = true;
    notice.value = "";
    try {
      const isNew = !record.value?.id;
      const payload = buildFormProcessPayload(form, status);
      const saved = await apiFetch(
        isNew ? "/api/form-processes/" : `/api/form-processes/${record.value.id}/`,
        {
          method: isNew ? "POST" : "PATCH",
          body: buildFormProcessRequestBody(payload, {
            file: fileList.value[0]?.file || null,
            removeAttachment: removeAttachment.value
          })
        }
      );
      syncSavedForm(saved);
      validationErrors.value = {};
      error.value = "";
      notice.value =
        status === "approved" ? "Form kaydı tamamlandı ve onaylandı." : "Taslak kaydedildi.";
      if (isNew) {
        await router.replace({ name: "form-process-edit", params: { recordId: saved.id } });
      }
      return saved;
    } catch (err) {
      validationErrors.value = apiFormProcessErrors(err?.data, selectedTemplate.value);
      error.value = errorMessage(err, "Form kaydı kaydedilemedi");
      if (Object.keys(validationErrors.value).length) currentStep.value = 2;
      return null;
    } finally {
      saving.value = false;
    }
  }

  async function saveDraft() {
    return save("draft");
  }

  async function complete() {
    const saved = await save("approved");
    if (saved) currentStep.value = 3;
  }

  function download() {
    if (!record.value?.generated_document_url) return;
    const link = document.createElement("a");
    link.href = record.value.generated_document_url;
    link.download = `${record.value.template_code}_${record.value.record_number}.docx`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  return {
    processes,
    templates,
    record,
    form,
    selectedTemplate,
    templateLocked,
    archived,
    currentStep,
    loading,
    saving,
    ready,
    error,
    notice,
    validationErrors,
    fileList,
    existingAttachment,
    reviewAttachment,
    dirty,
    load,
    selectProcess,
    selectTemplate,
    goToFields,
    updateIdentity,
    updateField,
    updateNotes,
    updateFileList,
    markAttachmentForRemoval,
    openAttachment,
    review,
    saveDraft,
    complete,
    download
  };
}
