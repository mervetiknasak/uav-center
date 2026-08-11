import { describe, expect, it } from "vitest";

import { normalizePersonGroups } from "./normalizers";

describe("organization normalizers", () => {
  it("normalizes missing and malformed people collections", () => {
    expect(normalizePersonGroups(null)).toEqual([]);
    expect(normalizePersonGroups([{ id: 1 }, { id: 2, people: [{ id: 3 }] }])).toEqual([
      { id: 1, people: [] },
      { id: 2, people: [{ id: 3 }] }
    ]);
  });
});
