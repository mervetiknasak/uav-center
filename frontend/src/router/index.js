import { createRouter, createWebHistory } from "vue-router";

import { DEFAULT_ROUTE_NAME } from "../app/navigation/menu";

const routes = [
  {
    path: "/",
    redirect: { name: DEFAULT_ROUTE_NAME }
  },
  {
    path: "/technical-documents",
    name: "technical-documents",
    component: () => import("../features/technical-documents/pages/TechnicalDocumentsPage.vue"),
    meta: { menuKey: "technical-documents" }
  },
  {
    path: "/flight-permits",
    name: "flight-permits",
    component: () => import("../features/flight-permits/pages/FlightPermitsPage.vue"),
    meta: { menuKey: "flight-permits" }
  },
  {
    path: "/form-processes",
    name: "form-processes",
    component: () => import("../features/form-processes/pages/FormProcessesPage.vue"),
    meta: { menuKey: "form-processes" }
  },
  {
    path: "/processes/flight-permits/:institution(institution-a|institution-b|institution-c)",
    redirect: { name: "flight-permits" }
  },
  {
    path: "/jobs",
    name: "jobs",
    component: () => import("../features/jobs/pages/JobsPage.vue"),
    meta: { menuKey: "jobs" }
  },
  {
    path: "/organization",
    name: "organization-projects",
    component: () => import("../features/organization/pages/OrganizationPage.vue"),
    meta: { menuKey: "organization-projects" }
  },
  {
    path: "/tools/document-processing",
    name: "documents",
    component: () => import("../features/document-processing/pages/DocumentProcessingPage.vue"),
    meta: { menuKey: "documents", anchor: "#document-tools" }
  },
  {
    path: "/tools/ai-results",
    name: "results",
    component: () => import("../features/document-processing/pages/DocumentProcessingPage.vue"),
    meta: { menuKey: "results", anchor: "#ai-results" }
  },
  {
    path: "/tools/word-to-jira",
    name: "word-to-jira",
    component: () => import("../features/word-to-jira/pages/WordToJiraPage.vue"),
    meta: { menuKey: "word-to-jira" }
  },
  {
    path: "/tools/ai-studio",
    name: "ai-studio",
    component: () => import("../features/ai-studio/pages/AIStudioPage.vue"),
    meta: { menuKey: "ai-studio" }
  },
  {
    path: "/system",
    name: "system-dashboard",
    component: () => import("../features/system-dashboard/pages/SystemDashboardPage.vue"),
    meta: { menuKey: "system-dashboard", requiresAdmin: true }
  },
  {
    path: "/admin/organization",
    name: "organization-admin",
    component: () => import("../features/organization/pages/OrganizationPage.vue"),
    meta: { menuKey: "organization-admin", requiresAdmin: true }
  },
  {
    path: "/admin/users",
    name: "users",
    component: () => import("../features/admin-users/pages/AdminUsersPage.vue"),
    meta: { menuKey: "users", requiresAdmin: true }
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: { name: DEFAULT_ROUTE_NAME }
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
