import { describe, expect, it } from "vitest";

import {
  canSubmitOrganizationEditor,
  createOrganizationEditorForm,
  createOrganizationSaveCommand,
  createResponsibleReorder,
  organizationDeletePrompt,
  organizationEditorTitle,
  selectResponsibleForRemoval
} from "./editor";

describe("organization editor model", () => {
  it("creates type-specific form payloads", () => {
    expect(createOrganizationEditorForm("project")).toEqual({
      name: "",
      code: "",
      description: "",
      is_active: true,
      order: 0
    });
    expect(
      createOrganizationEditorForm("person", {
        name: "Ada",
        title: "CVE, AS",
        titles: ["CVE", "AS"],
        email: "ada@example.com",
        username: "ada"
      })
    ).toEqual({
      name: "Ada",
      titles: ["CVE", "AS"],
      email: "ada@example.com",
      username: "ada"
    });
  });

  it("keeps title, submit and save-command behavior", () => {
    expect(organizationEditorTitle("panel")).toBe("Yeni Alt Panel");
    expect(organizationEditorTitle("project", 7)).toBe("Düzenle Proje");
    expect(canSubmitOrganizationEditor("project", { name: "Project", code: "" })).toBe(false);
    expect(canSubmitOrganizationEditor("group", { name: "Team" })).toBe(true);
    expect(
      createOrganizationSaveCommand({
        type: "panel",
        id: 2,
        parentId: 1,
        form: { name: "Panel", order: 3 }
      })
    ).toEqual({
      type: "panel",
      id: 2,
      parentId: 1,
      payload: { name: "Panel", order: 3 }
    });
  });

  it("builds delete confirmation and stable responsible ordering", () => {
    const panel = { id: 10, responsibles: [{ id: 1 }, { id: 2 }] };
    expect(organizationDeletePrompt({ name: "Panel" })).toContain("“Panel”");
    expect(createResponsibleReorder(panel, [{ id: 2 }, { id: 1 }])).toEqual({
      panelId: 10,
      items: [
        { id: 2, order: 0 },
        { id: 1, order: 1 }
      ]
    });
    expect(createResponsibleReorder(panel, [{ id: 1 }])).toBeNull();
    expect(selectResponsibleForRemoval(panel, 1)).toEqual({ id: 2 });
  });
});
