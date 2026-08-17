import { describe, expect, it } from "vitest";

import { filterFormProcessRecords, filterFormTemplates, groupTemplateFields } from "./selectors";

describe("form process selectors", () => {
  it("keeps source field group order", () => {
    expect(
      groupTemplateFields([
        { key: "a", group: "Genel" },
        { key: "b", group: "Teknik" },
        { key: "c", group: "Genel" }
      ])
    ).toEqual([
      {
        name: "Genel",
        fields: [
          { key: "a", group: "Genel" },
          { key: "c", group: "Genel" }
        ]
      },
      { name: "Teknik", fields: [{ key: "b", group: "Teknik" }] }
    ]);
  });

  it("filters by process, status and Turkish-aware search", () => {
    const records = [
      { record_number: "İHA-1", title: "Panel", process_code: "panel", status: "approved" },
      { record_number: "CRI-1", title: "İnceleme", process_code: "cri", status: "draft" }
    ];
    expect(filterFormProcessRecords(records, { search: "iha", process: "panel" })).toEqual([
      records[0]
    ]);
    expect(filterFormProcessRecords(records, { status: "draft" })).toEqual([records[1]]);
  });

  it("filters templates by process and searchable Turkish text", () => {
    const templates = [
      {
        process_code: "panel",
        form_number: "FM.DSG.1",
        title: "İHA Uyum Beyanı",
        description: "Panel değerlendirmesi"
      },
      { process_code: "cri", form_number: "FM.DSG.2", title: "CRI", description: "İnceleme" }
    ];

    expect(filterFormTemplates(templates, "panel", "iha")).toEqual([templates[0]]);
    expect(filterFormTemplates(templates, "", "inceleme")).toEqual([templates[1]]);
  });
});
