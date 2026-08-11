export const FLIGHT_PERMIT_TYPES = Object.freeze([
  { label: "Yurt İçi", value: "domestic" },
  { label: "Uluslararası", value: "international" },
  { label: "Test Uçuşu", value: "test" },
  { label: "İntikal Uçuşu", value: "ferry" }
]);

export const FLIGHT_PERMIT_RECORD_STATUSES = Object.freeze([
  { label: "Taslak", value: "draft" },
  { label: "Onaylandı", value: "approved" },
  { label: "Askıya Alındı", value: "suspended" },
  { label: "İptal Edildi", value: "revoked" }
]);

export const FLIGHT_PERMIT_VALIDITY_STATUSES = Object.freeze([
  { label: "Geçerli", value: "active" },
  { label: "Süresi Yaklaşıyor", value: "expiring" },
  { label: "Yaklaşan", value: "upcoming" },
  { label: "Süresi Doldu", value: "expired" },
  { label: "Taslak", value: "draft" },
  { label: "Askıya Alındı", value: "suspended" },
  { label: "İptal Edildi", value: "revoked" }
]);

export const FLIGHT_PERMIT_VALIDITY_TAG_TYPES = Object.freeze({
  active: "success",
  expiring: "warning",
  upcoming: "info",
  expired: "error",
  draft: "default",
  suspended: "warning",
  revoked: "error"
});
