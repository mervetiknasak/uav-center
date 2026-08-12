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
      is_recommendation: false,
      status: "approved",
      valid_from: null
    });
    expect(
      flightPermitToForm({
        permit_applicant: "UAV Center",
        permit_number: "P-1",
        aircraft_nationality: "TR",
        aircraft_id_mark: "TC-UAV-1",
        aircraft_owner: "UAV Center",
        aircraft_type: "Test",
        aircraft_manufacturer: "UAV Center",
        serial_number: "SN-1",
        purpose_of_flight: ["research_development", "customer_acceptance"],
        target_date: "2026-08-15",
        flight_duration: 2,
        aircraft_configuration: "Standart",
        conditions_restrictions: "Ankara",
        conditions_substantiations: "Rapor",
        is_recommendation: true,
        valid_from: "2026-08-01",
        valid_until: "2026-08-31",
        status: "approved",
        notes: ""
      }).purpose_of_flight
    ).toEqual(["research_development", "customer_acceptance"]);
    expect(
      flightPermitToForm({
        ...createFlightPermitForm(),
        purpose_of_flight: ["training"]
      }).purpose_of_flight
    ).toEqual(["training"]);
  });

  it("normalizes identifiers in the API payload", () => {
    expect(
      buildFlightPermitPayload({
        ...createFlightPermitForm(),
        permit_applicant: " UAV Center ",
        aircraft_nationality: " tr ",
        aircraft_id_mark: " tc-uav-1 ",
        permit_number: " shgm-1 ",
        serial_number: " sn-1 "
      })
    ).toMatchObject({
      permit_applicant: "UAV Center",
      aircraft_nationality: "TR",
      aircraft_id_mark: "TC-UAV-1",
      permit_number: "SHGM-1",
      serial_number: "SN-1",
      purpose_of_flight: [],
      target_date: "",
      flight_duration: ""
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
