import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  chatCompletion,
  fetchHealth,
  fetchModels,
  getAccessToken,
  loadModel as loadLocalModel,
  parseCompletion,
  refreshModels,
  saveAccessToken,
} from "./api.js";
import {
  THEME_OPTIONS,
  applyTheme,
  readThemePreference,
  resolveTheme,
  saveThemePreference,
} from "./theme.js";
import "./App.css";

const MAX_API_MESSAGES = 128;
const PROVIDER_LABELS = {
  auto: "Automatic free route",
  kilo: "Kilo",
  opencode: "OpenCode",
  openrouter: "OpenRouter",
  local: "Local Qwen",
};
const THEME_LABELS = {
  day: "Day",
  night: "Night",
  system: "System",
};

function providerLabel(name) {
  return PROVIDER_LABELS[name] || name;
}

function statusText(modelStatus, remoteReady) {
  if (modelStatus === "checking") return "Checking local model";
  if (modelStatus === "loaded") return "Local Qwen loaded";
  if (modelStatus === "error") return "Backend status unavailable";
  if (remoteReady) return "Free remote route ready";
  return "Local model not loaded";
}

function statusTone(modelStatus, remoteReady) {
  if (modelStatus === "loaded" || remoteReady) return "ready";
  if (modelStatus === "error") return "danger";
  return "pending";
}

function prefersReducedMotion() {
  try {
    return globalThis.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
  } catch {
    return false;
  }
}

function prefersDarkTheme() {
  try {
    return globalThis.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  } catch {
    return false;
  }
}

function App() {
  const initialTheme = readThemePreference();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState("checking");
  const [health, setHealth] = useState(null);
  const [catalog, setCatalog] = useState(null);
  const [selectedProvider, setSelectedProvider] = useState("auto");
  const [selectedModel, setSelectedModel] = useState("");
  const [useRag, setUseRag] = useState(false);
  const [themePreference, setThemePreference] = useState(initialTheme);
  const [resolvedTheme, setResolvedTheme] = useState(() =>
    resolveTheme(initialTheme, prefersDarkTheme()),
  );
  const [accessToken, setAccessToken] = useState(() => getAccessToken());
  const [routing, setRouting] = useState(null);
  const [notice, setNotice] = useState(null);
  const messagesEndRef = useRef(null);

  const providerStatuses = useMemo(() => {
    const statuses = catalog?.providers?.length ? catalog.providers : health?.providers || [];
    const byName = new Map(statuses.map((provider) => [provider.name, provider]));
    if (!byName.has("local")) {
      byName.set("local", { name: "local", configured: true, available: modelStatus === "loaded" });
    }
    return [...byName.values()];
  }, [catalog, health, modelStatus]);

  const catalogModels = catalog?.data || [];
  const localLoaded = modelStatus === "loaded";
  const remoteReady = providerStatuses.some(
    (provider) => provider.name !== "local" && provider.available,
  );
  const chatAvailable = localLoaded || remoteReady;
  const showLoadLocal = !localLoaded && !remoteReady;

  const selectableProviders = useMemo(() => {
    const names = providerStatuses
      .filter((provider) => provider.available)
      .map((provider) => provider.name);
    return ["auto", ...new Set(names)];
  }, [providerStatuses]);

  const visibleModels = useMemo(
    () =>
      selectedProvider === "auto"
        ? catalogModels
        : catalogModels.filter((model) => model.provider === selectedProvider),
    [catalogModels, selectedProvider],
  );

  const refreshData = useCallback(async (signal) => {
    const healthRequest = fetchHealth({ signal })
      .then((data) => {
        if (signal?.aborted) return null;
        setHealth(data);
        setModelStatus(data.model_loaded ? "loaded" : "not_loaded");
        return data;
      })
      .catch((error) => {
        if (signal?.aborted) return null;
        setModelStatus("error");
        setNotice({ tone: "error", message: error.message || "Health status is unavailable." });
        return null;
      });
    const catalogRequest = fetchModels({ signal })
      .then((data) => {
        if (signal?.aborted) return null;
        setCatalog(data);
        return data;
      })
      .catch((error) => {
        if (signal?.aborted) return null;
        setNotice({
          tone: "warning",
          message: error.message || "The model catalog could not be loaded. You can still try chat.",
        });
        return null;
      });

    const [healthResult, catalogResult] = await Promise.all([healthRequest, catalogRequest]);
    if (!signal?.aborted && !healthResult && !catalogResult) {
      setNotice({ tone: "error", message: "The QwenDBC backend could not be reached." });
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void refreshData(controller.signal);
    return () => controller.abort();
  }, [refreshData]);

  useEffect(() => {
    const media = window.matchMedia?.("(prefers-color-scheme: dark)");
    const updateTheme = () => {
      setResolvedTheme(applyTheme(themePreference, document.documentElement, media?.matches));
    };

    updateTheme();
    if (themePreference !== "system" || !media) return undefined;

    media.addEventListener?.("change", updateTheme);
    media.addListener?.(updateTheme);
    return () => {
      media.removeEventListener?.("change", updateTheme);
      media.removeListener?.(updateTheme);
    };
  }, [themePreference]);

  useEffect(() => {
    const behavior = prefersReducedMotion() ? "auto" : "smooth";
    messagesEndRef.current?.scrollIntoView?.({ behavior, block: "nearest" });
  }, [messages]);

  function selectTheme(preference) {
    if (!THEME_OPTIONS.includes(preference)) return;
    setThemePreference(preference);
    saveThemePreference(preference);
    setResolvedTheme(applyTheme(preference, document.documentElement, prefersDarkTheme()));
  }

  function handleProviderChange(event) {
    const provider = event.target.value;
    setSelectedProvider(provider);
    if (provider === "auto") {
      setSelectedModel("");
      return;
    }
    setSelectedModel(catalogModels.find((model) => model.provider === provider)?.id || "");
  }

  async function handleRefreshCatalog() {
    setNotice(null);
    try {
      const data = await refreshModels();
      setCatalog(data);
      setNotice({ tone: "success", message: "Free model catalog refreshed." });
    } catch (error) {
      setNotice({ tone: "error", message: error.message || "The model catalog could not be refreshed." });
    }
  }

  async function handleSaveAccessToken(event) {
    event.preventDefault();
    saveAccessToken(accessToken);
    setAccessToken(getAccessToken());
    setNotice({
      tone: "success",
      message: accessToken.trim()
        ? "Operator access saved for this browser session."
        : "Operator access cleared for this browser session.",
    });
    const controller = new AbortController();
    await refreshData(controller.signal);
  }

  async function handleLoadModel() {
    if (isLoading) return;
    setIsLoading(true);
    setNotice({ tone: "info", message: "Loading the local Qwen model. This may take a moment." });
    try {
      const data = await loadLocalModel();
      setModelStatus("loaded");
      setHealth((previous) => ({ ...previous, model_loaded: true }));
      setNotice({ tone: "success", message: data.status === "already_loaded" ? "Local Qwen is ready." : "Local Qwen loaded." });
    } catch (error) {
      setModelStatus("error");
      setNotice({ tone: "error", message: error.message || "The local model could not be loaded." });
    } finally {
      setIsLoading(false);
    }
  }

  async function sendMessage() {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;
    if (!chatAvailable) {
      setNotice({ tone: "warning", message: "Load the local model before starting a chat." });
      return;
    }

    const previousMessages = messages;
    const userMessage = { role: "user", content: trimmedInput };
    const conversation = [...previousMessages, userMessage].slice(-MAX_API_MESSAGES);
    setMessages(conversation);
    setInput("");
    setRouting(null);
    setNotice(null);
    setIsLoading(true);

    try {
      const data = await chatCompletion(conversation, {
        provider: selectedProvider === "auto" ? undefined : selectedProvider,
        model: selectedModel || undefined,
        useRag,
      });
      const content = parseCompletion(data);
      setMessages((previous) =>
        [...previous, { role: "assistant", content }].slice(-MAX_API_MESSAGES),
      );
      setRouting(data.qwendbc || null);
      if (data.qwendbc?.fallback) {
        setNotice({
          tone: "warning",
          message: `Fallback used: ${providerLabel(data.qwendbc.provider)} is answering this request.`,
        });
      }
    } catch (error) {
      setMessages(previousMessages);
      setInput(trimmedInput);
      setNotice({ tone: "error", message: error.message || "The chat request failed. Try again." });
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  }

  const statusClass = statusTone(modelStatus, remoteReady);
  const activeRoute = routing
    ? `${providerLabel(routing.provider)} · ${routing.model}`
    : selectedProvider === "auto"
      ? "Automatic free route"
      : providerLabel(selectedProvider);

  return (
    <div className="app-shell" data-resolved-theme={resolvedTheme}>
      <header className="site-header">
        <div className="header-inner">
          <a className="brand" href="#chat" aria-label="QwenDBC home">
            <span className="brand-mark" aria-hidden="true">
              Q
            </span>
            <span>
              <span className="brand-name">QwenDBC</span>
              <span className="brand-caption">knowledge interface / 01</span>
            </span>
          </a>

          <nav className="site-nav" aria-label="Primary navigation">
            <a href="#chat">Chat</a>
            <a href="#control-room">Control room</a>
            <a href="#notes">Notes</a>
          </nav>

          <div className="header-status">
            <span className={`status-dot ${statusClass}`} aria-hidden="true" />
            <span>{statusText(modelStatus, remoteReady)}</span>
          </div>
        </div>
      </header>

      <main className="workspace" id="chat">
        <section className="intro" aria-labelledby="page-title">
          <p className="eyebrow">LOCAL-FIRST / FREE MODEL ROUTING</p>
          <div className="intro-copy">
            <div>
              <h1 id="page-title">Ask better questions.</h1>
              <p className="intro-lede">
                A quiet workspace for Qwen conversations, retrieved context, and resilient free-model access.
              </p>
            </div>
            <div className="intro-index" aria-label="Interface version">
              <span>DBC / 01</span>
              <span>v{health?.version || "1.1"}</span>
            </div>
          </div>
        </section>

        <div className="workspace-grid">
          <section className="chat-panel surface" aria-labelledby="conversation-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">CONVERSATION</p>
                <h2 id="conversation-title">Open channel</h2>
              </div>
              <div className="panel-heading-actions">
                <span className="route-pill" title="Current response route">
                  <span className="route-pulse" aria-hidden="true" />
                  {activeRoute}
                </span>
                <button
                  className="quiet-button"
                  type="button"
                  onClick={() => {
                    setMessages([]);
                    setRouting(null);
                    setNotice(null);
                  }}
                  disabled={isLoading || messages.length === 0}
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="messages-container" aria-live="polite" aria-label="Conversation messages">
              {messages.length === 0 ? (
                <div className="empty-conversation">
                  <span className="empty-glyph" aria-hidden="true">
                    ◌
                  </span>
                  <h3>Start with a sharp prompt.</h3>
                  <p>
                    {chatAvailable
                      ? "Your response will use the selected free route and show which provider answered."
                      : "Load local Qwen or configure an authenticated remote route to begin."}
                  </p>
                </div>
              ) : (
                <ol className="message-list">
                  {messages.map((message, index) => (
                    <li key={`${message.role}-${index}`} className={`message ${message.role}`}>
                      <div className="message-meta">
                        <span>{message.role === "user" ? "YOU" : "QWENDBC"}</span>
                        <span>{String(index + 1).padStart(2, "0")}</span>
                      </div>
                      <p className="message-content">{message.content}</p>
                    </li>
                  ))}
                </ol>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="composer-wrap">
              <div className="composer-meta">
                <span>{isLoading ? "PROCESSING REQUEST" : chatAvailable ? "READY TO RECEIVE" : "WAITING FOR MODEL"}</span>
                <span>{input.length}/200,000</span>
              </div>
              <div className="composer">
                <label className="sr-only" htmlFor="chat-input">
                  Chat message
                </label>
                <textarea
                  id="chat-input"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={chatAvailable ? "Write a message..." : "Load a model to open the channel"}
                  rows={4}
                  disabled={isLoading || !chatAvailable}
                />
                <button
                  className="send-button"
                  onClick={() => void sendMessage()}
                  disabled={isLoading || !input.trim() || !chatAvailable}
                  type="button"
                >
                  <span>{isLoading ? "Working" : "Send"}</span>
                  <span aria-hidden="true">↗</span>
                </button>
              </div>
              <p className="composer-hint">
                <kbd>Enter</kbd> to send <span aria-hidden="true">·</span> <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line
              </p>
            </div>
          </section>

          <aside className="control-column" id="control-room" aria-label="QwenDBC control room">
            <section className="control-card surface" aria-labelledby="route-title">
              <div className="card-heading">
                <div>
                  <p className="eyebrow">ROUTING</p>
                  <h2 id="route-title">Choose a lane</h2>
                </div>
                <span className="card-number">01</span>
              </div>
              <div className="field-stack">
                <div className="field">
                  <label htmlFor="provider-select">Provider</label>
                  <select id="provider-select" value={selectedProvider} onChange={handleProviderChange}>
                    {selectableProviders.map((provider) => (
                      <option key={provider} value={provider}>
                        {providerLabel(provider)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="model-select">Model</label>
                  <select
                    id="model-select"
                    value={selectedModel}
                    onChange={(event) => setSelectedModel(event.target.value)}
                  >
                    <option value="">Provider automatic model</option>
                    {visibleModels.map((model) => (
                      <option key={`${model.provider}-${model.id}`} value={model.id}>
                        {model.name} · {providerLabel(model.provider)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="route-summary" aria-live="polite">
                <span className="summary-label">ACTIVE ROUTE</span>
                <strong>{activeRoute}</strong>
                <span className="summary-note">Free text models only · fallback remains available when configured.</span>
              </div>
              <button className="secondary-button full-width" type="button" onClick={() => void handleRefreshCatalog()}>
                Refresh free catalog
              </button>
            </section>

            <section className="control-card surface" aria-labelledby="model-status-title">
              <div className="card-heading">
                <div>
                  <p className="eyebrow">MODEL STATUS</p>
                  <h2 id="model-status-title">Runtime</h2>
                </div>
                <span className={`status-chip ${statusClass}`}>{statusText(modelStatus, remoteReady)}</span>
              </div>
              <div className="runtime-readout" role="status" aria-live="polite">
                <span className="runtime-model">
                  {health?.selected_model || health?.model_name || "Qwen GGUF"}
                </span>
                <span>{localLoaded ? "Loaded in local memory" : remoteReady ? "Remote access available" : "No serving model loaded"}</span>
              </div>
              {showLoadLocal && (
                <button className="primary-button full-width" type="button" onClick={() => void handleLoadModel()} disabled={isLoading}>
                  {isLoading ? "Loading local model..." : "Load local model"}
                </button>
              )}
              <div className="provider-list" aria-label="Provider availability">
                {providerStatuses.map((provider) => (
                  <div className="provider-row" key={provider.name}>
                    <span>{providerLabel(provider.name)}</span>
                    <span className={provider.available ? "provider-state ready" : "provider-state"}>
                      {provider.available ? "Available" : provider.configured ? "Standby" : "Off"}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section className="control-card surface" aria-labelledby="context-title">
              <div className="card-heading">
                <div>
                  <p className="eyebrow">DOCUMENT CONTEXT</p>
                  <h2 id="context-title">Bring the notes in</h2>
                </div>
                <span className="card-number">02</span>
              </div>
              <label className="toggle-row" htmlFor="rag-toggle">
                <span>
                  <strong>Use retrieved context</strong>
                  <small>Search the local document index for each prompt.</small>
                </span>
                <input
                  id="rag-toggle"
                  type="checkbox"
                  checked={useRag}
                  onChange={(event) => setUseRag(event.target.checked)}
                />
                <span className="toggle-track" aria-hidden="true" />
              </label>
              <p className="card-note">Context is bounded, labeled, and sent only with the request you submit.</p>
            </section>

            <section className="control-card surface" aria-labelledby="access-title">
              <div className="card-heading">
                <div>
                  <p className="eyebrow">OPERATOR ACCESS</p>
                  <h2 id="access-title">Private by default</h2>
                </div>
                <span className="card-number">03</span>
              </div>
              <form className="token-form" onSubmit={(event) => void handleSaveAccessToken(event)}>
                <label htmlFor="access-token">Application access token</label>
                <input
                  id="access-token"
                  type="password"
                  value={accessToken}
                  onChange={(event) => setAccessToken(event.target.value)}
                  placeholder="Paste operator token"
                  autoComplete="off"
                />
                <button className="secondary-button full-width" type="submit">
                  Save for this session
                </button>
              </form>
              <p className="card-note">Stored only in this browser session. Provider credentials stay on the backend.</p>
            </section>
          </aside>
        </div>

        <div className="theme-control" role="group" aria-labelledby="theme-title">
          <div>
            <span className="eyebrow" id="theme-title">INTERFACE THEME</span>
            <span className="theme-current">{THEME_LABELS[themePreference]} / {resolvedTheme} active</span>
          </div>
          <div className="theme-options">
            {THEME_OPTIONS.map((preference) => (
              <button
                className={themePreference === preference ? "theme-button selected" : "theme-button"}
                key={preference}
                type="button"
                aria-pressed={themePreference === preference}
                onClick={() => selectTheme(preference)}
              >
                {THEME_LABELS[preference]}
              </button>
            ))}
          </div>
        </div>

        {notice && (
          <div className={`notice ${notice.tone}`} role={notice.tone === "error" ? "alert" : "status"} aria-live="polite">
            <span className="notice-marker" aria-hidden="true" />
            <span>{notice.message}</span>
          </div>
        )}

        <section className="trust-strip" id="notes" aria-label="QwenDBC guarantees">
          <div>
            <span className="strip-label">01 / LOCAL</span>
            <p>GGUF inference stays available as the final fallback when loaded.</p>
          </div>
          <div>
            <span className="strip-label">02 / FREE</span>
            <p>Automatic routing accepts only eligible free text models.</p>
          </div>
          <div>
            <span className="strip-label">03 / PRIVATE</span>
            <p>Provider keys never cross the backend boundary.</p>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="footer-inner">
          <span>QwenDBC / local-first intelligence</span>
          <span>Built for focused work.</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
