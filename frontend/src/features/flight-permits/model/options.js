export const FLIGHT_PERMIT_KINDS = Object.freeze([
  { label: "Uçuş izni", value: false },
  { label: "Uçuş izni tavsiyesi", value: true }
]);

export const FLIGHT_PURPOSE_OPTIONS = Object.freeze([
  { label: "1. Geliştirme", value: "option_1" },
  {
    label: "2. Düzenlemelere veya sertifikasyon şartnamelerine uygunluğun gösterilmesi",
    value: "option_2"
  },
  { label: "3. Tasarım ya da üretim kuruluşlarının personel eğitimi", value: "option_3" },
  { label: "4. Yeni üretilen hava araçlarında üretim uçuş testleri", value: "option_4" },
  { label: "5. Üretim tesisleri arasında hava aracının uçurulması", value: "option_5" },
  { label: "6. Müşteri kabulü için uçurulması", value: "option_6" },
  { label: "7. Uçak teslimatı ve ihracı", value: "option_7" },
  { label: "8. Yetkili makam tarafından kabul uçuşu yapılması", value: "option_8" },
  { label: "9. Pazar araştırması, müşterinin personel eğitimi de dahil", value: "option_9" },
  { label: "10. Sergiler ve hava gösterileri", value: "option_10" },
  {
    label: "11. Bakım veya uçuşa elverişlilik incelemesi için ya da depolama yerine uçurulması",
    value: "option_11"
  },
  {
    label:
      "12. MTOW üzerinde, normal menzilin ötesi su veya karada (uygun iniş tesislerinin veya yakıtın bulunmadığı bölgelerde) aşırı yükle uçuş",
    value: "option_12"
  },
  { label: "13. Rekor kırma, hava yarışı veya benzeri yarışmalar", value: "option_13" },
  {
    label:
      "14. Çevresel gereksinimlere (gürültü, emisyon vb.) uyum sağlamadığı halde uçuşa elverişlilik gereksinimlerini karşılayan hava araçlarının uçurulması",
    value: "option_14"
  },
  {
    label:
      "15. Sivil, bireysel ve kompleks olmayan hava araçlarında, UE sertifikası veya Restricted UE olmayan durumlarda ticari olmayan uçuş faaliyetleri",
    value: "option_15"
  },
  {
    label:
      "16. Bakımdan sonra bir veya daha fazla sistem, parça ya da donanım işleyişinin test edilmesi veya sorun giderilme amacıyla uçuş",
    value: "option_16"
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
