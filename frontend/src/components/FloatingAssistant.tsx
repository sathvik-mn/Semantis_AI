import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MessageSquare, Send } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function FloatingAssistant() {
  const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
  const [isVisible, setIsVisible] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hi! Ask me anything about Semantis AI — semantic caching, pricing, integrations, and more.' },
  ]);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Show bar after scrolling past the hero CTA
  useEffect(() => {
    const handleScroll = () => {
      const ctaButtons = document.getElementById('hero-cta');
      if (ctaButtons) {
        const rect = ctaButtons.getBoundingClientRect();
        // Show as soon as the CTA buttons scroll past the middle of the screen
        setIsVisible(rect.bottom < window.innerHeight * 0.4);
      } else {
        setIsVisible(window.scrollY > 200);
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (inputMode === 'text') {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [inputMode]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = { role: 'user', content: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setTranscript('');
    setShowChat(true);
    setIsLoading(true);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      const res = await fetch(`${backendUrl}/api/assistant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text.trim(),
          history: messages.filter((_, idx) => idx !== 0).map(m => ({ role: m.role, content: m.content })),
        }),
      });

      if (!res.ok) throw new Error('Failed to get response');

      const data = await res.json();
      const reply = data.reply || 'Sorry, I couldn\'t generate a response.';
      setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I\'m having trouble connecting right now. Please try again later.',
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, messages]);

  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setInputMode('text');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const current = event.results[event.results.length - 1];
      setTranscript(current[0].transcript);
      if (current.isFinal) {
        sendMessage(current[0].transcript);
        setIsListening(false);
      }
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [sendMessage]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const isVoice = inputMode === 'voice';

  return (
    <div
      className="fixed bottom-6 left-1/2 z-[9999] flex flex-col items-center gap-3 pointer-events-auto"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translate(-50%, 0)' : 'translate(-50%, 20px)',
        transition: 'opacity 0.4s ease, transform 0.4s ease',
        pointerEvents: isVisible ? 'auto' : 'none',
      }}
    >

      {/* Chat bubble */}
      {showChat && (
        <div
          className="w-[440px] max-h-[360px] rounded-2xl overflow-hidden flex flex-col"
          style={{
            background: 'linear-gradient(180deg, rgba(20,15,30,0.95) 0%, rgba(10,10,11,0.97) 100%)',
            border: '1px solid rgba(255,255,255,0.08)',
            backdropFilter: 'blur(30px)',
            WebkitBackdropFilter: 'blur(30px)',
            boxShadow: '0 24px 80px rgba(0,0,0,0.6), 0 0 1px rgba(255,255,255,0.1)',
          }}
        >
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06]">
            <span className="text-xs font-medium text-white/50 tracking-wide">Semantis AI Assistant</span>
            <button
              type="button"
              onClick={() => setShowChat(false)}
              className="text-[11px] text-white/30 hover:text-white/60 transition-colors cursor-pointer px-2 py-0.5 rounded hover:bg-white/[0.06]"
              style={{ background: 'none', border: 'none' }}
            >
              close
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] px-3.5 py-2.5 text-[13px] leading-relaxed ${
                    msg.role === 'user'
                      ? 'rounded-2xl rounded-br-md text-white'
                      : 'rounded-2xl rounded-bl-md text-white/80'
                  }`}
                  style={
                    msg.role === 'user'
                      ? {
                          background: 'linear-gradient(135deg, rgba(150,60,120,0.35), rgba(100,40,80,0.25))',
                          border: '1px solid rgba(150,60,120,0.3)',
                        }
                      : {
                          background: 'rgba(255,255,255,0.04)',
                          border: '1px solid rgba(255,255,255,0.06)',
                        }
                  }
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="px-3.5 py-2.5 rounded-2xl rounded-bl-md text-white/40"
                     style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <span className="inline-flex gap-1 text-lg">
                    <span className="animate-bounce" style={{ animationDelay: '0ms' }}>·</span>
                    <span className="animate-bounce" style={{ animationDelay: '150ms' }}>·</span>
                    <span className="animate-bounce" style={{ animationDelay: '300ms' }}>·</span>
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Main floating bar — both modes rendered, animated via opacity/transform */}
      <div
        className="relative rounded-full px-1.5 py-1.5"
        style={{
          background: 'linear-gradient(135deg, rgba(20,15,30,0.88) 0%, rgba(10,10,11,0.92) 100%)',
          border: '1px solid rgba(255,255,255,0.08)',
          backdropFilter: 'blur(30px)',
          WebkitBackdropFilter: 'blur(30px)',
          boxShadow: '0 16px 48px rgba(0,0,0,0.5), 0 0 1px rgba(255,255,255,0.08)',
        }}
      >
        {/* Voice mode */}
        <div
          className="flex items-center"
          style={{
            opacity: isVoice ? 1 : 0,
            transform: isVoice ? 'scale(1)' : 'scale(0.95)',
            transition: 'opacity 0.35s ease, transform 0.35s ease',
            pointerEvents: isVoice ? 'auto' : 'none',
            position: isVoice ? 'relative' : 'absolute',
            inset: isVoice ? undefined : 0,
            padding: isVoice ? undefined : '6px',
          }}
        >
          <button
            type="button"
            onClick={isListening ? stopListening : startListening}
            disabled={isLoading}
            className="flex items-center gap-3 rounded-full pl-5 pr-6 py-3 cursor-pointer"
            style={{
              background: isListening
                ? 'linear-gradient(135deg, rgba(180,70,140,0.55), rgba(130,50,110,0.45))'
                : 'linear-gradient(135deg, rgba(150,55,120,0.45), rgba(110,40,90,0.35))',
              border: 'none',
              minWidth: '280px',
              boxShadow: isListening ? '0 0 24px rgba(150,60,120,0.25)' : 'none',
              transition: 'background 0.3s ease, box-shadow 0.3s ease',
            }}
          >
            <Mic className={`w-[18px] h-[18px] flex-shrink-0 ${isListening ? 'text-white animate-pulse' : 'text-white/60'}`}
                 style={{ transition: 'color 0.3s ease' }} />
            <span className="text-[13px] font-semibold tracking-widest text-white/85 uppercase truncate">
              {isListening ? (transcript || 'Listening...') : 'Tap and Ask AI'}
            </span>
          </button>

          <button
            type="button"
            onClick={() => { setInputMode('text'); stopListening(); }}
            className="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer hover:bg-white/[0.08] ml-1"
            style={{ background: 'transparent', border: 'none', transition: 'background 0.2s ease' }}
            aria-label="Switch to text"
          >
            <MessageSquare className="w-[18px] h-[18px] text-white/40" />
          </button>
        </div>

        {/* Text mode */}
        <div
          className="flex items-center"
          style={{
            opacity: isVoice ? 0 : 1,
            transform: isVoice ? 'scale(0.95)' : 'scale(1)',
            transition: 'opacity 0.35s ease, transform 0.35s ease',
            pointerEvents: isVoice ? 'none' : 'auto',
            position: isVoice ? 'absolute' : 'relative',
            inset: isVoice ? 0 : undefined,
            padding: isVoice ? '6px' : undefined,
          }}
        >
          <button
            type="button"
            onClick={() => setInputMode('voice')}
            className="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer hover:bg-white/[0.08] mr-1"
            style={{ background: 'transparent', border: 'none', transition: 'background 0.2s ease' }}
            aria-label="Switch to voice"
          >
            <Mic className="w-[18px] h-[18px] text-white/40" />
          </button>

          <div
            className="flex items-center gap-2.5 rounded-full pl-4 pr-2 py-1.5"
            style={{
              background: 'linear-gradient(135deg, rgba(150,55,120,0.45), rgba(110,40,90,0.35))',
              minWidth: '280px',
            }}
          >
            <MessageSquare className="w-4 h-4 text-white/50 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything..."
              disabled={isLoading}
              className="flex-1 bg-transparent text-[13px] text-white/90 outline-none placeholder:text-white/35 min-w-0 py-1.5"
              style={{ border: 'none' }}
            />
          </div>

          <button
            type="button"
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isLoading}
            className="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer disabled:opacity-25 disabled:cursor-not-allowed hover:bg-white/[0.08] ml-1"
            style={{ background: 'transparent', border: 'none', transition: 'background 0.2s ease, opacity 0.2s ease' }}
            aria-label="Send"
          >
            <Send className="w-[18px] h-[18px] text-white/60" />
          </button>
        </div>
      </div>
    </div>
  );
}
