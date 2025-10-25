import React, { useState } from 'react';

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([{ role: 'bot', text: "Hi! I'm GramaBot. How can I help?" }]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const text = input.trim();
    if (!text) return;
    setMessages((m) => [...m, { role: 'user', text }]);
    setInput('');
    setBusy(true);
    try {
      const res = await fetch('http://localhost:8000/api/chatbot/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      const reply = data?.reply || "Sorry, I'm not sure about that.";
      setMessages((m) => [...m, { role: 'bot', text: reply }]);
    } catch {
      setMessages((m) => [...m, { role: 'bot', text: 'Network error. Please try again later.' }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {open && (
        <div style={{ position: 'fixed', right: 16, bottom: 80, width: 320, height: 380, background: '#fff', border: '1px solid #ddd', borderRadius: 8, boxShadow: '0 8px 24px rgba(0,0,0,0.15)', display: 'flex', flexDirection: 'column', overflow: 'hidden', zIndex: 1000 }}>
          <div style={{ padding: 8, background: '#1976d2', color: '#fff', fontWeight: 600 }}>💬 GramaBot</div>
          <div style={{ flex: 1, padding: 8, overflowY: 'auto' }}>
            {messages.map((m, i) => (
              <div key={i} style={{ textAlign: m.role === 'user' ? 'right' : 'left', margin: '6px 0' }}>
                <span style={{ display: 'inline-block', padding: '6px 10px', borderRadius: 12, background: m.role === 'user' ? '#e3f2fd' : '#f5f5f5' }}>{m.text}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, padding: 8, borderTop: '1px solid #eee' }}>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type a message" style={{ flex: 1, border: '1px solid #ddd', borderRadius: 6, padding: '8px 10px' }} onKeyDown={(e) => { if (e.key === 'Enter') send(); }} />
            <button onClick={send} disabled={busy} className="login-btn">Send</button>
          </div>
        </div>
      )}
      <button onClick={() => setOpen(!open)} style={{ position: 'fixed', right: 16, bottom: 16, borderRadius: '999px', padding: '10px 14px', background: '#1976d2', color: '#fff', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.2)', zIndex: 1000 }}>
        {open ? 'Close' : 'Chat'}
      </button>
    </div>
  );
}
