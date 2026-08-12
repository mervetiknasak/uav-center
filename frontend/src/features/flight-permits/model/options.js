export const FLIGHT_PERMIT_KINDS = Object.freeze([
  { label: "Uçuş izni", value: false },
  { label: "Uçuş izni tavsiyesi", value: true }
]);

export const FLIGHT_PURPOSE_OPTIONS = Object.freeze([
  { label: "Geliştirme", value: "research_development" },
  {
    label: "Tasarım ya da üretim kuruluşlarının personel eğitimi",
    value: "certification_compliance"
  },
  { label: "Üretim tesisleri arasında hava aracının uçurulması", value: "production_flight_test" },
  { label: "Müşteri kabulü için uçurulması", value: "customer_acceptance" },
  { label: "Uçak teslimatı ve ihracı", value: "maintenance_check" },
  {
    label: "Bakım veya uçuşa elverişlilik incelenmesi için ya da depolama yerine uçurulması",
    value: "demonstration"
  }
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
