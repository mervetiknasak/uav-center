import { describe, expect, it, vi } from "vitest";

import { useOrganizationController } from "./useOrganizationController";

function createController(confirmDelete = vi.fn(() => true)) {
  const callbacks = {
    onSave: vi.fn(),
    onDelete: vi.fn(),
    onReorderResponsibles: vi.fn(),
    confirmDelete
  };
  return { callbacks, controller: useOrganizationController(callbacks) };
}

describe("organization controller", () => {
  it("opens an editor and emits the feature save command", () => {
    const { callbacks, controller } = createController();
    controller.openEditor("project", {
      id: 4,
      name: "UAV",
      code: "UAV-1",
      description: "",
      is_active: true,
      order: 2
    });
    controller.updateFormField("name", "UAV Center");
    controller.submit();

    expect(controller.modalTitle.value).toBe("Düzenle Proje");
    expect(callbacks.onSave).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "project",
        id: 4,
        parentId: null,
        payload: expect.objectContaining({ name: "UAV Center", code: "UAV-1" })
      })
    );
    callbacks.onSave.mock.calls[0][0].done();
    expect(controller.showModal.value).toBe(false);
  });

  it("honors delete confirmation before emitting", () => {
    const denied = createController(vi.fn(() => false));
    denied.controller.requestDelete("panel", { id: 1, name: "Panel" });
    expect(denied.callbacks.onDelete).not.toHaveBeenCalled();

    const accepted = createController();
    const item = { id: 1, name: "Panel" };
    accepted.controller.requestDelete("panel", item);
    expect(accepted.callbacks.onDelete).toHaveBeenCalledWith({ type: "panel", item });
  });

  it("emits valid reorders and responsible removals", () => {
    const { callbacks, controller } = createController();
    const panel = { id: 8, responsibles: [{ id: 1 }, { id: 2 }] };
    controller.reorderResponsibles(panel, [{ id: 2 }, { id: 1 }]);
    expect(callbacks.onReorderResponsibles).toHaveBeenCalledWith({
      panelId: 8,
      items: [
        { id: 2, order: 0 },
        { id: 1, order: 1 }
      ]
    });

    controller.reorderResponsibles(panel, [{ id: 1 }]);
    expect(callbacks.onReorderResponsibles).toHaveBeenCalledTimes(1);
    controller.removeResponsible(panel, 1);
    expect(callbacks.onDelete).toHaveBeenCalledWith({
      type: "responsible",
      item: { id: 2 }
    });
  });
});
