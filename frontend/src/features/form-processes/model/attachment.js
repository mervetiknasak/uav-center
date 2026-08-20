export const FORM_ATTACHMENT_ACCEPT = ".pdf,.docx,.xlsx,.jpg,.jpeg,.png";
export const FORM_ATTACHMENT_MAX_BYTES = 15 * 1024 * 1024;

const FORM_ATTACHMENT_EXTENSIONS = new Set(FORM_ATTACHMENT_ACCEPT.split(","));

export function validateFormAttachment(file) {
  if (!file) return "";
  const name = String(file.name || "").toLocaleLowerCase("tr-TR");
  const dotIndex = name.lastIndexOf(".");
  const extension = dotIndex >= 0 ? name.slice(dotIndex) : "";
  if (!FORM_ATTACHMENT_EXTENSIONS.has(extension)) return "Desteklenmeyen doküman tipi.";
  if (file.size > FORM_ATTACHMENT_MAX_BYTES) {
    return "Doküman boyutu 15 MB'dan büyük olamaz.";
  }
  return "";
}

export function formatFormAttachmentSize(size) {
  if (!size) return "";
  if (size < 1024 * 1024) return `${Math.max(1, Math.round(size / 1024))} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function existingFormAttachment(record) {
  if (!record?.attachment_url) return null;
  return {
    name: record.attachment_name,
    url: record.attachment_url,
    size: record.attachment_size
  };
}
