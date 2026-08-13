import { describe, expect, it } from "vitest";

import {
  FLIGHT_PERMIT_FILE_MAX_BYTES,
  validateFlightPermitFile,
  validateFlightPermitForm
} from "./validation";

const validForm = {
  permit_applicant: "UAV Center",
  permit_number: "SHGM-1",
  valid_from: "2026-08-01",
  valid_until: "2026-08-31",
  template_code: "institution_a",
  template_data: {}
};

const templates = [
  { code: "institution_a", fields: [] },
  {
    code: "institution_b",
    fields: [{ key: "approval_reference", label: "Kurul onay referansı", required: true }]
  }
];

describe("flight permit validation", () => {
  it("validates required fields and date order", () => {
    expect(validateFlightPermitForm({ ...validForm, permit_applicant: "" }, templates)).toContain(
      "zorunludur"
    );
    expect(
      validateFlightPermitForm({ ...validForm, valid_until: "2026-07-31" }, templates)
    ).toContain("önce olamaz");
    expect(validateFlightPermitForm(validForm, templates)).toBe("");
    expect(validateFlightPermitForm({ ...validForm, flight_duration: 0 }, templates)).toContain(
      "en az 1"
    );
    expect(
      validateFlightPermitForm(
        { ...validForm, template_code: "institution_b", template_data: {} },
        templates
      )
    ).toContain("Kurul onay referansı");
  });

  it("validates file extension and size", () => {
    expect(validateFlightPermitFile({ name: "izin.exe", size: 100 })).toContain("Desteklenmeyen");
    for (const name of ["eski-izin.doc", "eski-liste.xls"]) {
      expect(validateFlightPermitFile({ name, size: 100 })).toContain("Desteklenmeyen");
    }
    expect(
      validateFlightPermitFile({ name: "izin.PDF", size: FLIGHT_PERMIT_FILE_MAX_BYTES + 1 })
    ).toContain("15 MB");
    expect(validateFlightPermitFile({ name: "izin.pdf", size: 1024 })).toBe("");
    expect(validateFlightPermitFile({ name: "izin.docx", size: 1024 })).toBe("");
    expect(validateFlightPermitFile({ name: "liste.xlsx", size: 1024 })).toBe("");
  });
});
