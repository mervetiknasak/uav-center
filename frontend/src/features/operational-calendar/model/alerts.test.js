import { describe, expect, it } from "vitest";

import {
  filterOperationalAlerts,
  operationalAlertRoute,
  operationalAlertTimingLabel,
  selectOperationalAlertPanels,
  selectOperationalAlertProjects,
  sortOperationalAlerts
} from "./alerts";

const alerts = [
  {
    key: "technical_document:1:due_date",
    source_type: "technical_document",
    source_id: 1,
    bucket: "next_7_days",
    days_remaining: 4,
    days_in_status: null,
    reference: "İHA-SYS-001",
    title: "Uçuş Kontrol Dokümanı",
    status_display: "İncelemede",
    project: { id: 10, code: "İHA", name: "İHA Projesi" },
    panels: [{ id: 7, name: "Aviyonik Paneli" }]
  },
  {
    key: "flight_permit:3:valid_until",
    source_type: "flight_permit",
    source_id: 3,
    bucket: "overdue",
    days_remaining: -2,
    days_in_status: null,
    reference: "Uİ-003",
    title: "Özel uçuş izni",
    status_display: "Onaylandı",
    project: null,
    panels: []
  },
  {
    key: "technical_document:2:workflow_stale",
    source_type: "technical_document",
    source_id: 2,
    bucket: "stale",
    days_remaining: null,
    days_in_status: 18,
    reference: "PAY-002",
    title: "Faydalı Yük",
    status_display: "Revizyon bekliyor",
    project: { id: 20, code: "PAY", name: "Faydalı Yük" },
    panels: [{ id: 8, name: "Yapısal Panel" }]
  }
];

describe("operational alert model", () => {
  it("applies search and source, bucket, project and panel filters", () => {
    expect(
      filterOperationalAlerts(alerts, {
        search: "uçuş kontrol",
        sourceType: "technical_document",
        bucket: "next_7_days",
        projectId: 10,
        panelId: 7
      }).map((alert) => alert.key)
    ).toEqual(["technical_document:1:due_date"]);
  });

  it("sorts urgent dates first and stale items by time in status", () => {
    expect(sortOperationalAlerts(alerts).map((alert) => alert.bucket)).toEqual([
      "overdue",
      "next_7_days",
      "stale"
    ]);
    expect(operationalAlertTimingLabel(alerts[1])).toBe("2 gün gecikti");
    expect(operationalAlertTimingLabel(alerts[2])).toBe("18 gündür bu durumda");
  });

  it("derives unique project and panel filter options", () => {
    expect(selectOperationalAlertProjects(alerts).map((option) => option.value)).toEqual([10, 20]);
    expect(selectOperationalAlertPanels(alerts, 10)).toEqual([
      { label: "Aviyonik Paneli", value: 7 }
    ]);
  });

  it("builds current feature routes without bypassing notification handling", () => {
    expect(operationalAlertRoute(alerts[0])).toEqual({
      name: "technical-documents",
      query: { document: "1" }
    });
    expect(operationalAlertRoute(alerts[0], "notify")).toEqual({
      name: "technical-documents",
      query: { document: "1", action: "notify" }
    });
    expect(operationalAlertRoute(alerts[1])).toEqual({
      name: "processes",
      query: { flightPermit: "3" },
      hash: "#flight-permits"
    });
  });
});
