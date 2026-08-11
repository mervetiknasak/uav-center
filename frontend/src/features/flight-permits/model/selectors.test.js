import { describe, expect, it } from "vitest";

import {
  calculateFlightPermitMetrics,
  filterFlightPermits,
  normalizeFlightPermitSearch,
  selectAircraftOptions
} from "./selectors";

const permits = [
  {
    id: 1,
    aircraft_number: "TC-İHA-2",
    permit_number: "SHGM-2",
    issuing_authority: "SHGM",
    flight_region: "Ankara",
    document_name: "izin.pdf",
    document_url: "/api/flight-permits/1/document/",
    permit_type: "test",
    validity_status: "active"
  },
  {
    id: 2,
    aircraft_number: "TC-UAV-1",
    permit_number: "SHGM-1",
    issuing_authority: "SHGM",
    flight_region: "Konya",
    document_name: "",
    document_url: "",
    permit_type: "domestic",
    validity_status: "expiring"
  },
  {
    id: 3,
    aircraft_number: "TC-UAV-1",
    permit_number: "SHGM-3",
    issuing_authority: "SHGM",
    flight_region: "İzmir",
    document_name: "",
    document_url: "",
    permit_type: "domestic",
    validity_status: "expired"
  }
];

describe("flight permit selectors", () => {
  it("normalizes Turkish search text", () => {
    expect(normalizeFlightPermitSearch("  İHA  ")).toBe("iha");
  });

  it("creates unique sorted aircraft options", () => {
    expect(selectAircraftOptions(permits)).toEqual([
      { label: "TC-İHA-2", value: "TC-İHA-2" },
      { label: "TC-UAV-1", value: "TC-UAV-1" }
    ]);
  });

  it("combines search, validity, type and aircraft filters", () => {
    expect(
      filterFlightPermits(permits, {
        search: "konya",
        validityStatus: "expiring",
        permitType: "domestic",
        aircraft: "TC-UAV-1"
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
