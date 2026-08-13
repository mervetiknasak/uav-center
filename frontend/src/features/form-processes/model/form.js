export function flattenFormTemplates(processes = []) {
  return processes.flatMap((process) => process.templates || []);
}

export function createFormProcessForm(template = null) {
  return {
    process_code: template?.process_code || "",
    template_code: template?.code || "",
    record_number: "",
    title: template?.title || "",
    status: "draft",
    data: Object.fromEntries((template?.fields || []).map((field) => [field.key, ""])),
    notes: ""
  };
}

export function formProcessRecordToForm(record, templates = []) {
  const template = templates.find((item) => item.code === record?.template_code);
  if (!record) return createFormProcessForm(template || templates[0]);
  return {
    process_code: record.process_code,
    template_code: record.template_code,
    record_number: record.record_number,
    title: record.title,
    status: record.status,
    data: {
      ...Object.fromEntries((template?.fields || []).map((field) => [field.key, ""])),
      ...(record.data || {})
    },
    notes: record.notes || ""
  };
}

export function selectFormProcessTemplate(form, template) {
  Object.assign(form, createFormProcessForm(template));
}

export function buildFormProcessPayload(form) {
  return {
    template_code: form.template_code,
    record_number: String(form.record_number || "")
      .trim()
      .toUpperCase(),
    title: String(form.title || "").trim(),
    status: form.status,
    data: { ...(form.data || {}) },
    notes: String(form.notes || "").trim()
  };
}
