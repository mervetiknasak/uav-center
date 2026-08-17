function nonEmptyTableRows(value) {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (row) =>
      row && typeof row === "object" && Object.values(row).some((cell) => String(cell || "").trim())
  );
}

function validIsoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function collectFormProcessErrors(form, templates = [], { requireRequired = true } = {}) {
  const errors = {};
  const template = templates.find((item) => item.code === form.template_code);
  if (!template) errors.template_code = "Geçerli bir süreç ve FM şablonu seçilmelidir.";
  if (!String(form.record_number || "").trim()) {
    errors.record_number = "Kayıt numarası zorunludur.";
  }
  if (!String(form.title || "").trim()) errors.title = "Kayıt başlığı zorunludur.";
  for (const field of template?.fields || []) {
    if (field.type === "table") {
      if (!Array.isArray(form.data?.[field.key])) {
        errors[field.key] = `${field.label} satırları geçersiz.`;
        continue;
      }
      const rows = nonEmptyTableRows(form.data[field.key]);
      if (requireRequired && field.required && !rows.length) {
        errors[field.key] = `${field.label} için en az bir satır zorunludur.`;
        continue;
      }
      if (field.max_items && rows.length > field.max_items) {
        errors[field.key] = `${field.label} en fazla ${field.max_items} satır içerebilir.`;
        continue;
      }
      for (const [rowIndex, row] of rows.entries()) {
        for (const column of field.columns || []) {
          const cellValue = String(row[column.key] || "").trim();
          if (requireRequired && column.required && !cellValue) {
            errors[field.key] = `${rowIndex + 1}. satırda ${column.label} zorunludur.`;
            break;
          }
          if (cellValue.length > column.max_length) {
            errors[field.key] =
              `${rowIndex + 1}. satırda ${column.label} en fazla ${column.max_length} karakter olabilir.`;
            break;
          }
          if (column.type === "date" && cellValue && !validIsoDate(cellValue)) {
            errors[field.key] =
              `${rowIndex + 1}. satırda geçerli bir ${column.label.toLocaleLowerCase("tr-TR")} seçilmelidir.`;
            break;
          }
        }
        if (errors[field.key]) break;
      }
      continue;
    }
    const value = String(form.data?.[field.key] || "");
    if (requireRequired && field.required && !value.trim()) {
      errors[field.key] = `${field.label} zorunludur.`;
    } else if (value.length > field.max_length) {
      errors[field.key] = `${field.label} en fazla ${field.max_length} karakter olabilir.`;
    }
  }
  if (
    template?.code === "fm_dsg_0327" &&
    form.data?.valid_from &&
    form.data?.valid_until &&
    form.data.valid_from > form.data.valid_until
  ) {
    errors.valid_until = "Geçerlilik bitişi, başlangıç tarihinden önce olamaz.";
  }
  return errors;
}

export function validateFormProcessForm(form, templates = [], options) {
  return Object.values(collectFormProcessErrors(form, templates, options))[0] || "";
}

export function apiFormProcessErrors(data, template = null) {
  if (!data || typeof data !== "object") return {};
  const fieldKeys = new Set([
    "template_code",
    "record_number",
    "title",
    ...(template?.fields || []).map((field) => field.key)
  ]);
  const errors = {};
  for (const [key, value] of Object.entries(data)) {
    const message = Array.isArray(value) ? value.join(" ") : String(value || "");
    if (fieldKeys.has(key)) errors[key] = message;
    else errors.form = message;
  }
  return errors;
}
