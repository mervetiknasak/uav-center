import { describe, expect, it } from "vitest";

import {
  MAX_AI_IMAGE_PAYLOAD_CHARACTERS,
  estimatedImageDataUrlCharacters,
  imagePayloadCharacters,
  selectValidImageFiles,
  validateImageDataUrl,
  validateImagePayload
} from "./imageValidation";

describe("AI image validation", () => {
  it("counts the exact strings sent to the backend", () => {
    expect(imagePayloadCharacters([{ dataUrl: "data:image/png;base64,AAAA" }, "BBBB"])).toBe(
      "data:image/png;base64,AAAA".length + 4
    );
  });

  it("matches backend count and 28,000,000-character limits", () => {
    expect(validateImagePayload(3, MAX_AI_IMAGE_PAYLOAD_CHARACTERS)).toBe("");
    expect(validateImagePayload(4, 10)).toContain("3 görsel");
    expect(validateImagePayload(1, MAX_AI_IMAGE_PAYLOAD_CHARACTERS + 1)).toContain("20 MB");
  });

  it("filters non-image files and aggregate payload overflow", () => {
    const files = [
      { name: "notes.txt", type: "text/plain", size: 10 },
      { name: "large.png", type: "image/png", size: 21 * 1024 * 1024 },
      { name: "small.png", type: "image/png", size: 1024 }
    ];
    const result = selectValidImageFiles([], files);
    expect(result.acceptedFiles.map((file) => file.name)).toEqual(["small.png"]);
    expect(result.errors).toHaveLength(2);
    expect(estimatedImageDataUrlCharacters(files[2])).toBeGreaterThan(files[2].size);
  });

  it("validates an encoded image against the existing payload", () => {
    const existing = [{ dataUrl: "1234" }, { dataUrl: "5678" }];
    expect(validateImageDataUrl(existing, "abcd")).toBe("");
    expect(validateImageDataUrl([...existing, { dataUrl: "9" }], "abcd")).toContain("3 görsel");
  });
});
