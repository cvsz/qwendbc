import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

async function parseError(response, fallback) {
  try {
    const data = await response.json();
    return data.detail || data.error || fallback;
  } catch {
    return fallback;
  }
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState("unknown");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    let cancelled = false;

    async function checkHealth() {
      try {
        const response = await fetch(`${API_URL}/health`);
        if (!response.ok) {
          throw new Error(await parseError(response, "Health check failed"));
        }
        const data = await response.json();
        if (!cancelled) {
          setModelStatus(data.model_loaded ? "loaded" : "not_loaded");
        }
      } catch (error) {
        console.error("Health check failed:", error);
        if (!cancelled) setModelStatus("error");
      }
    }

    checkHealth();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadModel = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/model/load`, { method: "POST" });
      if (!response.ok) {
        throw new Error(await parseError(response, "Failed to load model"));
      }
      setModelStatus("loaded");
    } catch (error) {
      console.error("Failed to load model:", error);
      setModelStatus("error");
      window.alert(error.message || "Failed to load model. Check backend logs.");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    if (modelStatus !== "loaded") {
      window.alert("Model not loaded. Please load the model first.");
      return;
    }

    const userMessage = { role: "user", content: trimmedInput };
    const conversation = [...messages, userMessage];
    setMessages(conversation);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: conversation,
          temperature: 0.7,
          max_tokens: 2048,
        }),
      });
      if (!response.ok) {
        throw new Error(await parseError(response, "Chat request failed"));
      }

      const data = await response.json();
      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== "string") {
        throw new Error("Backend returned an invalid chat response");
      }
      setMessages((previous) => [...previous, { role: "assistant", content }]);
    } catch (error) {
      console.error("Send message failed:", error);
      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: `Error: ${error.message || "Failed to get response"}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Qwen LLM Chat</h1>
        <div className="status-bar">
          <span className={`status ${modelStatus}`} aria-live="polite">
            Model:{" "}
            {modelStatus === "loaded"
              ? "✅ Loaded"
              : modelStatus === "not_loaded"
                ? "⏸️ Not Loaded"
                : modelStatus === "unknown"
                  ? "… Checking"
                  : "❌ Error"}
          </span>
          {modelStatus !== "loaded" && (
            <button onClick={loadModel} disabled={isLoading} className="load-btn" type="button">
              {isLoading ? "Loading..." : "Load Model"}
            </button>
          )}
          <button onClick={() => setMessages([])} className="clear-btn" type="button">
            Clear Chat
          </button>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container" aria-live="polite">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <p>Welcome to Qwen LLM Chat!</p>
              <p>Load the model, then start chatting locally.</p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
                <div className="message-content">{message.content}</div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={3}
            aria-label="Chat message"
            disabled={isLoading || modelStatus !== "loaded"}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim() || modelStatus !== "loaded"}
            className="send-btn"
            type="button"
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </div>
      </main>

      <footer className="App-footer">
        <p>Local-first inference • Keep the backend private unless you add authentication.</p>
      </footer>
    </div>
  );
}

export default App;
