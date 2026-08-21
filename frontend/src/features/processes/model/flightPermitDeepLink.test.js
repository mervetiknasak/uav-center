import { describe, expect, it } from "vitest";

import { resolveFlightPermitDeepLink } from "./flightPermitDeepLink";

const records = [
  { id: 5, process_code: "flight-permits", record_number: "Uİ-5" },
  { id: 6, process_code: "quality", record_number: "KLT-6" }
];

describe("flight permit deep links", () => {
  it("resolves a visible flight permit record", () => {
    expect(resolveFlightPermitDeepLink("5", records)).toEqual({ record: records[0], error: "" });
  });

  it("rejects invalid, missing and non-flight targets without exposing records", () => {
    expect(resolveFlightPermitDeepLink("abc", records).error).toContain("geçersiz");
    expect(resolveFlightPermitDeepLink("99", records).error).toContain("bulunamadı");
    expect(resolveFlightPermitDeepLink("6", records).error).toContain("bulunamadı");
  });
});
