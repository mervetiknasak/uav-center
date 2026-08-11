import { describe, expect, it } from "vitest";

import {
  FLIGHT_PERMIT_FILE_MAX_BYTES,
  validateFlightPermitFile,
  validateFlightPermitForm
} from "./validation";

const validForm = {
  aircraft_number: "TC-UAV-1",
  permit_number: "SHGM-1",
  issuing_authority: "SHGM",
  valid_from: "2026-08-01",
  valid_until: "2026-08-31"
};

describe("flight permit validation", () => {
  it("validates required fields and date order", () => {
    expect(validateFlightPermitForm({ ...validForm, aircraft_number: "" })).toContain("zorunludur");
    expect(validateFlightPermitForm({ ...validForm, valid_until: "2026-07-31" })).toContain(
      "önce olamaz"
    );
    expect(validateFlightPermitForm(validForm)).toBe("");
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
