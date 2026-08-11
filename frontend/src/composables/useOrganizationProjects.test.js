import { describe, expect, it, vi } from "vitest";

import { useOrganizationProjects } from "./useOrganizationProjects";

describe("organization project read model", () => {
  it("normalizes the project collection for cross-feature consumers", async () => {
    const apiFetch = vi.fn().mockResolvedValue([{ id: 1, code: "TPL" }]);
    const directory = useOrganizationProjects(apiFetch);

    await directory.loadProjects();

    expect(apiFetch).toHaveBeenCalledWith("/api/organization/projects/");
    expect(directory.projects.value).toEqual([{ id: 1, code: "TPL" }]);
    expect(directory.loading.value).toBe(false);
  });

  it("exposes a stable empty collection and user-facing error on failure", async () => {
    const directory = useOrganizationProjects(vi.fn().mockRejectedValue(new Error("offline")));

    await directory.loadProjects();

    expect(directory.projects.value).toEqual([]);
    expect(directory.error.value).toContain("offline");
  });
});
