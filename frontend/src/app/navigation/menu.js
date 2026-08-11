export const DEFAULT_ROUTE_NAME = "technical-documents";

export const menuSections = [
  {
    label: "Uçuş Operasyonları",
    key: "flight-operations",
    children: [{ label: "Uçuş İzinleri", key: "flight-permits" }]
  },
  {
    label: "Doküman Yönetimi",
    key: "document-management",
    children: [{ label: "Teknik Dokümanlar", key: "technical-documents" }]
  },
  {
    label: "Organizasyon",
    key: "organization",
    children: [{ label: "Projeler ve Paneller", key: "organization-projects" }]
  },
  {
    label: "Araçlar",
    key: "tools",
    children: [
      { label: "Belge İşleme", key: "documents" },
      { label: "AI Sonuçları", key: "results" },
      { label: "Gemma 4 Studio", key: "ai-studio" },
      { label: "Toplantı Tutanağı Okuyucu", key: "word-to-jira" }
    ]
  },
  {
    label: "İşlemler",
    key: "operations",
    children: [{ label: "Joblarım", key: "jobs" }]
  },
  {
    label: "Sistem",
    key: "system",
    requiresAdmin: true,
    children: [{ label: "Kontrol Paneli", key: "system-dashboard" }]
  },
  {
    label: "Admin",
    key: "admin",
    requiresAdmin: true,
    children: [
      { label: "Organizasyon Yönetimi", key: "organization-admin" },
      { label: "Üyeler", key: "users" }
    ]
  }
];
