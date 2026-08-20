import { describe, expect, it } from "vitest";

import processesPageSource from "./ProcessesPage.vue?raw";
import routerSource from "../../../router/index.js?raw";

describe("unified processes application", () => {
  it("renders engineering forms and flight permits in the same route page", () => {
    expect(processesPageSource).toContain("<FormProcessesScreen");
    expect(processesPageSource).toContain("<FlightPermitsScreen");
    expect(processesPageSource).not.toContain("ProcessAppNavigation");
  });

  it("keeps legacy form URLs as redirects to the unified processes route", () => {
    expect(routerSource).toContain('path: "/processes"');
    expect(routerSource).toContain(
      'component: () => import("../features/processes/pages/ProcessesPage.vue")'
    );
    expect(routerSource.match(/redirect: \{ name: "processes" \}/g)).toHaveLength(3);
    expect(routerSource).not.toContain("FlightPermitsPage.vue");
    expect(routerSource).not.toContain("FormProcessesPage.vue");
  });
});
