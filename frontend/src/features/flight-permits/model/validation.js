export const FLIGHT_PERMIT_FILE_ACCEPT = ".pdf,.docx,.xlsx,.jpg,.jpeg,.png";
export const FLIGHT_PERMIT_FILE_MAX_BYTES = 15 * 1024 * 1024;

const FLIGHT_PERMIT_FILE_EXTENSIONS = new Set(FLIGHT_PERMIT_FILE_ACCEPT.split(","));

export function validateFlightPermitForm(form) {
  if (
    !String(form.aircraft_number || "").trim() ||
    !String(form.permit_number || "").trim() ||
    !String(form.issuing_authority || "").trim() ||
    !form.valid_from ||
    !form.valid_until
  ) {
    return "Uçak numarası, izin numarası, yetkili kurum ve geçerlilik tarihleri zorunludur.";
  }
  if (form.valid_until < form.valid_from) {
    return "Geçerlilik bitiş tarihi başlangıç tarihinden önce olamaz.";
  }
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
