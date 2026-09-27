import { computed, ref } from "vue";
import { describe, expect, it, vi } from "vitest";
import { useFormNumbering } from "./useFormNumbering";

function setup(apiFetch) {
  const editor = {
    form: {
      template_code: "fm_test",
      record_number: "",
      title: "Form",
      data: { program: "UAV" },
      notes: ""
    },
    record: ref(null),
    saving: ref(false),
    fileList: ref([]),
    removeAttachment: ref(false),
    applyNumberedRecord: vi.fn(),
    selectedTemplate: computed(() => ({ fields: [{ key: "program", label: "Proje" }] }))
  };
  const storage = { getItem: vi.fn(), setItem: vi.fn(), removeItem: vi.fn() };
  return { editor, storage, numbering: useFormNumbering({ apiFetch, editor, storage, userId: 1 }) };
}

describe("form numbering", () => {
  it("saves generated record and prevents duplicate clicks", async () => {
    let resolve;
    const apiFetch = vi.fn(
      () =>
        new Promise((done) => {
          resolve = done;
        })
    );
    const { numbering, editor } = setup(apiFetch);
    numbering.open({
      id: 1,
      target_field: "record_number",
      context_sources: { project: { source: "field", field: "data.program" } },
      format_snapshot: { required_context: [{ key: "project", required: true, max_length: 10 }] }
    });
    const pending = numbering.generate();
    await numbering.generate();
    expect(apiFetch).toHaveBeenCalledTimes(1);
    resolve({ id: "op", status: "completed", record: { id: 7, record_number: "Test-001" } });
    await pending;
    expect(editor.applyNumberedRecord).toHaveBeenCalledWith({ id: 7, record_number: "Test-001" });
    expect(editor.saving.value).toBe(false);
  });

  it("retains operation identity after a timeout", async () => {
    const apiFetch = vi.fn().mockRejectedValue(new Error("timeout"));
    const { numbering, storage } = setup(apiFetch);
    numbering.open({
      id: 1,
      target_field: "record_number",
      context_sources: {},
      format_snapshot: { required_context: [] }
    });
    await numbering.generate();
    expect(numbering.pending.value.id).toBeTruthy();
    expect(storage.removeItem).not.toHaveBeenCalled();
    expect(numbering.error.value).toBeTruthy();
  });
});

describe("number allocation recovery", () => {
  const mapping = {
    id: 1,
    target_field: "record_number",
    context_sources: {},
    format_snapshot: { required_context: [] }
  };
  it("clears a definitive pre-allocation conflict so the user can correct the form", async () => {
    const apiFetch = vi
      .fn()
      .mockRejectedValue(
        Object.assign(new Error("stale form"), { status: 409, data: { detail: "stale form" } })
      );
    const { numbering } = setup(apiFetch);
    numbering.open(mapping);
    await numbering.generate();
    expect(numbering.pending.value).toBe(null);
    expect(numbering.error.value).toBe("stale form");
  });
  it("retains an issued allocation on conflict", async () => {
    const apiFetch = vi.fn().mockRejectedValue(
      Object.assign(new Error("record changed"), {
        status: 409,
        data: { allocation_id: "retained-operation" }
      })
    );
    const { numbering } = setup(apiFetch);
    numbering.open(mapping);
    await numbering.generate();
    expect(numbering.pending.value.id).toBe("retained-operation");
  });
  it("uses a record-specific storage slot after a new form becomes saved", async () => {
    const apiFetch = vi.fn().mockResolvedValue({ status: "completed", record: { id: 7 } });
    const { numbering, editor, storage } = setup(apiFetch);
    editor.applyNumberedRecord.mockImplementation((record) => {
      editor.record.value = record;
    });
    numbering.open(mapping);
    await numbering.generate();
    expect(storage.removeItem).toHaveBeenCalledWith("form-numbering:1:new");
    numbering.open(mapping);
    apiFetch.mockRejectedValueOnce(new Error("timeout"));
    await numbering.generate();
    expect(storage.setItem.mock.calls.at(-1)[0]).toBe("form-numbering:1:7");
  });
  it("recovers a completed operation on reload without generating again", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ status: "completed", record: { id: 7 } });
    const { numbering, editor, storage } = setup(apiFetch);
    storage.getItem.mockReturnValue(JSON.stringify({ id: "pending-id", key: "pending-id" }));
    await numbering.load();
    expect(editor.applyNumberedRecord).toHaveBeenCalledWith({ id: 7 });
    expect(apiFetch.mock.calls.every(([, options]) => !options?.method)).toBe(true);
  });
});
