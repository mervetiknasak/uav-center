import { describe, expect, it } from "vitest";

import {
  buildFlightPermitPayload,
  createFlightPermitForm,
  flightPermitToForm,
  selectExistingFlightPermitDocument
} from "./form";

describe("flight permit form model", () => {
  it("creates fresh defaults and maps records", () => {
    expect(createFlightPermitForm()).toMatchObject({
      permit_type: "domestic",
      status: "approved",
      valid_from: null
    });
    expect(
      flightPermitToForm({
        aircraft_number: "TC-UAV-1",
        permit_number: "P-1",
        permit_type: "test",
        issuing_authority: "SHGM",
        flight_region: "Ankara",
        valid_from: "2026-08-01",
        valid_until: "2026-08-31",
        status: "approved",
        notes: ""
      }).permit_type
    ).toBe("test");
  });

  it("normalizes identifiers in the API payload", () => {
    expect(
      buildFlightPermitPayload({
        ...createFlightPermitForm(),
        aircraft_number: " tc-uav-1 ",
        permit_number: " shgm-1 ",
        issuing_authority: " SHGM "
      })
    ).toMatchObject({
      aircraft_number: "TC-UAV-1",
      permit_number: "SHGM-1",
      issuing_authority: "SHGM"
    });
  });

  it("maps an existing document only when a URL is available", () => {
    expect(selectExistingFlightPermitDocument({ document_url: "" })).toBeNull();
    expect(
      selectExistingFlightPermitDocument({
        document_url: "/document/1",
        document_name: "permit.pdf",
        document_size: 10
      })
    ).toEqual({ name: "permit.pdf", url: "/document/1", size: 10 });
  });
});
