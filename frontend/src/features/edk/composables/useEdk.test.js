import { describe, expect, it, vi } from "vitest";

import { useEdk } from "./useEdk";

describe("useEdk", () => {
  it("loads, creates and decides EDK applications through their feature endpoints", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce([{ id: 1, status: "pending" }])
      .mockResolvedValueOnce({ id: 2, status: "pending" })
      .mockResolvedValueOnce({ id: 1, status: "approved" });
    const edk = useEdk(apiFetch);

    await edk.loadApplications();
    await edk.createApplication({ meeting_title: "Uçuş" });
    await edk.decide({ id: 1 }, "approved", "Uygundur");

    expect(apiFetch).toHaveBeenNthCalledWith(1, "/api/edk/applications/");
    expect(apiFetch).toHaveBeenNthCalledWith(
      2,
      "/api/edk/applications/",
      expect.objectContaining({ method: "POST" })
    );
    expect(apiFetch).toHaveBeenNthCalledWith(
      3,
      "/api/edk/applications/1/decision/",
      expect.objectContaining({ method: "POST" })
    );
    expect(edk.applications.value.map((item) => item.status)).toEqual(["pending", "approved"]);
  });

  it("uploads minutes only through the selected approved application", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce({ application_id: 42, jira_draft: null })
      .mockResolvedValueOnce([]);
    const edk = useEdk(apiFetch);
    const file = new File(["docx"], "tutanak.docx");

    await edk.parse({ applicationId: 42, file });

    expect(apiFetch.mock.calls[0][0]).toBe("/api/edk/applications/42/minutes/parse/");
    expect(apiFetch.mock.calls[0][1].body).toBeInstanceOf(FormData);
  });
});
