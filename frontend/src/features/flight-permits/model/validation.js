export const FLIGHT_PERMIT_FILE_ACCEPT = ".pdf,.docx,.xlsx,.jpg,.jpeg,.png";
export const FLIGHT_PERMIT_FILE_MAX_BYTES = 15 * 1024 * 1024;

const FLIGHT_PERMIT_FILE_EXTENSIONS = new Set(FLIGHT_PERMIT_FILE_ACCEPT.split(","));

export function validateFlightPermitForm(form, templates = []) {
  if (
    !String(form.permit_applicant || "").trim() ||
    !String(form.permit_number || "").trim() ||
    !form.valid_from ||
    !form.valid_until
  ) {
    return "Başvuru sahibi, izin numarası ve geçerlilik tarihleri zorunludur.";
  }
  if (form.valid_until < form.valid_from) {
    return "Geçerlilik bitiş tarihi başlangıç tarihinden önce olamaz.";
  }
  if (form.flight_duration !== null && form.flight_duration < 1) {
    return "Uçuş süresi en az 1 saat olmalıdır.";
  }
  const template = templates.find((item) => item.code === form.template_code);
  if (!template) return "Geçerli bir alıcı kurum ve şablon seçilmelidir.";
  const missingField = template.fields.find(
    (field) => field.required && !String(form.template_data?.[field.key] || "").trim()
  );
  if (missingField) return `${missingField.label} zorunludur.`;
  return "";
}

export function validateFlightPermitFile(file) {
  if (!file) return "";
  const name = String(file.name || "").toLocaleLowerCase("tr-TR");
  const dotIndex = name.lastIndexOf(".");
  const extension = dotIndex >= 0 ? name.slice(dotIndex) : "";
  if (!FLIGHT_PERMIT_FILE_EXTENSIONS.has(extension)) {
    return "Desteklenmeyen doküman tipi.";
  }
  if (file.size > FLIGHT_PERMIT_FILE_MAX_BYTES) {
    return "Doküman boyutu 15 MB'dan büyük olamaz.";
  }
  return "";
}
