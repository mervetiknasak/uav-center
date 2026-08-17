export function flattenFormTemplates(processes = []) {
  return processes.flatMap((process) => process.templates || []);
}

function emptyFieldValue(field) {
  if (field.type === "table") return [];
  return field.type === "date" ? null : "";
}

function normalizePayloadValue(value) {
  if (Array.isArray(value)) {
    return value.filter(
      (row) =>
        row &&
        typeof row === "object" &&
        Object.values(row).some((cell) => String(cell || "").trim())
    );
  }
  return value ?? "";
}

function templateData(template, data = {}) {
  return Object.fromEntries(
    (template?.fields || []).map((field) => {
      const value = data[field.key];
      return [field.key, value === undefined || value === "" ? emptyFieldValue(field) : value];
    })
  );
}

export function createFormProcessForm(template = null) {
  return {
    process_code: template?.process_code || "",
    template_code: template?.code || "",
    record_number: "",
    title: template?.title || "",
    status: "draft",
    data: templateData(template),
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
    data: templateData(template, record.data),
    notes: record.notes || ""
  };
}

export function selectFormProcessTemplate(form, template) {
  Object.assign(form, createFormProcessForm(template));
}

export function buildFormProcessPayload(form, status = form.status) {
  return {
    template_code: form.template_code,
    record_number: String(form.record_number || "")
      .trim()
      .toUpperCase(),
    title: String(form.title || "").trim(),
    status,
    data: Object.fromEntries(
      Object.entries(form.data || {}).map(([key, value]) => [key, normalizePayloadValue(value)])
    ),
    notes: String(form.notes || "").trim()
  };
}
