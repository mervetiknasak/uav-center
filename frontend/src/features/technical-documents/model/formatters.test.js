import { describe, expect, it } from "vitest";

import {
  formatTechnicalDocumentDate,
  formatTechnicalDocumentDateTime,
  isoDateKey
} from "./formatters";

describe("technical document formatters", () => {
  it("creates a stable ISO date key", () => {
    expect(isoDateKey(new Date("2026-08-11T23:59:59Z"))).toBe("2026-08-11");
  });

  it("keeps empty date placeholders", () => {
    expect(formatTechnicalDocumentDate(null)).toBe("—");
    expect(formatTechnicalDocumentDateTime("")).toBe("—");
  });

  it("formats date values with the Turkish locale", () => {
    expect(formatTechnicalDocumentDate("2026-08-11")).toContain("2026");
    expect(formatTechnicalDocumentDateTime("2026-08-11T10:30:00Z")).toContain("2026");
  });
});
