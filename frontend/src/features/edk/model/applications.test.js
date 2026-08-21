import { describe, expect, it } from "vitest";

import { filterEdkApplications } from "./applications";

const applications = [
  {
    id: 11,
    aircraft_name: "Hürkuş",
    tail_number: "TC-UAV",
    project_display: "UAV — UAV Merkezi",
    applicant_name: "ayse",
    scope: "Uçuş emniyeti",
    status: "approved"
  },
  {
    id: 12,
    aircraft_name: "Gökbey",
    tail_number: "TC-GBY",
    project_display: "ATL — Atlas",
    applicant_name: "mehmet",
    scope: "Kalite değerlendirmesi",
    status: "pending"
  }
];

describe("filterEdkApplications", () => {
  it("searches EDK number and Turkish application fields", () => {
    expect(filterEdkApplications(applications, { search: "edk-11" })).toEqual([applications[0]]);
    expect(filterEdkApplications(applications, { search: "hürkuş" })).toEqual([applications[0]]);
    expect(filterEdkApplications(applications, { search: "tc-uav" })).toEqual([applications[0]]);
  });

  it("combines status and applicant filters", () => {
    expect(
      filterEdkApplications(applications, {
        search: "",
        status: "pending",
        applicant: "mehmet"
      })
    ).toEqual([applications[1]]);
  });
});
