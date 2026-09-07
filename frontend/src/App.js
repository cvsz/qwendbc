import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState("unknown");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();
      setModelStatus(data.model_loaded ? "loaded" : "not_loaded");
    } catch (error) {
      console.error("Health check failed:", error);
      setModelStatus("error");
    }
  };

  const loadModel = async () => {
    setIsLoading(true);
    try {
      await fetch(`${API_URL}/model/load`, { method: "POST" });
      setModelStatus("loaded");
    } catch (error) {
      console.error("Failed to load model:", error);
      alert("Failed to load model. Check backend logs.");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    if (modelStatus !== "loaded") {
      alert("Model not loaded. Please load the model first.");
      return;
    }

    const userMessage = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          temperature: 0.7,
          max_tokens: 2048,
        }),
      });

      if (!response.ok) throw new Error("Request failed");

      const data = await response.json();
      const assistantMessage = {
        role: "assistant",
        content: data.choices[0].message.content,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Send message failed:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Failed to get response" },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Qwen LLM Chat</h1>
        <div className="status-bar">
          <span className={`status ${modelStatus}`}>
            Model: {modelStatus === "loaded" ? "✅ Loaded" : 
                    modelStatus === "not_loaded" ? "⏸️ Not Loaded" : "❌ Error"}
          </span>
          {modelStatus !== "loaded" && (
            <button onClick={loadModel} disabled={isLoading} className="load-btn">
              {isLoading ? "Loading..." : "Load Model"}
            </button>
          )}
          <button onClick={clearChat} className="clear-btn">Clear Chat</button>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <p>Welcome to Qwen LLM Chat!</p>
              <p>Click "Load Model" to start chatting.</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-content">{msg.content}</div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            rows="3"
            disabled={isLoading || modelStatus !== "loaded"}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim() || modelStatus !== "loaded"}
            className="send-btn"
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </div>
      </main>

      <footer className="App-footer">
        <p>Running locally on your machine • Privacy First</p>
      </footer>
    </div>
  );
}

export default App;
