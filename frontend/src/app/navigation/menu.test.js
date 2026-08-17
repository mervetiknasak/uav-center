import { describe, expect, it } from "vitest";

import { menuSections } from "./menu";

describe("application menu", () => {
  it("exposes Processes as one application instead of nested form applications", () => {
    const processes = menuSections.find((section) => section.key === "processes");

    expect(processes).toEqual({ label: "Süreçler", key: "processes" });
    expect(menuSections.some((section) => section.key === "form-processes")).toBe(false);
    expect(menuSections.some((section) => section.key === "flight-permits")).toBe(false);
  });
});
