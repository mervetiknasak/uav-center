export const FORM_PROCESS_STATUSES = [
  { label: "Taslak", value: "draft" },
  { label: "İncelemede", value: "in_review" },
  { label: "Onaylandı", value: "approved" },
  { label: "Arşivlendi", value: "archived" }
];

export const FORM_PROCESS_STATUS_TAGS = {
  draft: "default",
  in_review: "warning",
  approved: "success",
  archived: "info"
};
