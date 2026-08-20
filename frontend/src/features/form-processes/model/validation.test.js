import { describe, expect, it } from "vitest";

import {
  apiFormProcessErrors,
  collectFormProcessErrors,
  validateFormProcessForm
} from "./validation";

const templates = [
  {
    code: "fm_dsg_0200t",
    fields: [{ key: "panel_name", label: "Panel adı", required: true, max_length: 20 }]
  },
  {
    code: "fm_dsg_0327",
    fields: [
      {
        key: "issue_records",
        label: "Yayın geçmişi",
        type: "table",
        required: true,
        max_items: 5,
        columns: [
          { key: "issue", label: "Yayın", type: "text", required: true, max_length: 60 },
          { key: "date", label: "Tarih", type: "date", required: true, max_length: 10 }
        ]
      }
    ]
  },
  {
    code: "fm_qua_0579",
    fields: [
      {
        key: "purpose_of_flight",
        label: "Uçuş amacı",
        type: "multi_select",
        required: false,
        options: [
          { value: "option_1", label: "Geliştirme" },
          { value: "option_6", label: "Müşteri kabulü" }
        ]
      },
      { key: "valid_from", label: "Başlangıç", type: "date", required: true, max_length: 10 },
      { key: "valid_until", label: "Bitiş", type: "date", required: true, max_length: 10 },
      { key: "flight_duration", label: "Süre", type: "text", required: false, max_length: 8 }
    ]
  }
];

describe("form process validation", () => {
  it("validates record identity and required template fields", () => {
    const form = {
      template_code: "fm_dsg_0200t",
      record_number: "PANEL-1",
      title: "Panel beyanı",
      data: { panel_name: "" }
    };
    expect(validateFormProcessForm(form, templates)).toContain("Panel adı");
    form.data.panel_name = "Panel A";
    expect(validateFormProcessForm(form, templates)).toBe("");
    form.record_number = "";
    expect(validateFormProcessForm(form, templates)).toContain("Kayıt numarası");
  });

  it("allows missing template fields for drafts but keeps record identity required", () => {
    const form = {
      template_code: "fm_dsg_0200t",
      record_number: "PANEL-1",
      title: "Panel beyanı",
      data: { panel_name: "" }
    };

    expect(collectFormProcessErrors(form, templates, { requireRequired: false })).toEqual({});
    form.record_number = "";
    expect(collectFormProcessErrors(form, templates, { requireRequired: false })).toHaveProperty(
      "record_number"
    );
  });

  it("maps API validation messages to identity, template and form fields", () => {
    expect(
      apiFormProcessErrors(
        {
          record_number: ["Aynı kayıt numarası kullanılıyor."],
          panel_name: ["Panel adı zorunludur."],
          data: ["Bilinmeyen alan gönderildi."]
        },
        templates[0]
      )
    ).toEqual({
      record_number: "Aynı kayıt numarası kullanılıyor.",
      panel_name: "Panel adı zorunludur.",
      form: "Bilinmeyen alan gönderildi."
    });
  });

  it("validates required structured rows and their dates", () => {
    const form = {
      template_code: "fm_dsg_0327",
      record_number: "FCC-1",
      title: "FCC",
      data: { issue_records: [] }
    };

    expect(validateFormProcessForm(form, templates)).toContain("en az bir satır");
    form.data.issue_records = [{ issue: "TFCC-01.00", date: "17/08/2026" }];
    expect(validateFormProcessForm(form, templates)).toContain("geçerli bir tarih");
    form.data.issue_records[0].date = "2026-08-17";
    expect(validateFormProcessForm(form, templates)).toBe("");
  });

  it("validates flight permit choices, period and duration in the shared form model", () => {
    const form = {
      template_code: "fm_qua_0579",
      record_number: "UI-1",
      title: "Uçuş izni",
      data: {
        purpose_of_flight: ["unknown"],
        valid_from: "2026-09-01",
        valid_until: "2026-08-01",
        flight_duration: "0"
      }
    };

    const errors = collectFormProcessErrors(form, templates);
    expect(errors).toHaveProperty("purpose_of_flight");
    expect(errors).toHaveProperty("valid_until");
    expect(errors).toHaveProperty("flight_duration");
  });
});
