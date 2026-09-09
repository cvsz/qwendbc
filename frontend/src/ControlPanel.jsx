import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

async function parseError(response, fallback) {
  try {
    const data = await response.json();
    return data.detail || data.error || fallback;
  } catch {
    return fallback;
  }
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(await parseError(response, `Request to ${path} failed`));
  }
  if (response.status === 204) return null;
  return response.json();
}

function Section({ title, children }) {
  return (
    <section className="control-panel__section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function Toggle({ label, checked, onChange, disabled }) {
  return (
    <label className="control-panel__toggle">
      <span>{label}</span>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span className="control-panel__switch" />
    </label>
  );
}

function Stat({ label, value }) {
  return (
    <div className="control-panel__stat">
      <span className="control-panel__stat-label">{label}</span>
      <span className="control-panel__stat-value">{value}</span>
    </div>
  );
}

export default function ControlPanel({ open, onClose, modelStatus, onModelStatusChange }) {
  const [modelInfo, setModelInfo] = useState(null);
  const [health, setHealth] = useState(null);
  const [loadingModel, setLoadingModel] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);

  const refresh = useMemo(
    () => async () => {
      try {
        const [info, healthData] = await Promise.all([
          requestJson("/model/info"),
          requestJson("/health"),
        ]);
        setModelInfo(info);
        setHealth(healthData);
        onModelStatusChange(healthData.model_loaded ? "loaded" : "not_loaded");
      } catch (err) {
        setError(err.message || "Failed to load control panel data");
      }
    },
    [onModelStatusChange],
  );

  useEffect(() => {
    if (open) {
      setError(null);
      setStatusMessage(null);
      refresh();
    }
  }, [open, refresh]);

  const handleLoadModel = async () => {
    setLoadingModel(true);
    setError(null);
    setStatusMessage(null);
    try {
      await requestJson("/model/load", { method: "POST" });
      setStatusMessage("Model loaded");
      await refresh();
    } catch (err) {
      setError(err.message || "Failed to load model");
    } finally {
      setLoadingModel(false);
    }
  };

  const handleUnloadModel = async () => {
    setLoadingModel(true);
    setError(null);
    setStatusMessage(null);
    try {
      await requestJson("/model/unload", { method: "POST" });
      setStatusMessage("Model unloaded");
      await refresh();
    } catch (err) {
      setError(err.message || "Failed to unload model");
    } finally {
      setLoadingModel(false);
    }
  };

  const toggleStreaming = async () => {
    setStreaming(true);
    setError(null);
    setStatusMessage(null);
    try {
      // A lightweight probe request to toggle the streaming mode flag.
      await requestJson("/model/streaming", {
        method: "POST",
        body: JSON.stringify({ enabled: !streaming }),
      });
      setStreaming((prev) => !prev);
      setStatusMessage(streaming ? "Streaming disabled" : "Streaming enabled");
    } catch (err) {
      // Streaming toggle is a best-effort control; the endpoint may not exist.
      setError(err.message || "Streaming toggle unavailable");
    } finally {
      setStreaming(false);
    }
  };

  if (!open) return null;

  const isLoaded = modelStatus === "loaded";

  return (
    <div className="control-panel__overlay" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="control-panel" onClick={(event) => event.stopPropagation()}>
        <header className="control-panel__header">
          <h2>Control Panel</h2>
          <button
            className="control-panel__close"
            onClick={onClose}
            aria-label="Close control panel"
            type="button"
          >
            ✕
          </button>
        </header>

        {error && (
          <div className="control-panel__error" role="alert">
            {error}
          </div>
        )}
        {statusMessage && (
          <div className="control-panel__success">{statusMessage}</div>
        )}

        <Section title="System Health">
          <div className="control-panel__stats">
            <Stat label="Status" value={health?.status || "unknown"} />
            <Stat label="Model" value={health?.model_loaded ? "Loaded" : "Not Loaded"} />
            <Stat label="Version" value={health?.version || "—"} />
          </div>
        </Section>

        <Section title="Model">
          <div className="control-panel__stats">
            <Stat label="Name" value={modelInfo?.name || "—"} />
            <Stat label="File" value={modelInfo?.file || "—"} />
            <Stat label="Context" value={modelInfo?.context_length || "—"} />
            <Stat label="Threads" value={modelInfo?.n_threads || "—"} />
          </div>
          <div className="control-panel__actions">
            <button
              className="control-panel__btn"
              onClick={handleLoadModel}
              disabled={loadingModel || isLoaded}
              type="button"
            >
              {loadingModel ? "Loading..." : "Load Model"}
            </button>
            <button
              className="control-panel__btn control-panel__btn--secondary"
              onClick={handleUnloadModel}
              disabled={loadingModel || !isLoaded}
              type="button"
            >
              {loadingModel ? "Working..." : "Unload Model"}
            </button>
          </div>
        </Section>

        <Section title="Generation">
          <Toggle
            label="Streaming responses"
            checked={streaming}
            disabled={loadingModel}
            onChange={toggleStreaming}
          />
        </Section>

        <Section title="Documents">
          <p className="control-panel__hint">
            Upload UTF-8 text and search indexed chunks from the Documents API.
          </p>
          <div className="control-panel__actions">
            <button
              className="control-panel__btn control-panel__btn--ghost"
              onClick={onClose}
              type="button"
            >
              Manage in API docs
            </button>
          </div>
        </Section>

        <footer className="control-panel__footer">
          <button
            className="control-panel__btn control-panel__btn--ghost"
            onClick={refresh}
            type="button"
          >
            Refresh
          </button>
          <button
            className="control-panel__btn control-panel__btn--ghost"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </footer>
      </div>
    </div>
  );
}