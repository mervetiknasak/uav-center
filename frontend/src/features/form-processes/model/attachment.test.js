import { describe, expect, it } from "vitest";

import {
  FORM_ATTACHMENT_MAX_BYTES,
  existingFormAttachment,
  formatFormAttachmentSize,
  validateFormAttachment
} from "./attachment";

describe("form process attachments", () => {
  it("accepts bounded modern document formats", () => {
    expect(validateFormAttachment({ name: "izin.pdf", size: 1024 })).toBe("");
    expect(validateFormAttachment({ name: "izin.exe", size: 1024 })).toContain("Desteklenmeyen");
    expect(
      validateFormAttachment({ name: "izin.docx", size: FORM_ATTACHMENT_MAX_BYTES + 1 })
    ).toContain("15 MB");
  });

  it("normalizes existing attachment metadata", () => {
    expect(existingFormAttachment({ attachment_url: "" })).toBeNull();
    expect(
      existingFormAttachment({
        attachment_url: "/api/form-processes/3/attachment/",
        attachment_name: "izin.pdf",
        attachment_size: 2048
      })
    ).toEqual({ name: "izin.pdf", url: "/api/form-processes/3/attachment/", size: 2048 });
    expect(formatFormAttachmentSize(2048)).toBe("2 KB");
  });
});
