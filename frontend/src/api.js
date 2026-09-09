const configuredApiUrl = import.meta.env?.VITE_API_URL;
export const API_URL = (configuredApiUrl || "/api/v1").replace(/\/$/, "");
export const ACCESS_TOKEN_STORAGE_KEY = "qwendbc.accessToken";

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function getDefaultStorage() {
  try {
    return globalThis.sessionStorage;
  } catch {
    return undefined;
  }
}

function readAccessToken(storage = getDefaultStorage()) {
  try {
    return storage?.getItem(ACCESS_TOKEN_STORAGE_KEY)?.trim() || "";
  } catch {
    return "";
  }
}

function requestUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_URL}/${String(path).replace(/^\/+/, "")}`;
}

function safeMessage(status) {
  if (status === 401) return "Authentication is required for this action.";
  if (status === 403) return "This action is not available for the current access.";
  if (status === 404) return "The requested QwenDBC resource was not found.";
  if (status === 408 || status === 504) return "The request timed out. Please try again.";
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status >= 500) return "The QwenDBC backend is unavailable right now.";
  return "The request was rejected. Check the input and try again.";
}

function bodyForFetch(body, headers) {
  if (
    body !== null &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof Blob)
  ) {
    if (!Object.keys(headers).some((key) => key.toLowerCase() === "content-type")) {
      headers["Content-Type"] = "application/json";
    }
    return JSON.stringify(body);
  }
  return body;
}

export async function apiRequest(
  path,
  { storage = getDefaultStorage(), fetchImpl = globalThis.fetch, ...options } = {},
) {
  if (typeof fetchImpl !== "function") {
    throw new ApiError(0, "Network access is unavailable in this browser.");
  }

  const headers = { ...options.headers };
  const accessToken = readAccessToken(storage);
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  let response;
  try {
    response = await fetchImpl(requestUrl(path), {
      ...options,
      headers,
      body: bodyForFetch(options.body, headers),
    });
  } catch {
    throw new ApiError(0, "The QwenDBC backend could not be reached.");
  }

  let payload = null;
  try {
    payload = response.status === 204 ? null : await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) throw new ApiError(response.status, safeMessage(response.status));
  return payload;
}

export function fetchModels(options = {}) {
  return apiRequest("/models", { method: "GET", ...options });
}

export function fetchHealth(options = {}) {
  return apiRequest("/health", { method: "GET", ...options });
}

export function refreshModels(options = {}) {
  return apiRequest("/models/refresh", { method: "POST", ...options });
}

export function loadModel(options = {}) {
  return apiRequest("/model/load", { method: "POST", ...options });
}

export function chatCompletion(messages, options = {}) {
  const { provider, model, useRag, ragTopK, ...requestOptions } = options;
  return apiRequest("/chat/completions", {
    method: "POST",
    ...requestOptions,
    body: {
      messages,
      ...(provider ? { provider } : {}),
      ...(model ? { model } : {}),
      ...(typeof useRag === "boolean" ? { use_rag: useRag } : {}),
      ...(ragTopK ? { rag_top_k: ragTopK } : {}),
    },
  });
}

export function parseCompletion(response) {
  const content = response?.choices?.[0]?.message?.content;
  if (typeof content !== "string") throw new Error("Backend returned an invalid chat response");
  return content;
}

export function* parseSseEvents(source) {
  const lines = typeof source === "string" ? source.split(/\r?\n/) : source;
  for (const rawLine of lines) {
    const line = typeof rawLine === "string" ? rawLine.trim() : "";
    if (!line || line.startsWith(":")) continue;
    if (!line.startsWith("data:")) continue;
    const data = line.slice(5).trim();
    if (data === "[DONE]") return;
    try {
      const event = JSON.parse(data);
      if (event && typeof event === "object") yield event;
    } catch {
      // Ignore malformed events; the stream may contain provider keepalives.
    }
  }
}
