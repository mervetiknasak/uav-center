import { describe, expect, it } from "vitest";

import routerSource from "../../../router/index.js?raw";
import pageSource from "./OperationalCalendarPage.vue?raw";

describe("operational calendar route page", () => {
  it("keeps the route lazy-loaded and linked to the operations menu key", () => {
    expect(routerSource).toContain('path: "/operational-calendar"');
    expect(routerSource).toContain('name: "operational-calendar"');
    expect(routerSource).toContain(
      'import("../features/operational-calendar/pages/OperationalCalendarPage.vue")'
    );
    expect(routerSource).toContain('meta: { menuKey: "operational-calendar" }');
  });

  it("loads alerts through the feature composable", () => {
    expect(pageSource).toContain("useOperationalAlerts(api.apiFetch)");
    expect(pageSource).toContain("onMounted(operationalAlerts.loadAlerts)");
  });
});
