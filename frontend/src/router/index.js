import { createRouter, createWebHistory } from "vue-router";

export const DEFAULT_ROUTE_NAME = "technical-documents";

const routes = [
  {
    path: "/",
    redirect: { name: DEFAULT_ROUTE_NAME }
  },
  {
    path: "/technical-documents",
    name: "technical-documents",
    component: () => import("../views/TechnicalDocumentsView.vue"),
    meta: { menuKey: "technical-documents" }
  },
  {
    path: "/organization",
    name: "organization-projects",
    component: () => import("../views/OrganizationView.vue"),
    meta: { menuKey: "organization-projects" }
  },
  {
    path: "/tools/document-processing",
    name: "documents",
    component: () => import("../views/DocumentProcessingView.vue"),
    meta: { menuKey: "documents", anchor: "#document-tools" }
  },
  {
    path: "/tools/ai-results",
    name: "results",
    component: () => import("../views/DocumentProcessingView.vue"),
    meta: { menuKey: "results", anchor: "#ai-results" }
  },
  {
    path: "/tools/word-to-jira",
    name: "word-to-jira",
    component: () => import("../views/WordToJiraView.vue"),
    meta: { menuKey: "word-to-jira" }
  },
  {
    path: "/system",
    name: "system-dashboard",
    component: () => import("../views/SystemView.vue"),
    meta: { menuKey: "system-dashboard", requiresAdmin: true }
  },
  {
    path: "/admin/organization",
    name: "organization-admin",
    component: () => import("../views/OrganizationView.vue"),
    meta: { menuKey: "organization-admin", requiresAdmin: true }
  },
  {
    path: "/admin/users",
    name: "users",
    component: () => import("../views/AdminMembershipView.vue"),
    meta: { menuKey: "users", requiresAdmin: true }
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: { name: DEFAULT_ROUTE_NAME }
  }
];

export const menuSections = [
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
      { label: "Toplantı Tutanağı Okuyucu", key: "word-to-jira" }
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

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.meta.anchor) {
      return { el: to.meta.anchor, behavior: "smooth", top: 16 };
    }
    return { top: 0 };
  }
});

export default router;
