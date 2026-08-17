import { beforeEach, describe, expect, it, vi } from "vitest";

import { useFormProcessEditor } from "./useFormProcessEditor";

const template = {
  code: "fm_test",
  process_code: "test-process",
  process_name: "Test Süreci",
  form_number: "FM.TEST.1",
  title: "Test Formu",
  description: "Test açıklaması",
  fields: [
    {
      key: "required_field",
      label: "Zorunlu alan",
      type: "text",
      group: "Genel",
      required: true,
      max_length: 50
    },
    {
      key: "event_date",
      label: "Tarih",
      type: "date",
      group: "Genel",
      required: false,
      max_length: 10
    }
  ]
};

const catalog = [{ code: "test-process", name: "Test Süreci", templates: [template] }];

function savedRecord(status, data = {}) {
  return {
    id: 7,
    process_code: template.process_code,
    process_name: template.process_name,
    template_code: template.code,
    template_title: template.title,
    form_number: template.form_number,
    record_number: "TEST-1",
    title: "Test kaydı",
    status,
    status_display: status === "approved" ? "Onaylandı" : "Taslak",
    data: { required_field: "", event_date: "", ...data },
    notes: "",
    generated_document_url: "/api/form-processes/7/generated-document/"
  };
}

describe("form process editor controller", () => {
  beforeEach(() => {
    vi.stubGlobal("window", { scrollTo: vi.fn() });
  });

  it("saves an incomplete draft, locks its template and switches to PATCH", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce(catalog)
      .mockResolvedValueOnce(savedRecord("draft"))
      .mockResolvedValueOnce(savedRecord("approved", { required_field: "Tamam" }));
    const router = { replace: vi.fn().mockResolvedValue() };
    const editor = useFormProcessEditor({ apiFetch, router });

    await editor.load();
    editor.selectProcess(template.process_code);
    editor.selectTemplate(template.code);
    editor.goToFields();
    editor.updateIdentity("record_number", "TEST-1");
    editor.updateIdentity("title", "Test kaydı");

    await editor.saveDraft();

    expect(JSON.parse(apiFetch.mock.calls[1][1].body)).toMatchObject({
      status: "draft",
      data: { required_field: "", event_date: "" }
    });
    expect(router.replace).toHaveBeenCalledWith({
      name: "form-process-edit",
      params: { recordId: 7 }
    });
    expect(editor.templateLocked.value).toBe(true);
    expect(editor.dirty.value).toBe(false);

    editor.updateField("required_field", "Tamam");
    editor.review();
    expect(editor.currentStep.value).toBe(3);
    expect(apiFetch).toHaveBeenCalledTimes(2);

    await editor.complete();
    expect(apiFetch.mock.calls[2][0]).toBe("/api/form-processes/7/");
    expect(JSON.parse(apiFetch.mock.calls[2][1].body).status).toBe("approved");
    expect(editor.record.value.status).toBe("approved");
  });

  it("keeps review local and returns required field errors to the form step", async () => {
    const apiFetch = vi.fn().mockResolvedValueOnce(catalog);
    const editor = useFormProcessEditor({ apiFetch, router: { replace: vi.fn() } });

    await editor.load();
    editor.selectProcess(template.process_code);
    editor.selectTemplate(template.code);
    editor.goToFields();
    editor.updateIdentity("record_number", "TEST-1");
    editor.updateIdentity("title", "Test kaydı");
    editor.review();

    expect(editor.currentStep.value).toBe(2);
    expect(editor.validationErrors.value.required_field).toContain("zorunludur");
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });

  it("prevents saving an archived record", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce(catalog)
      .mockResolvedValueOnce({ ...savedRecord("approved"), status: "archived" });
    const editor = useFormProcessEditor({
      apiFetch,
      router: { replace: vi.fn() },
      recordId: 7
    });

    await editor.load();
    expect(editor.archived.value).toBe(true);
    await editor.saveDraft();
    expect(apiFetch).toHaveBeenCalledTimes(2);
  });
});
