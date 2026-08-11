import { describe, expect, it } from "vitest";

import {
  buildTechnicalDocumentPayload,
  createTechnicalDocumentForm,
  createTechnicalDocumentNotification,
  technicalDocumentToForm,
  validateTechnicalDocumentForm
} from "./form";

describe("technical document form model", () => {
  it("creates independent defaults and maps an existing document", () => {
    const first = createTechnicalDocumentForm(10);
    const second = createTechnicalDocumentForm(20);
    first.panels.push(1);
    expect(second.panels).toEqual([]);
    expect(
      technicalDocumentToForm({
        project: 10,
        panel_details: [{ id: 7 }],
        code: "TD-1",
        title: "Title",
        description: "",
        category: "",
        document_type: "",
        cover_page: { number: "KP-1", issue: "A" },
        revision: "A",
        status: "draft",
        priority: "normal",
        classification: "internal",
        owner_name: "",
        publication_date: null,
        due_date: null,
        review_date: null,
        source_url: "",
        notes: ""
      }).panels
    ).toEqual([7]);
  });

  it("keeps the existing required, publication and cover-page rules", () => {
    const form = createTechnicalDocumentForm(10);
    expect(validateTechnicalDocumentForm(form)).toContain("zorunludur");
    Object.assign(form, { code: "TD-1", title: "Title", status: "published" });
    expect(validateTechnicalDocumentForm(form)).toContain("yayın tarihi");
    Object.assign(form, { publication_date: "2026-08-11", cover_page_number: "KP-1" });
    expect(validateTechnicalDocumentForm(form)).toContain("birlikte");
    form.cover_page_issue = "A";
    expect(validateTechnicalDocumentForm(form)).toBe("");
  });

  it("trims identifiers and serializes optional dates and cover pages", () => {
    const form = {
      ...createTechnicalDocumentForm(10),
      panels: [1, 2],
      code: " TD-1 ",
      title: " Title ",
      cover_page_number: " KP-1 ",
      cover_page_issue: " A "
    };
    expect(buildTechnicalDocumentPayload(form)).toMatchObject({
      code: "TD-1",
      title: "Title",
      panels: [1, 2],
      cover_page: { number: "KP-1", issue: "A" },
      publication_date: null
    });
  });

  it("builds the existing notification defaults", () => {
    const notification = createTechnicalDocumentNotification({
      project_code: "UAV",
      code: "TD-1",
      title: "Title",
      status_display: "Taslak",
      revision: "A",
      publication_date: null,
      due_date: null
    });
    expect(notification.subject).toBe("[UAV] TD-1 — Title");
    expect(notification.message).toContain("Durum: Taslak");
  });
});
