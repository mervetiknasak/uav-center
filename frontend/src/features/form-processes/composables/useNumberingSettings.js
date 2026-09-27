import { computed, reactive, ref } from "vue";
import { errorMessage } from "../../../composables/errorMessage";
import { flattenFormTemplates } from "../model/form";

const base = "/api/form-processes/numbering/";
const empty = () => ({
  id: null,
  template_code: null,
  target_field: null,
  format_code: null,
  enabled: true,
  context_sources: {}
});
export function useNumberingSettings({ apiFetch }) {
  const templates = ref([]);
  const formats = ref([]);
  const mappings = ref([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref("");
  const notice = ref("");
  const form = reactive(empty());
  const template = computed(() => templates.value.find((item) => item.code === form.template_code));
  const format = computed(() => formats.value.find((item) => item.code === form.format_code));
  const templateOptions = computed(() =>
    templates.value.map((item) => ({
      label: `${item.form_number} — ${item.title}`,
      value: item.code
    }))
  );
  const formatOptions = computed(() =>
    formats.value.map((item) => ({ label: `${item.name} (${item.code})`, value: item.code }))
  );
  const sourceOptions = computed(() => [
    { label: "Kayıt numarası", value: "record_number" },
    { label: "Kayıt başlığı", value: "title" },
    ...(template.value?.fields || [])
      .filter((field) => !["table", "multi_select"].includes(field.type))
      .map((field) => ({ label: field.label, value: `data.${field.key}` }))
  ]);
  const targetOptions = computed(() => [
    { label: "Kayıt numarası", value: "record_number" },
    ...(template.value?.fields || [])
      .filter((field) => ["text", "textarea"].includes(field.type))
      .map((field) => ({ label: field.label, value: `data.${field.key}` }))
  ]);

  function setFormat(code) {
    form.format_code = code;
    form.context_sources = Object.fromEntries(
      (format.value?.required_context || []).map((item) => [
        item.key,
        { source: item.required ? "manual" : "default" }
      ])
    );
  }
  function setTemplate(code) {
    form.template_code = code;
    form.target_field = null;
    setFormat(form.format_code);
  }
  function edit(mapping) {
    Object.assign(form, empty(), JSON.parse(JSON.stringify(mapping)));
    const contract =
      format.value?.required_context || mapping.format_snapshot?.required_context || [];
    form.context_sources = Object.fromEntries(
      contract.map((item) => [
        item.key,
        form.context_sources[item.key] || { source: item.required ? "manual" : "default" }
      ])
    );
    notice.value = "";
  }
  function reset() {
    Object.assign(form, empty());
  }

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      const [catalog, configured] = await Promise.all([
        apiFetch("/api/form-processes/templates/"),
        apiFetch(`${base}mappings/`)
      ]);
      templates.value = flattenFormTemplates(catalog);
      mappings.value = configured;
      const discovered = [];
      let page = 1;
      let total = 1;
      do {
        const result = await apiFetch(`${base}formats/?page=${page}`);
        discovered.push(...result.results);
        total = result.total_pages;
        page += 1;
      } while (page <= total);
      formats.value = discovered;
    } catch (err) {
      error.value = errorMessage(err, "Numaratör ayarları yüklenemedi.");
    } finally {
      loading.value = false;
    }
  }
  async function save() {
    if (saving.value) return;
    if (!form.template_code || !form.target_field || !form.format_code) {
      error.value = "Form, hedef alan ve format seçin.";
      return;
    }
    saving.value = true;
    error.value = "";
    notice.value = "";
    try {
      const { template_code, target_field, format_code, enabled, context_sources } = form;
      await apiFetch(`${base}mappings/${form.id ? `${form.id}/` : ""}`, {
        method: form.id ? "PATCH" : "POST",
        body: JSON.stringify({ template_code, target_field, format_code, enabled, context_sources })
      });
      mappings.value = await apiFetch(`${base}mappings/`);
      notice.value = "Eşleştirme kaydedildi. Mevcut numaralar ve alan kilitleri korunur.";
      reset();
    } catch (err) {
      error.value = errorMessage(err, "Eşleştirme kaydedilemedi.");
    } finally {
      saving.value = false;
    }
  }
  return {
    templates,
    formats,
    mappings,
    loading,
    saving,
    error,
    notice,
    form,
    template,
    format,
    templateOptions,
    formatOptions,
    sourceOptions,
    targetOptions,
    setFormat,
    setTemplate,
    edit,
    reset,
    load,
    save
  };
}
