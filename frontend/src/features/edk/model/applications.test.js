import { describe, expect, it } from "vitest";

import { filterEdkApplications } from "./applications";

const applications = [
  {
    id: 11,
    meeting_title: "Uçuş Emniyeti",
    project_name: "UAV Merkezi",
    applicant_name: "ayse",
    location: "Hangar",
    status: "approved"
  },
  {
    id: 12,
    meeting_title: "Kalite Değerlendirmesi",
    project_name: "Atlas",
    applicant_name: "mehmet",
    location: "Toplantı Odası",
    status: "pending"
  }
];

describe("filterEdkApplications", () => {
  it("searches EDK number and Turkish application fields", () => {
    expect(filterEdkApplications(applications, { search: "edk-11" })).toEqual([applications[0]]);
    expect(filterEdkApplications(applications, { search: "uçuş" })).toEqual([applications[0]]);
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
