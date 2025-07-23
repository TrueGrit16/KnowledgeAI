import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const clean = (s: string) => s.trim();

type Turn = { id: string; role: 'user' | 'bot' | 'error'; content: string };

export default function Chat() {
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText]   = useState('');
  const [mode, setMode]   = useState<'sop' | 'rca' | 'ticket'>('sop');
  const listRef     = useRef<HTMLDivElement>(null);

  const send = async () => {
    if (!text.trim() || loading) return;
    // add user turn
    setTurns(t => [...t, { id: crypto.randomUUID(), role: 'user', content: text.trim() }]);
    setText('');
    setLoading(true);

    const botId = crypto.randomUUID();
    // add placeholder for bot
    setTurns(t => [...t, { id: botId, role: 'bot', content: '' }]);

    try {
      const response = await axios.post('/chat', { text: text.trim(), mode });
      // pick out the right field if backend still returns { sop: "...", ... }, otherwise fallback
      let answer: string;
      if (response.data && typeof response.data === 'object' && mode in response.data) {
        answer = clean((response.data as Record<string, string>)[mode]);
      } else {
        answer = clean(String(response.data));
      }
      // update bot placeholder with full answer
      setTurns(prev =>
        prev.map(t =>
          t.id === botId ? { ...t, content: answer } : t
        )
      );
    } catch (err: any) {
      setTurns(prev =>
        prev.map(t =>
          t.id === botId
            ? { ...t, role: 'error', content: err.message || 'Request failed' }
            : t
        )
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    // only auto-scroll if near bottom
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (atBottom) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }, [turns]);

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      <div className="px-4 py-2 bg-brand text-black font-semibold">KnowledgeAI Chat</div>
      <div
        ref={listRef}
        className="relative flex-1 overflow-y-auto p-4 space-y-3"
      >
        {turns.filter(t => clean(t.content)).map(t => (
          <div
            key={t.id}
            className={
              t.role === 'user'
                ? 'self-end max-w-md bg-brand/80 rounded-lg p-2 text-black'
                : t.role === 'bot'
                ? 'self-start max-w-prose bg-slate-700 rounded-lg p-2 text-white'
                : 'self-start max-w-prose bg-red-700 rounded-lg p-2 text-white'
            }
          >
            {t.role === 'bot' ? (
              <div className="prose prose-invert max-w-none break-words">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {t.content}
                </ReactMarkdown>
              </div>
            ) : (
              <>{t.content}</>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2 p-2 bg-slate-800">
        <select
          value={mode}
          onChange={e => setMode(e.target.value as any)}
          disabled={loading}
          className="bg-slate-700 rounded text-sm px-2 text-white"
        >
          <option value="sop">SOP</option>
          <option value="rca">RCA</option>
          <option value="ticket">Ticket</option>
        </select>
        <input
          autoFocus
          className="flex-1 bg-slate-700 rounded px-2 outline-none text-white placeholder-gray-400"
          placeholder="Ask something…"
          value={text}
          disabled={loading}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          onChange={e => setText(e.target.value)}
        />
        <button
          onClick={send}
          disabled={loading}
          className="relative bg-brand hover:bg-brand-dark px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? (
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-t-transparent border-white mx-auto inline-block" />
          ) : (
            'Send'
          )}
        </button>
      </div>
    </div>
  );
}