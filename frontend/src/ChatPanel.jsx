import React, { useEffect, useRef, useState } from "react";
import { fetchJSON } from "./lib.js";

const SUGGESTIONS = [
  "Wie ist die Fraktionsverteilung in der 21. Wahlperiode?",
  "Wer ist Olaf Scholz?",
];

function ToolBadge({ tool }) {
  // Shows what the LLM autonomously decided to call — the bonus task, visible.
  const argStr = Object.entries(tool.args || {})
    .map(([k, v]) => `${k}=${v}`)
    .join(", ");
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[11px] ${
        tool.ok
          ? "border-line bg-surface text-ink/70"
          : "border-accent/40 bg-accent/5 text-accent"
      }`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {tool.name}
      {argStr && <span className="opacity-60">({argStr})</span>}
    </span>
  );
}

function Bubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && msg.tools?.length > 0 && (
          <div className="mb-1.5 flex flex-wrap gap-1.5">
            {msg.tools.map((t, i) => (
              <ToolBadge key={i} tool={t} />
            ))}
          </div>
        )}
        <div
          className={`whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "rounded-br-sm bg-ink text-surface"
              : "rounded-bl-sm border border-line bg-surface text-ink/90"
          }`}
        >
          {msg.content}
        </div>
      </div>
    </div>
  );
}

export default function ChatPanel({ groqConfigured }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function send(text) {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    const userMsg = { role: "user", content: q };
    setMessages((m) => [...m, userMsg]);
    setBusy(true);

    // Send prior turns (user + assistant text only) so the agent keeps context.
    const history = messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const res = await fetchJSON("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q, history }),
      });
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, tools: res.tools_used },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Fehler: ${e.message}`, tools: [] },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-line px-6 py-4">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-ink/45">
          Assistent
        </p>
        <h2 className="mt-1 font-display text-lg font-semibold">
          Fragen zu Personen &amp; Fraktionen
        </h2>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <p className="max-w-xs text-sm text-ink/55">
              Stelle eine Frage. Der Assistent wählt selbstständig das passende
              Werkzeug und antwortet auf Basis echter DIP-Daten.
            </p>
            <div className="flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  disabled={!groqConfigured}
                  className="rounded-full border border-line bg-surface px-4 py-1.5 text-sm text-ink/70 transition-colors hover:border-ink/30 hover:text-ink disabled:opacity-40"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <Bubble key={i} msg={m} />
        ))}

        {busy && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm border border-line bg-surface px-4 py-3">
              <Dot delay="0ms" />
              <Dot delay="150ms" />
              <Dot delay="300ms" />
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-line p-4">
        {!groqConfigured && (
          <p className="mb-2 text-center font-mono text-[11px] text-accent">
            GROQ_API_KEY fehlt — Chat ist deaktiviert. Key in .env eintragen.
          </p>
        )}
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={!groqConfigured || busy}
            rows={1}
            placeholder="Frage eingeben …"
            className="max-h-32 flex-1 resize-none rounded-xl border border-line bg-surface px-4 py-2.5 text-sm outline-none transition-colors focus:border-ink/40 disabled:opacity-50"
          />
          <button
            onClick={() => send()}
            disabled={!groqConfigured || busy || !input.trim()}
            className="rounded-xl bg-ink px-4 py-2.5 text-sm font-medium text-surface transition-opacity hover:opacity-90 disabled:opacity-30"
          >
            Senden
          </button>
        </div>
      </div>
    </div>
  );
}

function Dot({ delay }) {
  return (
    <span
      className="h-2 w-2 animate-bounce rounded-full bg-ink/40"
      style={{ animationDelay: delay }}
    />
  );
}
