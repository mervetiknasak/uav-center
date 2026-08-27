const EDITOR_LABELS = Object.freeze({
  project: "Proje",
  panel: "Alt Panel",
  responsible: "Sorumlu",
  group: "Kişi Grubu",
  person: "Kişi"
});

export const ORGANIZATION_TITLE_OPTIONS = Object.freeze(
  ["CVE", "AS", "PSK", "Şef", "IPT"].map((title) => ({ label: title, value: title }))
);

export function createOrganizationEditorForm(type, item = null) {
  if (type === "project") {
    return {
      name: item?.name ?? "",
      code: item?.code ?? "",
      description: item?.description ?? "",
      is_active: item?.is_active ?? true,
      order: item?.order ?? 0
    };
  }
  if (type === "responsible" || type === "person") {
    return {
      name: item?.name ?? "",
      titles: Array.isArray(item?.titles) ? [...item.titles] : [],
      email: item?.email ?? "",
      username: item?.username ?? ""
    };
  }
  return {
    name: item?.name ?? "",
    description: item?.description ?? "",
    order: item?.order ?? 0
  };
}

export function organizationEditorTitle(type, id = null) {
  return `${id ? "Düzenle" : "Yeni"} ${EDITOR_LABELS[type]}`;
}

export function canSubmitOrganizationEditor(type, form) {
  return Boolean(
    String(form.name || "").trim() && (type !== "project" || String(form.code || "").trim())
  );
}

export function createOrganizationSaveCommand({ type, id, parentId, form }) {
  return { type, id, parentId, payload: { ...form } };
}

export function organizationDeletePrompt(item) {
  return `“${item.name}” kaydı silinsin mi? Alt kayıtlar da silinebilir.`;
}

export function createResponsibleReorder(panel, reorderedItems) {
  if (reorderedItems.length !== panel.responsibles.length) return null;
  return {
    panelId: panel.id,
    items: reorderedItems.map((item, index) => ({ ...item, order: index }))
  };
}

export function selectResponsibleForRemoval(panel, index) {
  return panel.responsibles[index] || null;
}
