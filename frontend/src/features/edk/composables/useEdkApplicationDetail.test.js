import { describe, expect, it, vi } from "vitest";

import { useEdkApplicationDetail } from "./useEdkApplicationDetail";

describe("useEdkApplicationDetail", () => {
  it("loads and decides the selected application", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce({ id: 7, status: "pending" })
      .mockResolvedValueOnce({ id: 7, status: "approved" });
    const detail = useEdkApplicationDetail(apiFetch);

    await detail.loadApplication(7);
    await detail.decide("approved", "Uygundur");

    expect(apiFetch).toHaveBeenNthCalledWith(1, "/api/edk/applications/7/");
    expect(apiFetch).toHaveBeenNthCalledWith(
      2,
      "/api/edk/applications/7/decision/",
      expect.objectContaining({ method: "POST" })
    );
    expect(detail.application.value.status).toBe("approved");
  });

  it("uploads minutes for the loaded detail and refreshes it", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce({ id: 7, status: "approved" })
      .mockResolvedValueOnce({ application_id: 7, jira_draft: { task: {}, subtasks: [] } })
      .mockResolvedValueOnce({ id: 7, status: "approved", minutes_file_name: "tutanak.docx" });
    const detail = useEdkApplicationDetail(apiFetch);
    const file = new File(["docx"], "tutanak.docx");

    await detail.loadApplication(7);
    await detail.parse({ file });

    expect(apiFetch.mock.calls[1][0]).toBe("/api/edk/applications/7/minutes/parse/");
    expect(apiFetch.mock.calls[1][1].body).toBeInstanceOf(FormData);
    expect(apiFetch).toHaveBeenNthCalledWith(3, "/api/edk/applications/7/");
    expect(detail.application.value.minutes_file_name).toBe("tutanak.docx");
  });
});
