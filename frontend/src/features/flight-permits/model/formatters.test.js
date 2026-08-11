import { describe, expect, it } from "vitest";

import { formatFlightPermitDate, formatFlightPermitFileSize } from "./formatters";

describe("flight permit formatters", () => {
  it("keeps empty placeholders", () => {
    expect(formatFlightPermitDate(null)).toBe("—");
    expect(formatFlightPermitFileSize(0)).toBe("");
  });

  it("formats byte sizes with the existing UI rules", () => {
    expect(formatFlightPermitFileSize(1)).toBe("1 KB");
    expect(formatFlightPermitFileSize(1024 * 1024)).toBe("1.0 MB");
  });

  it("formats a date with the Turkish locale", () => {
    expect(formatFlightPermitDate("2026-08-11")).toContain("2026");
  });
});
