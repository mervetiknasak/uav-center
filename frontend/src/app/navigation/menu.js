export const DEFAULT_ROUTE_NAME = "technical-documents";

export const menuSections = [
  {
    label: "Süreçler",
    key: "processes"
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
      { label: "EDK", key: "edk" }
    ]
  },
  {
    label: "İşlemler",
    key: "operations",
    children: [
      { label: "Operasyonel Takvim", key: "operational-calendar" },
      { label: "Joblarım", key: "jobs" }
    ]
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
