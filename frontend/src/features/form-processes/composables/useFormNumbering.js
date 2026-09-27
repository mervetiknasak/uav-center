import { computed, ref } from "vue";

import { errorMessage } from "../../../composables/errorMessage";
import { buildFormProcessPayload } from "../model/form";

const base = "/api/form-processes/numbering/";
export function useFormNumbering({ apiFetch, editor, userId, storage = window.sessionStorage }) {
  const mappings = ref([]);
  const selected = ref(null);
  const manual = ref({});
  const busy = ref(false);
  const error = ref("");
  const pending = ref(null);
  const storageKey = () =>
    `form-numbering:${userId}:${editor.record.value?.id || editor.recordId || "new"}`;
  let activeStorageKey = storageKey();
  const available = computed(() =>
    mappings.value.filter(
      (item) => item.enabled && item.template_code === editor.form.template_code
    )
  );
  const contextRows = computed(() =>
    (selected.value?.format_snapshot?.required_context || []).map((item) => {
      const source = selected.value.context_sources[item.key];
      let value = source.value ?? "";
      if (source.source === "field")
        value = source.field.startsWith("data.")
          ? editor.form.data[source.field.slice(5)]
          : editor.form[source.field];
      if (source.source === "default") value = item.default;
      return { ...item, source: source.source, value };
    })
  );

  function storePending(value) {
    if (value) {
      if (!pending.value) activeStorageKey = storageKey();
      storage.setItem(activeStorageKey, JSON.stringify(value));
    } else storage.removeItem(activeStorageKey);
    pending.value = value;
  }

  async function accept(result) {
    if (result.status !== "completed") return;
    if (result.record) await editor.applyNumberedRecord(result.record);
    storePending(null);
    selected.value = null;
    error.value = result.record ? "" : "Numara işlemi tamamlanmış ancak form kaydı silinmiş.";
  }

  async function load() {
    try {
      activeStorageKey = storageKey();
      const raw = storage.getItem(activeStorageKey);
      if (raw) {
        pending.value = JSON.parse(raw);
        if (pending.value.payload?.form) {
          Object.assign(editor.form, pending.value.payload.form);
          if (editor.currentStep) editor.currentStep.value = 2;
        }
      }
      mappings.value = await apiFetch(`${base}mappings/`);
      if (pending.value) {
        const result = await apiFetch(`${base}allocations/${pending.value.id}/`);
        await accept(result);
      }
    } catch (err) {
      error.value = errorMessage(err, "Numaratör ayarları veya bekleyen işlem yüklenemedi.");
    }
  }

  function open(mapping) {
    if (busy.value || pending.value) return;
    selected.value = mapping;
    manual.value = {};
    error.value = "";
  }

  async function generate() {
    if (busy.value || editor.saving.value || !selected.value || pending.value) return;
    for (const row of contextRows.value) {
      if (
        row.source === "manual" &&
        (!manual.value[row.key]?.trim() || manual.value[row.key].length > row.max_length)
      ) {
        error.value = `${row.key}: 1–${row.max_length} karakter girin.`;
        return;
      }
    }
    const form = buildFormProcessPayload(editor.form);
    delete form.status;
    if (editor.removeAttachment.value) form.remove_attachment = true;
    const payload = {
      mapping_id: selected.value.id,
      record_id: editor.record.value?.id || null,
      expected_updated_at: editor.record.value?.updated_at || null,
      form,
      manual_context: { ...manual.value }
    };
    const key = crypto.randomUUID();
    const file = editor.fileList.value[0]?.file;
    try {
      // Persist the identity before sending, so a lost HTTP response is recoverable.
      storePending({ id: key, key, payload, hasAttachment: Boolean(file) });
    } catch {
      error.value =
        "Güvenli tekrar deneme için tarayıcı oturum depolaması kullanılabilir olmalıdır.";
      return;
    }
    await submit(file);
  }

  async function submit(file = null, retry = false) {
    if (busy.value || editor.saving.value || !pending.value) return;
    busy.value = true;
    editor.saving.value = true;
    error.value = "";
    try {
      let body = JSON.stringify(pending.value.payload);
      if (file) {
        body = new FormData();
        body.append("payload", JSON.stringify(pending.value.payload));
        body.append("attachment", file);
      }
      const result = await apiFetch(
        retry ? `${base}allocations/${pending.value.id}/retry/` : `${base}allocations/`,
        {
          method: "POST",
          headers: { "Idempotency-Key": pending.value.key },
          body: retry ? undefined : body
        }
      );
      await accept(result);
    } catch (err) {
      if (err?.data?.allocation_id) storePending({ ...pending.value, id: err.data.allocation_id });
      // Validation before allocation has no side effect. An ambiguous failure keeps its identity.
      if ([400, 403, 404, 409, 422].includes(err?.status) && !err?.data?.allocation_id)
        storePending(null);
      error.value = errorMessage(
        err,
        "Numara işlemi tamamlanamadı. Aynı işlemi güvenle tekrar deneyebilirsiniz."
      );
    } finally {
      busy.value = false;
      editor.saving.value = false;
    }
  }

  async function retry() {
    if (!pending.value || busy.value) return;
    try {
      const result = await apiFetch(`${base}allocations/${pending.value.id}/`);
      if (result.status === "completed") return accept(result);
      await submit(null, true);
    } catch (err) {
      if (err?.status === 404) {
        const file = editor.fileList.value[0]?.file;
        if (pending.value.hasAttachment && !file) {
          error.value = "İlk istekteki dosya ekini yeniden seçip tekrar deneyin.";
          return;
        }
        await submit(file);
      } else error.value = errorMessage(err, "İşlem durumu alınamadı.");
    }
  }

  return {
    mappings,
    available,
    selected,
    manual,
    busy,
    error,
    pending,
    contextRows,
    load,
    open,
    generate,
    retry
  };
}
