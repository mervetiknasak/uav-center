export function parseNdjsonBuffer(buffer, text, { flush = false } = {}) {
  const lines = `${buffer || ""}${text || ""}`.split("\n");
  const remainder = flush ? "" : lines.pop() || "";
  const values = lines
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  return { values, remainder };
}

export function reduceOllamaMessage(message, chunk) {
  if (chunk.error) throw new Error(chunk.error);
  const next = {
    ...message,
    thinking: `${message.thinking || ""}${chunk.message?.thinking || ""}`,
    content: `${message.content || ""}${chunk.message?.content || ""}`,
    toolCalls: [...(message.toolCalls || []), ...(chunk.message?.tool_calls || [])]
  };
  if (chunk.done) {
    next.stats = {
      doneReason: chunk.done_reason,
      promptTokens: chunk.prompt_eval_count || 0,
      outputTokens: chunk.eval_count || 0,
      totalDuration: chunk.total_duration || 0,
      evalDuration: chunk.eval_duration || 0
    };
  }
  return next;
}

export async function consumeNdjson(response, onChunk) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    const decoded = decoder.decode(value || new Uint8Array(), { stream: !done });
    const parsed = parseNdjsonBuffer(buffer, decoded, { flush: done });
    buffer = parsed.remainder;
    parsed.values.forEach(onChunk);
    if (done) break;
  }
}
