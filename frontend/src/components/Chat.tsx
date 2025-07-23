import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';      // optional
import remarkGfm from 'remark-gfm';
import { api } from '../utils/api';

type Turn = { id: string; role: 'user' | 'bot' | 'error'; content: string };

export default function Chat() {
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText]   = useState('');
  const [mode, setMode]   = useState<'sop' | 'rca' | 'ticket'>('sop');
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = async () => {
    const message = text.trim();
    if (!message) return;

    // optimistic user turn
    setTurns(t => [...t, { id: crypto.randomUUID(), role: 'user', content: message }]);
    setText('');
    setLoading(true);

    try {
      // 🚀 call backend
      const { data } = await api.post<string>('/chat', { text: message, mode });
      const answer = data;            // backend now returns plain text
      setTurns(t => [
        ...t,
        { id: crypto.randomUUID(), role: 'bot', content: answer },
      ]);
    } catch (err: any) {
      setTurns(t => [
        ...t,
        { id: crypto.randomUUID(), role: 'error', content: err.message || 'Error' },
      ]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => bottomRef.current?.scrollIntoView({behavior:'smooth'}), [turns]);

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      {/* header */}
      <div className="px-4 py-2 bg-brand">KnowledgeAI Chat</div>

      {/* chat area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading && (
          <div className="flex justify-center my-3">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-t-transparent border-primary" />
          </div>
        )}
        {turns.map(t =>
          <div key={t.id}
               className={t.role==='user'
                 ? 'self-end max-w-md bg-brand/80 rounded-lg p-2'
                 : t.role==='bot'
                    ? 'self-start max-w-prose bg-slate-700 rounded-lg p-2'
                    : 'self-start max-w-prose bg-red-700 rounded-lg p-2'}>
            {t.role==='bot'
              ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    className="prose prose-invert max-w-none"
                  >
                    {t.content}
                  </ReactMarkdown>
                )
              : <>{t.content}</>}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* input bar */}
      <div className="flex gap-2 p-2 bg-slate-800">
        <select value={mode}
                onChange={e=>setMode(e.target.value as any)}
                className="bg-slate-700 rounded text-sm px-2">
          <option value="sop">SOP</option>
          <option value="rca">RCA</option>
          <option value="ticket">Ticket</option>
        </select>
        <input className="flex-1 bg-slate-700 rounded px-2 outline-none"
               placeholder="Ask something…"
               value={text}
               onKeyDown={e=>e.key==='Enter' && send()}
               onChange={e=>setText(e.target.value)} />
        <button
          onClick={send}
          disabled={loading}
          className="bg-brand hover:bg-brand-dark px-3 py-1 rounded disabled:opacity-50"
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}