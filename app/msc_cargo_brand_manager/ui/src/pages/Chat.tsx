import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  sql?: string;
  columns?: string[];
  data?: string[][];
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const endpoint = conversationId ? "/api/genie/followup" : "/api/genie/ask";
      const body = conversationId
        ? { conversation_id: conversationId, question }
        : { question };

      const resp = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await resp.json();

      if (data.conversation_id) setConversationId(data.conversation_id);

      const assistantMsg: Message = {
        role: "assistant",
        content: data.text_response || data.description || "Query completed.",
        sql: data.sql,
        columns: data.columns,
        data: data.data,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: any) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b bg-white">
        <h2 className="text-lg font-bold">Ask Genie</h2>
        <p className="text-xs text-slate-500">Ask natural language questions about MSC Cargo brand performance</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20">
            <p className="text-lg mb-2">Ask a question about your brand KPIs</p>
            <div className="space-y-2 text-sm">
              {["Why is NPS so low in South Asia?", "Which campaign had the worst ROI?", "How is our share of voice trending vs Maersk?"].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="block mx-auto px-3 py-1.5 bg-slate-100 rounded-full hover:bg-slate-200 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-lg p-3 ${
              msg.role === "user" ? "bg-blue-600 text-white" : "bg-white border shadow-sm"
            }`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {msg.sql && (
                <details className="mt-2">
                  <summary className="text-xs text-slate-500 cursor-pointer">Show SQL</summary>
                  <pre className="mt-1 text-xs bg-slate-50 p-2 rounded overflow-x-auto">{msg.sql}</pre>
                </details>
              )}

              {msg.columns && msg.data && msg.data.length > 0 && (
                <div className="mt-2 overflow-x-auto">
                  <table className="text-xs w-full border-collapse">
                    <thead>
                      <tr>
                        {msg.columns.map((col) => (
                          <th key={col} className="border-b px-2 py-1 text-left font-medium text-slate-600">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {msg.data.slice(0, 10).map((row, ri) => (
                        <tr key={ri}>
                          {row.map((cell, ci) => (
                            <td key={ci} className="border-b px-2 py-1 text-slate-700">{cell}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {msg.data.length > 10 && (
                    <p className="text-xs text-slate-400 mt-1">Showing 10 of {msg.data.length} rows</p>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border shadow-sm rounded-lg p-3">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about brand performance..."
            className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
          {conversationId && (
            <button
              onClick={() => { setConversationId(null); setMessages([]); }}
              className="px-3 py-2 border rounded-lg text-sm text-slate-600 hover:bg-slate-50"
            >
              New
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
