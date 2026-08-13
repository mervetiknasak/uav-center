import { describe, expect, it } from "vitest";

import { buildFormProcessPayload, createFormProcessForm, flattenFormTemplates } from "./form";

const template = {
  code: "fm_dsg_0200t",
  process_code: "panel-declaration",
  title: "Panel Uyum Beyanı",
  fields: [{ key: "panel_name" }, { key: "declaration" }]
};

describe("form process form model", () => {
  it("initializes template-owned data fields", () => {
    expect(createFormProcessForm(template)).toMatchObject({
      process_code: "panel-declaration",
      template_code: "fm_dsg_0200t",
      data: { panel_name: "", declaration: "" }
    });
  });

  it("flattens the process catalog and normalizes payload identifiers", () => {
    expect(flattenFormTemplates([{ templates: [template] }])).toEqual([template]);
    expect(
      buildFormProcessPayload({
        ...createFormProcessForm(template),
        record_number: " panel-001 ",
        title: "  Uyum Beyanı  "
      })
    ).toMatchObject({ record_number: "PANEL-001", title: "Uyum Beyanı" });
  });
});
