import { describe, expect, it } from "vitest";

import { validateFormProcessForm } from "./validation";

const templates = [
  {
    code: "fm_dsg_0200t",
    fields: [{ key: "panel_name", label: "Panel adı", required: true, max_length: 20 }]
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
});
