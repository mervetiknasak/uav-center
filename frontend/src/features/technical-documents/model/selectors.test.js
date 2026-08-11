import { describe, expect, it } from "vitest";

import {
  calculateTechnicalDocumentMetrics,
  countTechnicalDocumentsForProject,
  filterTechnicalDocuments,
  isTechnicalDocumentOverdue,
  normalizeTechnicalDocumentSearch,
  selectTechnicalDocumentCategories,
  selectProjectDocuments
} from "./selectors";

const documents = [
  {
    id: 1,
    project: 10,
    code: "İHA-SYS-001",
    title: "Uçuş Kontrolü",
    owner_name: "Aviyonik",
    category: "Sistem",
    status: "in_review",
    due_date: "2026-01-10",
    last_notification_at: "2026-01-01T10:00:00Z",
    cover_page: { number: "KP-1", issue: "A" },
    panel_details: [{ id: 7 }]
  },
  {
    id: 2,
    project: 10,
    code: "UAV-OPS-002",
    title: "Operasyon",
    owner_name: "Operasyon",
    category: "Operasyon",
    status: "published",
    due_date: "2025-12-01",
    last_notification_at: null,
    cover_page: null,
    panel_details: []
  },
  {
    id: 3,
    project: 20,
    code: "PAY-003",
    title: "Faydalı Yük",
    owner_name: "Payload",
    category: "Sistem",
    status: "draft",
    due_date: null,
    last_notification_at: null,
    cover_page: null,
    panel_details: []
  }
];

describe("technical document selectors", () => {
  it("normalizes Turkish search text", () => {
    expect(normalizeTechnicalDocumentSearch("  İHA  ")).toBe("iha");
  });

  it("selects a project and applies all filters", () => {
    const projectDocuments = selectProjectDocuments(documents, 10);
    expect(
      filterTechnicalDocuments(projectDocuments, {
        search: "uçuş",
        status: "in_review",
        panelId: 7,
        category: "Sistem"
      }).map((document) => document.id)
    ).toEqual([1]);
    expect(countTechnicalDocumentsForProject(documents, 10)).toBe(2);
  });

  it("returns sorted unique category options", () => {
    expect(selectTechnicalDocumentCategories(documents)).toEqual([
      { label: "Operasyon", value: "Operasyon" },
      { label: "Sistem", value: "Sistem" }
    ]);
  });

  it("does not mark terminal documents overdue", () => {
    expect(isTechnicalDocumentOverdue(documents[0], "2026-02-01")).toBe(true);
    expect(isTechnicalDocumentOverdue(documents[1], "2026-02-01")).toBe(false);
    expect(isTechnicalDocumentOverdue(documents[2], "2026-02-01")).toBe(false);
  });

  it("calculates dashboard metrics deterministically", () => {
    expect(calculateTechnicalDocumentMetrics(documents.slice(0, 2), "2026-02-01")).toEqual({
      total: 2,
      published: 1,
      active: 1,
      overdue: 1,
      notified: 1,
      publicationRate: 50
    });
    expect(calculateTechnicalDocumentMetrics([], "2026-02-01").publicationRate).toBe(0);
  });
});
