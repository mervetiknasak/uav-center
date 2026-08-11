export const TECHNICAL_DOCUMENT_STATUSES = Object.freeze([
  { label: "Taslak", value: "draft" },
  { label: "İncelemede", value: "in_review" },
  { label: "Revizyon Bekliyor", value: "changes_requested" },
  { label: "Onaylandı", value: "approved" },
  { label: "Yayınlandı", value: "published" },
  { label: "Yürürlükten Kalktı", value: "superseded" },
  { label: "Arşivlendi", value: "archived" }
]);

export const TECHNICAL_DOCUMENT_STATUS_TYPES = Object.freeze({
  draft: "default",
  in_review: "info",
  changes_requested: "warning",
  approved: "success",
  published: "success",
  superseded: "error",
  archived: "default"
});

export const TECHNICAL_DOCUMENT_PRIORITY_TYPES = Object.freeze({
  normal: "default",
  high: "warning",
  critical: "error"
});

export const TECHNICAL_DOCUMENT_PRIORITIES = Object.freeze([
  { label: "Normal", value: "normal" },
  { label: "Yüksek", value: "high" },
  { label: "Kritik", value: "critical" }
]);

export const TECHNICAL_DOCUMENT_CLASSIFICATIONS = Object.freeze([
  { label: "Kurum İçi", value: "internal" },
  { label: "Gizli", value: "confidential" },
  { label: "Kısıtlı", value: "restricted" },
  { label: "Herkese Açık", value: "public" }
]);
