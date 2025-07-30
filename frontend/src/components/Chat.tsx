import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


const clean = (s: string) => s.trim();

const normalizeSOP = (md: string) => {
  // Split into lines
  let lines = md.split('\n');

  // Remove lines that are just a bullet or empty
  lines = lines.filter(l => !/^\s*[\*\-\+•‣⁃◦]\s*$/.test(l));

  let normalized: string[] = [];
  let listNumber = 1;
  let inList = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trimEnd();
    // Remove stray bullets at start or end of line
    line = line.replace(/^[\*\-\+•‣⁃◦]\s*/, '');
    line = line.replace(/\s*[\*\-\+•‣⁃◦]$/, '');

    // If the line is empty, just push a blank (will collapse later)
    if (/^\s*$/.test(line)) {
      normalized.push('');
      inList = false;
      continue;
    }

    // If line is a heading or section (starts with #, ends with :, or is bold-only)
    if (/^\s*#/.test(line) || /:\s*$/.test(line) || /^\*\*.*\*\*$/.test(line)) {
      inList = false;
      listNumber = 1;
      normalized.push(line);
      continue;
    }

    // If line is a bullet item (even if indented)
    if (/^\s*[\*\-\+•‣⁃◦]\s+(.*)/.test(lines[i])) {
      const content = lines[i].replace(/^\s*[\*\-\+•‣⁃◦]\s+/, '').replace(/\s*[\*\-\+•‣⁃◦]$/, '');
      if (!inList) {
        inList = true;
        listNumber = 1;
      }
      normalized.push(`${listNumber}. ${content}`);
      listNumber++;
      continue;
    }

    // If line is a numbered list item (even if not sequential)
    if (/^\s*\d+\.\s+(.*)/.test(lines[i])) {
      const content = lines[i].replace(/^\s*\d+\.\s+/, '').replace(/\s*[\*\-\+•‣⁃◦]$/, '');
      if (!inList) {
        inList = true;
        listNumber = 1;
      }
      normalized.push(`${listNumber}. ${content}`);
      listNumber++;
      continue;
    }

    // Otherwise, not a list item
    inList = false;
    normalized.push(line);
  }

  // Join lines and collapse multiple blank lines to one
  let result = normalized
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/(\n\s*){2,}/g, '\n\n')
    // Collapse multiple blank lines between list items into a single newline
    .replace(/(\n\s*){2,}/g, '\n')
    .replace(/(:)\n\n/g, '$1\n') // Remove blank line after headings ending with :
    .trim();
  // Remove any leftover empty lines at the start/end
  result = result.replace(/^\s*\n/, '').replace(/\n\s*$/, '');
  return result;
};

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
        answer = normalizeSOP(clean((response.data as Record<string, string>)[mode]));
      } else {
        answer = normalizeSOP(clean(String(response.data)));
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

/*  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    let frame: number;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    function smoothScrollToBottom() {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      if (distance < 1) return; // already at bottom
      const step = Math.min(30, distance / 12);
      el.scrollBy(0, step);
      frame = requestAnimationFrame(smoothScrollToBottom);
    }
    if (atBottom) {
      smoothScrollToBottom();
    }
    return () => cancelAnimationFrame(frame);
  }, [turns]);*/

  useEffect(() => {
  const el = listRef.current;
  if (!el) return;

  let raf1 = 0;
  let raf2 = 0;

  // After layout
  raf1 = requestAnimationFrame(() => {
    el.scrollTop = el.scrollHeight;
    // One more frame in case images/markdown expand height further
    raf2 = requestAnimationFrame(() => {
      el.scrollTop = el.scrollHeight;
    });
  });

  return () => {
    cancelAnimationFrame(raf1);
    cancelAnimationFrame(raf2);
  };
}, [turns]);

  return (
    <div className="flex flex-col h-screen bg-slate-900 font-sans text-sm">
      <div className="px-4 py-2 bg-brand text-black font-semibold">KnowledgeAI Chat</div>
      <div
        ref={listRef}
        className="relative flex-1 overflow-y-auto px-6 py-4 space-y-2 bg-slate-900"
      >
        {turns.filter(t => clean(t.content)).map(t => (
          <div
            key={t.id}
            className={`rounded-lg px-4 py-2 ${
              t.role === 'user' || t.role === 'error'
                ? 'self-end bg-brand/90 text-black shadow-md whitespace-pre-wrap'
                : 'self-start bg-slate-700 text-white shadow whitespace-normal'
            }`}
          >
            {t.role === 'bot' ? (
              <div
                className={
                  "prose prose-invert max-w-none break-words text-sm " +
                  "prose-p:my-1 " +
                  "prose-ul:mt-0 prose-ul:mb-0 prose-ul:pl-4 " +
                  "prose-ol:mt-0 prose-ol:mb-1 prose-ol:pl-4 prose-ol:list-decimal " +
                  "prose-li:my-0.5 prose-li:pl-2 " +
                  "prose-pre:p-3 prose-pre:bg-slate-800 prose-pre:rounded " +
                  "prose-code:before:content-none prose-code:after:content-none"
                }
              >
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    ol: ({ children, ...props }) => (
                      <ol
                        style={{
                          listStyleType: 'decimal',
                          marginLeft: '1.25em',
                          paddingLeft: '1.25em',
                        }}
                        {...props}
                      >
                        {children}
                      </ol>
                    ),
                    ul: ({ children, ...props }) => (
                      <ol
                        style={{
                          listStyleType: 'decimal',
                          marginLeft: '1.25em',
                          paddingLeft: '1.25em',
                        }}
                        {...props}
                      >
                        {children}
                      </ol>
                    ),
                    li: ({ children, ...props }) => {
                      // If the list item is empty, render nothing
                      if (!children || (Array.isArray(children) && children.length === 0)) {
                        return null;
                      }
                      return (
                        <li style={{ marginBottom: '0.2em' }} {...props}>
                          {children}
                        </li>
                      );
                    },
                  }}
                >
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
          className="bg-slate-700 rounded text-sm px-2 py-1 text-white border border-slate-500 hover:border-white transition"
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