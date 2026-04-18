import React, { useState, useEffect, useRef } from 'react';
import { X, PaperPlaneRight, Robot } from '@phosphor-icons/react';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

export const AIChatDrawer = ({ isOpen, onClose, persona }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const personaColor = persona === 'individual' ? '#1D9E75' : persona === 'shop_owner' ? '#EF9F27' : '#185FA5';

  useEffect(() => {
    if (isOpen) fetchHistory();
  }, [isOpen]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const fetchHistory = async () => {
    try { const { data } = await axios.get(`${API}/api/ai/chat-history`, { withCredentials: true }); setMessages(data.map(d => [{ role: 'user', text: d.message }, { role: 'ai', text: d.response }]).flat()); } catch {}
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    const msg = input; setInput('');
    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/ai/chat`, { message: msg, persona }, { withCredentials: true });
      setMessages(prev => [...prev, { role: 'ai', text: data.response }]);
    } catch { setMessages(prev => [...prev, { role: 'ai', text: 'Sorry, something went wrong. Please try again.' }]); }
    finally { setLoading(false); }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-end bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full sm:w-[400px] h-[85vh] sm:h-[80vh] sm:mr-4 bg-[var(--p-surface)] border border-[var(--p-border)] rounded-t-2xl sm:rounded-2xl flex flex-col shadow-2xl" onClick={e => e.stopPropagation()} data-testid="ai-chat-drawer">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--p-border)]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${personaColor}15` }}>
              <Robot size={18} weight="duotone" style={{ color: personaColor }} />
            </div>
            <div>
              <p className="text-sm font-semibold text-[var(--p-text)]">Capital Care AI</p>
              <p className="text-[10px] text-[var(--p-text-muted)]">Your financial assistant</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="close-chat"><X size={16} /></button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <div className="w-12 h-12 rounded-full mx-auto mb-3 flex items-center justify-center" style={{ background: `${personaColor}15` }}>
                <Robot size={24} weight="duotone" style={{ color: personaColor }} />
              </div>
              <p className="text-sm font-medium text-[var(--p-text)]">Ask me anything!</p>
              <p className="text-xs text-[var(--p-text-muted)] mt-1">
                {persona === 'individual' ? 'Budget tips, savings advice, tax deductions...' : persona === 'shop_owner' ? 'Revenue growth, pricing, GST help...' : 'Tax law, compliance, client advisory...'}
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-3 py-2 rounded-xl text-xs leading-relaxed ${m.role === 'user' ? 'text-white' : 'bg-[var(--p-bg)] text-[var(--p-text)] border border-[var(--p-border)]'}`}
                style={m.role === 'user' ? { background: personaColor } : {}}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-[var(--p-bg)] border border-[var(--p-border)] rounded-xl px-4 py-2">
                <div className="flex gap-1"><span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: personaColor, animationDelay: '0ms' }} /><span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: personaColor, animationDelay: '150ms' }} /><span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: personaColor, animationDelay: '300ms' }} /></div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="p-3 border-t border-[var(--p-border)]">
          <div className="flex gap-2">
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()}
              className="flex-1 h-10 bg-[var(--p-bg)] border border-[var(--p-border)] rounded-xl px-3 text-sm text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[var(--p-primary)] outline-none"
              placeholder="Type a message..." data-testid="chat-input" />
            <button onClick={send} disabled={loading || !input.trim()}
              className="w-10 h-10 rounded-xl flex items-center justify-center text-white disabled:opacity-40 transition-all"
              style={{ background: personaColor }} data-testid="chat-send">
              <PaperPlaneRight size={16} weight="fill" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
