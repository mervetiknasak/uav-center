import { describe, expect, it } from "vitest";

import {
  buildFormProcessPayload,
  buildFormProcessRequestBody,
  createFormProcessForm,
  flattenFormTemplates,
  formProcessRecordToForm
} from "./form";

const template = {
  code: "fm_dsg_0200t",
  process_code: "panel-declaration",
  title: "Panel Uyum Beyanı",
  fields: [
    { key: "panel_name", type: "text" },
    { key: "declaration", type: "textarea" },
    { key: "declaration_date", type: "date" },
    { key: "issue_records", type: "table" },
    { key: "purpose_of_flight", type: "multi_select" }
  ]
};

describe("form process form model", () => {
  it("initializes template-owned data fields", () => {
    expect(createFormProcessForm(template)).toMatchObject({
      process_code: "panel-declaration",
      template_code: "fm_dsg_0200t",
      data: {
        panel_name: "",
        declaration: "",
        declaration_date: null,
        issue_records: [],
        purpose_of_flight: []
      }
    });
  });

  it("uses null for empty date picker values in new and existing records", () => {
    expect(createFormProcessForm(template).data.declaration_date).toBeNull();
    expect(
      formProcessRecordToForm(
        {
          process_code: template.process_code,
          template_code: template.code,
          record_number: "PANEL-1",
          title: "Panel",
          status: "draft",
          data: { declaration_date: "" }
        },
        [template]
      ).data.declaration_date
    ).toBeNull();
  });

  it("flattens the process catalog and normalizes payload identifiers", () => {
    expect(flattenFormTemplates([{ templates: [template] }])).toEqual([template]);
    expect(
      buildFormProcessPayload({
        ...createFormProcessForm(template),
        record_number: " panel-001 ",
        title: "  Uyum Beyanı  "
      })
    ).toMatchObject({
      record_number: "PANEL-001",
      title: "Uyum Beyanı",
      data: { declaration_date: "" }
    });
  });

  it("keeps structured rows and removes completely empty rows from payloads", () => {
    const form = createFormProcessForm(template);
    form.data.issue_records = [
      { issue: "", date: null, prepared_by: "", description: "" },
      {
        issue: "TFCC-01.00",
        date: "2026-08-17",
        prepared_by: "Selin Demir",
        description: "İlk yayın"
      }
    ];

    expect(buildFormProcessPayload(form).data.issue_records).toEqual([
      {
        issue: "TFCC-01.00",
        date: "2026-08-17",
        prepared_by: "Selin Demir",
        description: "İlk yayın"
      }
    ]);
  });

  it("keeps unique multi-select values and builds multipart removal requests", () => {
    const form = createFormProcessForm(template);
    form.data.purpose_of_flight = ["option_1", "option_1", "option_6"];
    const payload = buildFormProcessPayload(form);

    expect(payload.data.purpose_of_flight).toEqual(["option_1", "option_6"]);
    const body = buildFormProcessRequestBody(payload, { removeAttachment: true });
    expect(body).toBeInstanceOf(FormData);
    expect(body.get("remove_attachment")).toBe("true");
    expect(JSON.parse(body.get("data")).purpose_of_flight).toEqual(["option_1", "option_6"]);
  });
});
