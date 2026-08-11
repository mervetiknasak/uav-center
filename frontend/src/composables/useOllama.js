import { ref } from "vue";

import {
  selectValidImageFiles,
  validateImageDataUrl
} from "../features/ai-studio/model/imageValidation";
import { consumeNdjson, reduceOllamaMessage } from "../features/ai-studio/model/ndjson";

const DEFAULT_SYSTEM_PROMPT =
  "Sen UAV Center içinde çalışan, Türkçe yanıt veren kıdemli bir mühendislik asistanısın. Yanıtların doğru, açık ve uygulanabilir olsun.";

export function useOllama({ apiFetch, ensureCsrfToken, API_BASE_URL }) {
  const status = ref(null);
  const loadingStatus = ref(false);
  const installing = ref(false);
  const unloading = ref(false);
  const generating = ref(false);
  const error = ref("");
  const notice = ref("");
  const input = ref("");
  const systemPrompt = ref(DEFAULT_SYSTEM_PROMPT);
  const images = ref([]);
  const messages = ref([]);
  const toolsText = ref("");
  const settings = ref({
    think: true,
    responseFormat: "text",
    temperature: 1,
    topP: 0.95,
    topK: 64,
    numCtx: 8192,
    numPredict: 2048,
    seed: null,
    keepAlive: "5m"
  });
  let abortController = null;
  const lifecycleController = new AbortController();
  let disposed = false;

  async function loadStatus() {
    if (disposed) return;
    loadingStatus.value = true;
    error.value = "";
    try {
      status.value = await apiFetch("/api/ai/ollama/status/", {
        signal: lifecycleController.signal
      });
    } catch (requestError) {
      if (requestError.name !== "AbortError") error.value = requestError.message;
    } finally {
      loadingStatus.value = false;
    }
  }

  async function installModel() {
    installing.value = true;
    error.value = "";
    notice.value = "Model indiriliyor. Bu işlem bağlantınıza göre uzun sürebilir.";
    try {
      const result = await apiFetch("/api/ai/ollama/pull/", {
        method: "POST",
        signal: lifecycleController.signal
      });
      notice.value = `${result.model} kurulumu tamamlandı.`;
      await loadStatus();
    } catch (requestError) {
      if (requestError.name !== "AbortError") {
        error.value = requestError.message;
        notice.value = "";
      }
    } finally {
      installing.value = false;
    }
  }

  async function unloadModel() {
    unloading.value = true;
    error.value = "";
    try {
      await apiFetch("/api/ai/ollama/unload/", {
        method: "POST",
        signal: lifecycleController.signal
      });
      notice.value = "Model çalışma belleğinden çıkarıldı.";
      await loadStatus();
    } catch (requestError) {
      if (requestError.name !== "AbortError") error.value = requestError.message;
    } finally {
      unloading.value = false;
    }
  }

  async function addImages(fileList) {
    error.value = "";
    const { acceptedFiles, errors } = selectValidImageFiles(images.value, fileList);
    if (errors.length) error.value = errors.at(-1);

    for (const file of acceptedFiles) {
      const dataUrl = await readFile(file);
      const validationError = validateImageDataUrl(images.value, dataUrl);
      if (validationError) {
        error.value = `${file.name}: ${validationError}`;
        continue;
      }
      images.value.push({ name: file.name, dataUrl });
    }
  }

  function removeImage(index) {
    images.value.splice(index, 1);
  }

  function parseTools() {
    const value = toolsText.value.trim();
    if (!value) return [];
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) throw new Error("Araç şeması bir JSON listesi olmalıdır.");
    return parsed;
  }

  async function sendMessage() {
    const content = input.value.trim();
    if ((!content && !images.value.length) || generating.value) return;
    if (!status.value?.connected || !status.value?.installed) {
      error.value = "Sohbet için Ollama çalışıyor ve model kurulu olmalıdır.";
      return;
    }

    let tools;
    try {
      tools = parseTools();
    } catch (parseError) {
      error.value = `Araç şeması okunamadı: ${parseError.message}`;
      return;
    }

    const userMessage = {
      role: "user",
      content: content || "Bu görseli ayrıntılı olarak analiz et.",
      images: images.value.map((image) => image.dataUrl),
      imageNames: images.value.map((image) => image.name)
    };
    messages.value.push(userMessage);
    const assistantMessage = {
      role: "assistant",
      content: "",
      thinking: "",
      toolCalls: [],
      stats: null
    };
    messages.value.push(assistantMessage);
    input.value = "";
    images.value = [];
    error.value = "";
    notice.value = "";
    generating.value = true;
    abortController = new AbortController();

    const payloadMessages = messages.value.slice(0, -1).map((message) => {
      const payload = { role: message.role, content: message.content };
      if (message.images?.length) payload.images = message.images;
      if (message.thinking) payload.thinking = message.thinking;
      if (message.toolCalls?.length) payload.tool_calls = message.toolCalls;
      return payload;
    });

    const body = {
      model: status.value.configured_model,
      messages: payloadMessages,
      system_prompt: systemPrompt.value,
      think: settings.value.think,
      response_format: settings.value.responseFormat,
      tools,
      temperature: settings.value.temperature,
      top_p: settings.value.topP,
      top_k: settings.value.topK,
      num_ctx: settings.value.numCtx,
      num_predict: settings.value.numPredict,
      seed: settings.value.seed,
      keep_alive: settings.value.keepAlive
    };

    try {
      const csrfToken = await ensureCsrfToken({ signal: abortController.signal });
      const response = await fetch(`${API_BASE_URL}/api/ai/ollama/chat/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify(body),
        signal: abortController.signal
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || `HTTP ${response.status}`);
      }
      await consumeNdjson(response, (chunk) => {
        Object.assign(assistantMessage, reduceOllamaMessage(assistantMessage, chunk));
      });
      if (!assistantMessage.content && !assistantMessage.toolCalls.length) {
        assistantMessage.content = "Model metin yanıtı üretmedi.";
      }
    } catch (requestError) {
      if (requestError.name === "AbortError") {
        assistantMessage.stopped = true;
      } else {
        error.value = requestError.message;
        assistantMessage.error = requestError.message;
      }
    } finally {
      generating.value = false;
      abortController = null;
      if (!disposed) await loadStatus();
    }
  }

  function stopGeneration() {
    abortController?.abort();
  }

  function dispose() {
    disposed = true;
    lifecycleController.abort();
    abortController?.abort();
  }

  function clearConversation() {
    if (generating.value) stopGeneration();
    messages.value = [];
    error.value = "";
    notice.value = "";
  }

  return {
    status,
    loadingStatus,
    installing,
    unloading,
    generating,
    error,
    notice,
    input,
    systemPrompt,
    images,
    messages,
    toolsText,
    settings,
    loadStatus,
    installModel,
    unloadModel,
    addImages,
    removeImage,
    sendMessage,
    stopGeneration,
    dispose,
    clearConversation
  };
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error(`${file.name} okunamadı.`));
    reader.readAsDataURL(file);
  });
}
