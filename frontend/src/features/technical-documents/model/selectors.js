const ACTIVE_WORKFLOW_STATUSES = new Set(["in_review", "changes_requested", "approved"]);
const NON_OVERDUE_STATUSES = new Set(["published", "superseded", "archived"]);

export function normalizeTechnicalDocumentSearch(value) {
  return String(value || "")
    .toLocaleLowerCase("tr-TR")
    .trim();
}

export function selectProjectDocuments(documents, projectId) {
  return (documents || []).filter((document) => document.project === projectId);
}

export function selectTechnicalDocumentCategories(documents) {
  return [...new Set((documents || []).map((document) => document.category).filter(Boolean))]
    .sort()
    .map((category) => ({ label: category, value: category }));
}

export function filterTechnicalDocuments(
  documents,
  { search = "", status = null, panelId = null, category = null } = {}
) {
  const query = normalizeTechnicalDocumentSearch(search);
  return (documents || []).filter((document) => {
    const matchesSearch =
      !query ||
      [
        document.code,
        document.title,
        document.owner_name,
        document.category,
        document.cover_page?.number,
        document.cover_page?.issue
      ].some((value) => normalizeTechnicalDocumentSearch(value).includes(query));
    const matchesStatus = !status || document.status === status;
    const matchesPanel =
      !panelId || (document.panel_details || []).some((panel) => panel.id === panelId);
    const matchesCategory = !category || document.category === category;
    return matchesSearch && matchesStatus && matchesPanel && matchesCategory;
  });
}

export function isTechnicalDocumentOverdue(document, today) {
  return Boolean(
    document?.due_date && document.due_date < today && !NON_OVERDUE_STATUSES.has(document.status)
  );
}

export function calculateTechnicalDocumentMetrics(documents, today) {
  const items = documents || [];
  const published = items.filter((document) => document.status === "published").length;
  return {
    total: items.length,
    published,
    active: items.filter((document) => ACTIVE_WORKFLOW_STATUSES.has(document.status)).length,
    overdue: items.filter((document) => isTechnicalDocumentOverdue(document, today)).length,
    notified: items.filter((document) => document.last_notification_at).length,
    publicationRate: items.length ? Math.round((published / items.length) * 100) : 0
  };
}

export function countTechnicalDocumentsForProject(documents, projectId) {
  return selectProjectDocuments(documents, projectId).length;
}
