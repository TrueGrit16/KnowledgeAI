import React, { useState, useRef, useEffect } from "react";
import ChatBubble from "../components/ChatBubble";
import ChatInput from "../components/ChatInput";
import axios from "axios";

export interface Message {
  role: "user" | "assistant" | "error";
  content: string;
}

export default function App() {
  const [history, setHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // auto-scroll
  useEffect(() => {
    containerRef.current?.scrollTo({
      top: containerRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [history]);

  async function handleSend(text: string) {
    setHistory((h) => [...h, { role: "user", content: text }]);
    setLoading(true);

    // Decide which sub-agent to hit
    const mode = text.toLowerCase().includes("ticket")
      ? "ticket"
      : text.includes("why") || text.includes("cause")
      ? "rca"
      : "sop";

    try {
      const { data } = await axios.post("http://127.0.0.1:9191/super", {
        mode,
        payload: { topic: text },
      });

      const reply =
        data.sop ?? data.rca ?? data.resolution ?? data.error ?? JSON.stringify(data);

      setHistory((h) => [...h, { role: "assistant", content: reply }]);
    } catch (err: any) {
      setHistory((h) => [
        ...h,
        { role: "error", content: "Request failed: " + err.message },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-primary text-white px-4 py-2 text-sm">
        KnowledgeAI Chat
      </header>

      {/* Chat scroll area */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto space-y-3 p-4 bg-gray-50 dark:bg-gray-900"
      >
        {history.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} />
        ))}
        {loading && (
          <ChatBubble role="assistant" content="⋯ Thinking / contacting agent …" />
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}