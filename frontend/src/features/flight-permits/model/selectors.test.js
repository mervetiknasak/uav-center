import { describe, expect, it } from "vitest";

import {
  calculateFlightPermitMetrics,
  filterFlightPermits,
  normalizeFlightPermitSearch,
  selectSerialNumberOptions
} from "./selectors";

const permits = [
  {
    id: 1,
    permit_applicant: "SSB",
    permit_number: "SHGM-2",
    serial_number: "SN-2",
    purpose_of_flight: ["research_development"],
    purpose_of_flight_display: ["Araştırma ve geliştirme uçuşu"],
    document_name: "izin.pdf",
    document_url: "/api/flight-permits/1/document/",
    is_recommendation: true,
    validity_status: "active"
  },
  {
    id: 2,
    permit_applicant: "UAV Center",
    permit_number: "SHGM-1",
    serial_number: "SN-1",
    purpose_of_flight: ["customer_acceptance"],
    purpose_of_flight_display: ["Müşteri kabul uçuşu"],
    document_name: "",
    document_url: "",
    is_recommendation: false,
    validity_status: "expiring"
  },
  {
    id: 3,
    permit_applicant: "UAV Center",
    permit_number: "SHGM-3",
    serial_number: "SN-1",
    purpose_of_flight: ["training"],
    purpose_of_flight_display: ["Eğitim uçuşu"],
    document_name: "",
    document_url: "",
    is_recommendation: false,
    validity_status: "expired"
  }
];

describe("flight permit selectors", () => {
  it("normalizes Turkish search text", () => {
    expect(normalizeFlightPermitSearch("  İHA  ")).toBe("iha");
  });

  it("creates unique sorted serial number options", () => {
    expect(selectSerialNumberOptions(permits)).toEqual([
      { label: "SN-1", value: "SN-1" },
      { label: "SN-2", value: "SN-2" }
    ]);
  });

  it("combines search, validity, type and aircraft filters", () => {
    expect(
      filterFlightPermits(permits, {
        search: "müşteri kabul",
        validityStatus: "expiring",
        recommendation: false,
        serialNumber: "SN-1"
      }).map((permit) => permit.id)
    ).toEqual([2]);
  });

  it("calculates validity and document metrics", () => {
    expect(calculateFlightPermitMetrics(permits)).toEqual({
      total: 3,
      active: 1,
      expiring: 1,
      expired: 1,
      documented: 1
    });
  });
});
