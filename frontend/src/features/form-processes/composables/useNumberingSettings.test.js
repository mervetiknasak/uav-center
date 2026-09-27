import { describe, expect, it, vi } from "vitest";
import { useNumberingSettings } from "./useNumberingSettings";

const format = {
  code: "TEST",
  name: "Test",
  required_context: [
    { key: "project", required: true, max_length: 10 },
    { key: "branch", required: false, default: "HQ", max_length: 10 }
  ]
};
describe("numbering settings", () => {
  it("loads every format page and initializes context sources", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ results: [format], total_pages: 2 })
      .mockResolvedValueOnce({ results: [{ ...format, code: "SECOND" }], total_pages: 2 });
    const settings = useNumberingSettings({ apiFetch });
    await settings.load();
    expect(settings.formats.value).toHaveLength(2);
    settings.setFormat("TEST");
    expect(settings.form.context_sources).toEqual({
      project: { source: "manual" },
      branch: { source: "default" }
    });
  });
  it("saves the selected mapping and reloads configured mappings", async () => {
    const apiFetch = vi
      .fn()
      .mockResolvedValueOnce({ id: 1 })
      .mockResolvedValueOnce([{ id: 1 }]);
    const settings = useNumberingSettings({ apiFetch });
    Object.assign(settings.form, {
      template_code: "fm_test",
      target_field: "record_number",
      format_code: "TEST",
      context_sources: { project: { source: "fixed", value: "UAV" } }
    });
    await settings.save();
    expect(apiFetch.mock.calls[0][1].method).toBe("POST");
    expect(JSON.parse(apiFetch.mock.calls[0][1].body).context_sources.project.value).toBe("UAV");
    expect(settings.notice.value).toContain("kaydedildi");
    expect(settings.saving.value).toBe(false);
  });
});
