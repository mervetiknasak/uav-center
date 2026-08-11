import { describe, expect, it } from "vitest";

import { parseNdjsonBuffer, reduceOllamaMessage } from "./ndjson";

describe("NDJSON model helpers", () => {
  it("keeps partial JSON between stream chunks", () => {
    const first = parseNdjsonBuffer("", '{"message":{"content":"Mer', { flush: false });
    expect(first.values).toEqual([]);
    const second = parseNdjsonBuffer(first.remainder, 'haba"}}\n{"done":true', {
      flush: false
    });
    expect(second.values).toEqual([{ message: { content: "Merhaba" } }]);
    expect(parseNdjsonBuffer(second.remainder, "}", { flush: true }).values).toEqual([
      { done: true }
    ]);
  });

  it("ignores blank lines", () => {
    expect(parseNdjsonBuffer("", '\n {"done":true}\r\n\n', { flush: true }).values).toEqual([
      { done: true }
    ]);
  });

  it("accumulates message fields without mutating the input", () => {
    const message = { content: "A", thinking: "T", toolCalls: [], stats: null };
    const next = reduceOllamaMessage(message, {
      message: { content: "B", thinking: "2", tool_calls: [{ function: { name: "x" } }] },
      done: true,
      done_reason: "stop",
      prompt_eval_count: 10,
      eval_count: 4,
      total_duration: 20,
      eval_duration: 8
    });
    expect(next).toMatchObject({
      content: "AB",
      thinking: "T2",
      stats: { doneReason: "stop", promptTokens: 10, outputTokens: 4 }
    });
    expect(next.toolCalls).toHaveLength(1);
    expect(message.content).toBe("A");
  });

  it("raises provider stream errors", () => {
    expect(() => reduceOllamaMessage({}, { error: "model failed" })).toThrow("model failed");
  });
});
