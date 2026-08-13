export function validateFormProcessForm(form, templates = []) {
  if (!String(form.record_number || "").trim() || !String(form.title || "").trim()) {
    return "Kayıt numarası ve kayıt başlığı zorunludur.";
  }
  const template = templates.find((item) => item.code === form.template_code);
  if (!template) return "Geçerli bir süreç ve FM şablonu seçilmelidir.";
  const missing = template.fields.find(
    (field) => field.required && !String(form.data?.[field.key] || "").trim()
  );
  if (missing) return `${missing.label} zorunludur.`;
  const tooLong = template.fields.find(
    (field) => String(form.data?.[field.key] || "").length > field.max_length
  );
  if (tooLong) return `${tooLong.label} en fazla ${tooLong.max_length} karakter olabilir.`;
  return "";
}
