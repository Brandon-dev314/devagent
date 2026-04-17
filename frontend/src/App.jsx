import { useState, useRef, useEffect } from "react";


const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "/api/v1";

const HEALTH_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/health`
  : "/health";

function renderMarkdown(text) {
  if (!text) return "";
  return text
    .replace(
      /```(\w*)\n([\s\S]*?)```/g,
      '<pre style="background:rgba(0,0,0,0.06);padding:12px 16px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.5;margin:8px 0"><code>$2</code></pre>'
    )
    .replace(
      /`([^`]+)`/g,
      '<code style="background:rgba(0,0,0,0.06);padding:2px 6px;border-radius:4px;font-size:13px">$1</code>'
    )
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}

function SourceChip({ source }) {
  const name = source.chunk?.metadata?.source?.split("/").pop() || "source";
  const score = source.score ? `${(source.score * 100).toFixed(0)}%` : "";
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: 4,
        padding: "3px 10px", borderRadius: 20,
        background: "rgba(16,185,129,0.1)", color: "#059669",
        fontSize: 11, fontWeight: 600, letterSpacing: 0.3,
      }}
    >
      <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor">
        <path d="M2 4a2 2 0 012-2h4.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V14a2 2 0 01-2 2H4a2 2 0 01-2-2V4z" />
      </svg>
      {name} {score && <span style={{ opacity: 0.7 }}>· {score}</span>}
    </span>
  );
}

function ToolBadge({ tool }) {
  const icons = { rag_search: "🔍", github_create_issue: "🐙", code_executor: "⚡", database: "🗄️" };
  const labels = { rag_search: "Docs", github_create_issue: "GitHub", code_executor: "Code", database: "DB" };
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: 4,
        padding: "3px 10px", borderRadius: 20,
        background: "rgba(99,102,241,0.1)", color: "#4f46e5",
        fontSize: 11, fontWeight: 600,
      }}
    >
      {icons[tool] || "🔧"} {labels[tool] || tool}
    </span>
  );
}

// ── Message bubble ──
function Message({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: 16,
        animation: "fadeUp 0.3s ease",
      }}
    >
      <div
        style={{
          maxWidth: "82%", padding: "14px 18px", borderRadius: 16,
          ...(isUser
            ? { background: "#1e1e2e", color: "#e4e4e7", borderBottomRightRadius: 4 }
            : { background: "#f4f4f5", color: "#18181b", borderBottomLeftRadius: 4 }),
          fontSize: 14, lineHeight: 1.65,
        }}
      >
        {!isUser && (
          <div style={{
            fontSize: 11, fontWeight: 700, color: "#6366f1",
            marginBottom: 6, letterSpacing: 1.2, textTransform: "uppercase",
          }}>
            DevAgent
          </div>
        )}

        <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />

        {msg.tools_used?.length > 0 && (
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
            {msg.tools_used.map((t, i) => <ToolBadge key={i} tool={t} />)}
          </div>
        )}

        {msg.sources?.length > 0 && (
          <div style={{
            marginTop: 10, paddingTop: 10,
            borderTop: "1px solid rgba(0,0,0,0.06)",
          }}>
            <div style={{
              fontSize: 10, fontWeight: 700, color: "#71717a",
              marginBottom: 6, letterSpacing: 0.8, textTransform: "uppercase",
            }}>
              Sources
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {msg.sources.map((s, i) => <SourceChip key={i} source={s} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Typing indicator ──
function TypingDots() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
      <div style={{
        padding: "14px 22px", borderRadius: 16, borderBottomLeftRadius: 4,
        background: "#f4f4f5", display: "flex", gap: 5, alignItems: "center",
      }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 7, height: 7, borderRadius: "50%", background: "#a1a1aa",
              animation: `bounce 1.2s ease-in-out ${i * 0.15}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

// ── Main App ──
export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [status, setStatus] = useState("connecting");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(HEALTH_URL)
      .then((r) => r.json())
      .then(() => setStatus("connected"))
      .catch(() => setStatus("disconnected"));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [loading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.message,
          sources: data.sources || [],
          tools_used: data.tools_used || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error connecting to the API: ${err.message}. Make sure the backend is running.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const newConversation = () => {
    setMessages([]);
    setConversationId(null);
  };

  return (
    <div
      style={{
        display: "flex", flexDirection: "column", height: "100vh",
        fontFamily: "'DM Sans', 'Segoe UI', system-ui, sans-serif",
        background: "#fafafa",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes fadeUp { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        @keyframes bounce { 0%,80%,100% { transform:translateY(0); } 40% { transform:translateY(-6px); } }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
        pre code { font-family: 'JetBrains Mono', monospace !important; }
        textarea:focus { outline: none; }
        textarea::placeholder { color: #a1a1aa; }
      `}</style>

      {/* ── Header ── */}
      <header
        style={{
          padding: "14px 24px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          borderBottom: "1px solid #e4e4e7", background: "#fff",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 34, height: 34, borderRadius: 10, background: "#1e1e2e",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 16,
            }}
          >
            
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#18181b", letterSpacing: -0.3 }}>
              DevAgent
            </div>
            <div style={{ fontSize: 11, color: "#71717a", display: "flex", alignItems: "center", gap: 5 }}>
              <span
                style={{
                  width: 6, height: 6, borderRadius: "50%",
                  background: status === "connected" ? "#22c55e" : status === "connecting" ? "#eab308" : "#ef4444",
                  animation: status === "connecting" ? "pulse 1.5s infinite" : "none",
                }}
              />
              {status === "connected" ? "Online" : status === "connecting" ? "Connecting..." : "Offline"}
              {conversationId && (
                <span style={{ opacity: 0.5 }}>· {conversationId.slice(0, 8)}</span>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={newConversation}
          style={{
            padding: "7px 14px", borderRadius: 8, border: "1px solid #e4e4e7",
            background: "#fff", cursor: "pointer", fontSize: 12, fontWeight: 600,
            color: "#52525b", transition: "all 0.15s",
          }}
          onMouseEnter={(e) => { e.target.style.background = "#f4f4f5"; }}
          onMouseLeave={(e) => { e.target.style.background = "#fff"; }}
        >
          + New chat
        </button>
      </header>

      {/* ── Messages ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 24px 8px" }}>
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", padding: "80px 20px", animation: "fadeUp 0.5s ease" }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🤖</div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: "#18181b", marginBottom: 8, letterSpacing: -0.5 }}>
                DevAgent
              </h2>
              <p style={{ fontSize: 14, color: "#71717a", maxWidth: 400, margin: "0 auto", lineHeight: 1.6 }}>
                AI-powered developer support. Ask about documentation, create GitHub issues, run code, or query databases.
              </p>
              <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 24, flexWrap: "wrap" }}>
                {[
                  "How do I configure CORS in FastAPI?",
                  "Run: print('Hello World!')",
                  "What is dependency injection?",
                ].map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(q)}
                    style={{
                      padding: "8px 16px", borderRadius: 20, border: "1px solid #e4e4e7",
                      background: "#fff", cursor: "pointer", fontSize: 12, color: "#52525b",
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={(e) => { e.target.style.background = "#f4f4f5"; }}
                    onMouseLeave={(e) => { e.target.style.background = "#fff"; }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          {loading && <TypingDots />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* ── Input ── */}
      <div style={{ padding: "12px 24px 20px", borderTop: "1px solid #e4e4e7", background: "#fff" }}>
        <div style={{ maxWidth: 720, margin: "0 auto", display: "flex", gap: 10, alignItems: "flex-end" }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask something..."
            rows={1}
            style={{
              flex: 1, resize: "none", padding: "12px 16px", borderRadius: 12,
              border: "1.5px solid #e4e4e7", fontSize: 14, fontFamily: "inherit",
              lineHeight: 1.5, transition: "border-color 0.15s", background: "#fafafa",
            }}
            onFocus={(e) => { e.target.style.borderColor = "#6366f1"; }}
            onBlur={(e) => { e.target.style.borderColor = "#e4e4e7"; }}
            onInput={(e) => {
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{
              padding: "12px 16px", borderRadius: 12, border: "none",
              background: loading || !input.trim() ? "#d4d4d8" : "#1e1e2e",
              color: "#fff", cursor: loading ? "wait" : "pointer",
              transition: "all 0.15s", display: "flex", alignItems: "center",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}