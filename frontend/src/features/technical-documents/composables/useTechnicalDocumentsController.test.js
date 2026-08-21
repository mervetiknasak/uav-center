import { nextTick, ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("naive-ui", () => ({
  useDialog: () => ({ warning: vi.fn() })
}));

import { useTechnicalDocumentsController } from "./useTechnicalDocumentsController";

function createDeepLinkController({ id = 42, action = "detail", canNotify = true } = {}) {
  const ready = ref(false);
  const requested = ref(true);
  const callbacks = { onSave: vi.fn(), onDelete: vi.fn(), onNotify: vi.fn() };
  const controller = useTechnicalDocumentsController({
    projects: ref([{ id: 8, code: "UAV", name: "UAV" }]),
    documents: ref([
      {
        id: 42,
        project: 8,
        code: "UAV-SYS-042",
        title: "Sistem Dokümanı",
        status: "in_review"
      }
    ]),
    deepLinkReady: ready,
    deepLinkRequested: requested,
    deepLinkDocumentId: ref(id),
    deepLinkAction: ref(action),
    canNotify: ref(canNotify),
    ...callbacks
  });
  return { controller, ready };
}

describe("technical document deep links", () => {
  beforeEach(() => vi.clearAllMocks());

  it("selects the document project and opens details after data is ready", async () => {
    const { controller, ready } = createDeepLinkController();

    ready.value = true;
    await nextTick();

    expect(controller.activeProjectId.value).toBe(8);
    expect(controller.detailDocument.value.id).toBe(42);
    expect(controller.showDetail.value).toBe(true);
    expect(controller.deepLinkWarning.value).toBe("");
  });

  it("opens the existing notification modal only for authorized users", async () => {
    const allowed = createDeepLinkController({ action: "notify" });
    allowed.ready.value = true;
    await nextTick();
    expect(allowed.controller.notifyDocument.value.id).toBe(42);
    expect(allowed.controller.showNotify.value).toBe(true);

    const denied = createDeepLinkController({ action: "notify", canNotify: false });
    denied.ready.value = true;
    await nextTick();
    expect(denied.controller.showNotify.value).toBe(false);
    expect(denied.controller.deepLinkWarning.value).toContain("yetkiniz yok");
  });

  it("keeps the normal list visible for an invalid target", async () => {
    const invalid = createDeepLinkController({ id: null });
    invalid.ready.value = true;
    await nextTick();

    expect(invalid.controller.deepLinkWarning.value).toContain("bağlantısı geçersiz");
    expect(invalid.controller.showDetail.value).toBe(false);
  });
});
