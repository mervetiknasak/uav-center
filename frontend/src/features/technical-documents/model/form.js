import { formatTechnicalDocumentDate } from "./formatters";

export function createTechnicalDocumentForm(project = null) {
  return {
    project,
    panels: [],
    code: "",
    title: "",
    description: "",
    category: "",
    document_type: "",
    cover_page_number: "",
    cover_page_issue: "",
    revision: "A",
    status: "draft",
    priority: "normal",
    classification: "internal",
    owner_name: "",
    publication_date: null,
    due_date: null,
    review_date: null,
    source_url: "",
    notes: ""
  };
}

export function technicalDocumentToForm(document, fallbackProject = null) {
  if (!document) return createTechnicalDocumentForm(fallbackProject);
  return {
    project: document.project,
    panels: (document.panel_details || []).map((panel) => panel.id),
    code: document.code,
    title: document.title,
    description: document.description,
    category: document.category,
    document_type: document.document_type,
    cover_page_number: document.cover_page?.number || "",
    cover_page_issue: document.cover_page?.issue || "",
    revision: document.revision,
    status: document.status,
    priority: document.priority,
    classification: document.classification,
    owner_name: document.owner_name,
    publication_date: document.publication_date,
    due_date: document.due_date,
    review_date: document.review_date,
    source_url: document.source_url,
    notes: document.notes
  };
}

export function validateTechnicalDocumentForm(form) {
  if (!form.project || !String(form.code || "").trim() || !String(form.title || "").trim()) {
    return "Proje, doküman kodu ve başlık zorunludur.";
  }
  if (form.status === "published" && !form.publication_date) {
    return "Yayınlanan doküman için yayın tarihi zorunludur.";
  }
  const hasCoverPageNumber = Boolean(String(form.cover_page_number || "").trim());
  const hasCoverPageIssue = Boolean(String(form.cover_page_issue || "").trim());
  if (hasCoverPageNumber !== hasCoverPageIssue) {
    return "Kapak sayfası numarası ve issue birlikte girilmelidir.";
  }
  return "";
}

export function buildTechnicalDocumentPayload(form) {
  const { cover_page_number, cover_page_issue, ...documentFields } = form;
  const coverPageNumber = String(cover_page_number || "").trim();
  const coverPageIssue = String(cover_page_issue || "").trim();
  return {
    ...documentFields,
    panels: [...(form.panels || [])],
    cover_page: coverPageNumber ? { number: coverPageNumber, issue: coverPageIssue } : null,
    code: String(form.code || "").trim(),
    title: String(form.title || "").trim(),
    publication_date: form.publication_date || null,
    due_date: form.due_date || null,
    review_date: form.review_date || null
  };
}

export function createTechnicalDocumentNotification(document) {
  return {
    subject: `[${document.project_code}] ${document.code} — ${document.title}`,
    message:
      `${document.code} kodlu “${document.title}” dokümanı için bilgilendirme.\n\n` +
      `Durum: ${document.status_display}\nRevizyon: ${document.revision}\n` +
      `Yayın tarihi: ${formatTechnicalDocumentDate(document.publication_date)}\n` +
      `Termin: ${formatTechnicalDocumentDate(document.due_date)}`
  };
}
