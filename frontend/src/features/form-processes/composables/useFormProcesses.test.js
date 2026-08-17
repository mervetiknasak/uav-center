import { describe, expect, it, vi } from "vitest";

import { useFormProcesses } from "./useFormProcesses";

describe("form process records", () => {
  it("archives and reopens records through the existing detail endpoint", async () => {
    const approved = {
      id: 4,
      record_number: "FM-4",
      status: "approved",
      status_display: "Onaylandı"
    };
    const archived = { ...approved, status: "archived", status_display: "Arşivlendi" };
    const draft = { ...approved, status: "draft", status_display: "Taslak" };
    const apiFetch = vi.fn().mockResolvedValueOnce(archived).mockResolvedValueOnce(draft);
    const records = useFormProcesses(apiFetch);
    records.records.value = [approved];

    await records.updateStatus(approved, "archived");
    expect(apiFetch).toHaveBeenLastCalledWith("/api/form-processes/4/", {
      method: "PATCH",
      body: JSON.stringify({ status: "archived" })
    });
    expect(records.records.value[0].status).toBe("archived");

    await records.updateStatus(archived, "draft");
    expect(records.records.value[0].status).toBe("draft");
    expect(records.notice.value).toContain("yeniden taslak");
  });
});
