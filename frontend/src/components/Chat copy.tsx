import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';      // optional
import remarkGfm from 'remark-gfm';

type Turn = { id: string; role: 'user' | 'bot' | 'error'; content: string };

export default function Chat() {
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText]   = useState('');
  const [mode, setMode]   = useState<'sop' | 'rca' | 'ticket'>('sop');
  const listRef     = useRef<HTMLDivElement>(null);

  const send = async () => {
    let botId = '';
    if (!text.trim() || loading) return;
    // add user turn
    setTurns(t => [...t, { id: crypto.randomUUID(), role: 'user', content: text.trim() }]);
    setText('');
    setLoading(true);

    // prepare bot placeholder
    botId = crypto.randomUUID();
    setTurns(t => [...t, { id: botId, role: 'bot', content: '' }]);

    try {
      const response = await fetch(
        `/chat/stream?text=${encodeURIComponent(text.trim())}&mode=${mode}`
      );
      if (!response.body) throw new Error('No response body');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        // split on SSE delimiter
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';
        for (const chunk of parts) {
          if (!chunk.startsWith('data:')) continue;
          const data = chunk.slice(5).trim();
          if (data === '[DONE]') {
            setLoading(false);
            reader.cancel();
            return;
          }
          try {
            const json = JSON.parse(data);
            const delta = json.choices?.[0]?.delta?.content || '';
            if (delta) {
              setTurns(prev =>
                prev.map(turn =>
                  turn.id === botId ? { ...turn, content: turn.content + delta } : turn
                )
              );
            }
          } catch {
            // ignore parsing errors
          }
        }
      }
      setLoading(false);
    } catch (err: any) {
      setTurns(prev =>
        prev.map(turn =>
          turn.id === botId
            ? { ...turn, role: 'error', content: err.message || 'Stream error' }
            : turn
        )
      );
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
        {turns.map(t => (
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
              <ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-invert max-w-none">
                {t.content}
              </ReactMarkdown>
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