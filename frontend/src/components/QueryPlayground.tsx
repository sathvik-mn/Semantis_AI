import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ChatResponse, sendChatCompletionStream, hasApiKey, setApiKey } from '../api/semanticAPI';
import { MarkdownRenderer } from './MarkdownRenderer';
import { Key, ExternalLink, Copy, Trash2, Clock, Send, Bot, User, Zap, Gauge, Layers, Sparkles } from 'lucide-react';

const MAX_HISTORY = 50;
const MESSAGES_KEY_PREFIX = 'semantis_chat_messages_';
const HISTORY_KEY_PREFIX = 'semantis_chat_history_';

/** Get a tenant-scoped storage key based on the current API key. */
function getTenantSlug(): string {
  const key = localStorage.getItem('semantic_api_key') || '';
  // API key format: sc-{tenant}-{rest}
  const parts = key.split('-');
  if (parts.length >= 3) return parts[1];
  return 'default';
}

function getHistoryKey(): string {
  return HISTORY_KEY_PREFIX + getTenantSlug();
}

function getMessagesKey(): string {
  return MESSAGES_KEY_PREFIX + getTenantSlug();
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  meta?: ChatResponse['meta'];
  usage?: ChatResponse['usage'];
  isStreaming?: boolean;
  timestamp: number;
}

interface HistoryEntry {
  id: string;
  prompt: string;
  response: ChatResponse;
  timestamp: number;
}

function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(getHistoryKey());
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveHistory(entries: HistoryEntry[]) {
  localStorage.setItem(getHistoryKey(), JSON.stringify(entries.slice(0, MAX_HISTORY)));
}

function loadMessages(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(getMessagesKey());
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function saveMessages(msgs: ChatMessage[]) {
  // Only persist completed messages (not currently streaming)
  const completed = msgs.filter(m => !m.isStreaming);
  localStorage.setItem(getMessagesKey(), JSON.stringify(completed.slice(-200)));
}

interface QueryPlaygroundProps {
  onQueryComplete?: () => void;
}

export function QueryPlayground({ onQueryComplete }: QueryPlaygroundProps) {
  const [prompt, setPrompt] = useState('');
  const [model, setModelState] = useState(() => {
    try { return localStorage.getItem('semantis_playground_model') || 'gpt-4o-mini'; }
    catch { return 'gpt-4o-mini'; }
  });
  const [temperature, setTemperatureState] = useState(() => {
    try {
      const stored = localStorage.getItem('semantis_playground_temperature');
      return stored !== null ? parseFloat(stored) : 0.2;
    } catch { return 0.2; }
  });

  const setModel = useCallback((value: string) => {
    setModelState(value);
    try { localStorage.setItem('semantis_playground_model', value); } catch {}
  }, []);

  const setTemperature = useCallback((value: number) => {
    setTemperatureState(value);
    try { localStorage.setItem('semantis_playground_temperature', String(value)); } catch {}
  }, []);
  const [messages, setMessages] = useState<ChatMessage[]>(loadMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKeyInput, setShowApiKeyInput] = useState(!hasApiKey());
  const [history, setHistory] = useState<HistoryEntry[]>(loadHistory);
  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const userIsNearBottomRef = useRef(true);

  const isNearBottom = useCallback(() => {
    const el = chatAreaRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < 120;
  }, []);

  const scrollToBottom = useCallback((force?: boolean) => {
    if (force || userIsNearBottomRef.current) {
      const el = chatAreaRef.current;
      if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
      }
      userIsNearBottomRef.current = true;
      setShowScrollBtn(false);
    }
  }, []);

  useEffect(() => {
    if (userIsNearBottomRef.current) {
      scrollToBottom();
    } else {
      // User scrolled away — show the "jump to bottom" button if streaming
      const anyStreaming = messages.some(m => m.isStreaming);
      setShowScrollBtn(anyStreaming);
    }
  }, [messages, scrollToBottom]);

  // Persist messages to localStorage whenever they change (skip while streaming)
  useEffect(() => {
    if (!messages.some(m => m.isStreaming)) {
      saveMessages(messages);
    }
  }, [messages]);

  useEffect(() => {
    const storedKey = localStorage.getItem('semantic_api_key');
    if (storedKey) setShowApiKeyInput(false);
  }, []);

  useEffect(() => {
    const checkKey = () => {
      if (hasApiKey() && showApiKeyInput) setShowApiKeyInput(false);
    };
    window.addEventListener('storage', checkKey);
    const interval = setInterval(checkKey, 2000);
    return () => { window.removeEventListener('storage', checkKey); clearInterval(interval); };
  }, [showApiKeyInput]);

  const addToHistory = useCallback((prompt: string, resp: ChatResponse) => {
    const entry: HistoryEntry = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      prompt,
      response: resp,
      timestamp: Date.now(),
    };
    setHistory(prev => {
      const next = [entry, ...prev].slice(0, MAX_HISTORY);
      saveHistory(next);
      return next;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setHistory([]);
    setMessages([]);
    localStorage.removeItem(getHistoryKey());
    localStorage.removeItem(getMessagesKey());
  }, []);

  const loadFromHistory = useCallback((entry: HistoryEntry) => {
    const userMsg: ChatMessage = {
      id: entry.id + '-u',
      role: 'user',
      content: entry.prompt,
      timestamp: entry.timestamp,
    };
    const assistantMsg: ChatMessage = {
      id: entry.id + '-a',
      role: 'assistant',
      content: entry.response.choices[0]?.message.content || '',
      meta: entry.response.meta,
      usage: entry.response.usage,
      timestamp: entry.timestamp,
    };
    setMessages([userMsg, assistantMsg]);
    setShowHistory(false);
  }, []);

  const handleApiKeySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const key = apiKeyInput.trim();
    if (!key) return;
    if (!key.startsWith('sc-') || key.split('-').length < 3 || key.length < 10) {
      alert('Invalid key format. Key must start with "sc-", contain at least 3 parts separated by hyphens (e.g. sc-tenant-key), and be at least 10 characters long.');
      return;
    }
    setApiKey(key);
    setShowApiKeyInput(false);
    setApiKeyInput('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(36) + '-u',
      role: 'user',
      content: prompt.trim(),
      timestamp: Date.now(),
    };

    const assistantId = Date.now().toString(36) + '-a';
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: Date.now(),
    };

    userIsNearBottomRef.current = isNearBottom();
    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setPrompt('');
    setIsLoading(true);
    setError(null);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      // Real SSE streaming — chunks appear as they arrive from the backend
      let fullContent = '';
      for await (const chunk of sendChatCompletionStream({
        model,
        messages: [{ role: 'user', content: userMessage.content }],
        temperature,
      })) {
        fullContent += chunk;
        const snapshot = fullContent;
        setMessages(prev =>
          prev.map(m => m.id === assistantId ? { ...m, content: snapshot } : m)
        );
      }

      // Mark streaming complete — metadata comes from the next
      // request which will be an instant cache hit.
      const estimatedTokens = Math.ceil(fullContent.split(/\s+/).length * 1.3);
      const streamUsage: ChatResponse['usage'] = {
        prompt_tokens: 0,
        completion_tokens: estimatedTokens,
        total_tokens: estimatedTokens,
      };

      setMessages(prev =>
        prev.map(m => m.id === assistantId
          ? { ...m, content: fullContent, isStreaming: false, usage: streamUsage }
          : m
        )
      );

      // Save to history
      addToHistory(userMessage.content, {
        id: assistantId,
        object: 'chat.completion',
        created: Date.now(),
        model,
        choices: [{ index: 0, message: { role: 'assistant', content: fullContent }, finish_reason: 'stop' }],
        usage: streamUsage,
        meta: { hit: 'miss', similarity: 0, latency_ms: 0, strategy: 'stream' },
      } as ChatResponse);

      if (onQueryComplete) onQueryComplete();
    } catch (err: any) {
      let errorMsg = err?.message || 'Query failed';
      // Make plan limit errors user-friendly
      if (errorMsg.includes('429') && !errorMsg.includes('plan')) {
        errorMsg = 'Monthly request limit reached for your plan. Go to Settings → Billing to upgrade.';
      }
      setError(errorMsg);
      // If we received partial content, keep it visible with an error indicator
      setMessages(prev => {
        const assistantMsg = prev.find(m => m.id === assistantId);
        if (assistantMsg && assistantMsg.content) {
          return prev.map(m => m.id === assistantId
            ? { ...m, isStreaming: false, content: m.content + '\n\n\u26a0 Response was interrupted' }
            : m
          );
        }
        // No content received — remove the empty assistant message
        return prev.filter(m => m.id !== assistantId);
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const autoResizeTextarea = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
  };

  const copyContent = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getBadgeColor = (hit: string) => {
    switch (hit) {
      case 'exact': return '#10b981';
      case 'semantic': return '#3b82f6';
      case 'miss': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getBadgeIcon = (hit: string) => {
    switch (hit) {
      case 'exact': return <Zap size={12} />;
      case 'semantic': return <Sparkles size={12} />;
      default: return <Layers size={12} />;
    }
  };

  return (
    <div style={styles.container}>
      {/* API Key Prompt */}
      {showApiKeyInput && (
        <div style={styles.apiKeyBanner}>
          <Key size={18} style={{ color: '#60a5fa' }} />
          <span style={{ flex: 1, color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
            API key required.{' '}
            <Link to="/settings" style={{ color: '#60a5fa', textDecoration: 'none' }}>
              Generate in Settings <ExternalLink size={12} style={{ verticalAlign: 'middle' }} />
            </Link>
          </span>
          <form onSubmit={handleApiKeySubmit} style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="sc-..."
              style={styles.apiKeyInlineInput}
            />
            <button type="submit" disabled={!apiKeyInput.trim()} style={styles.apiKeySaveBtn}>Save</button>
          </form>
        </div>
      )}

      {/* Chat Messages */}
      <div
        ref={chatAreaRef}
        style={styles.chatArea}
        onScroll={() => {
          const near = isNearBottom();
          userIsNearBottomRef.current = near;
          if (near) setShowScrollBtn(false);
          else if (isLoading) setShowScrollBtn(true);
        }}
      >
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <Bot size={40} style={{ color: 'rgba(255,255,255,0.15)', marginBottom: '12px' }} />
            <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: '15px', margin: 0 }}>
              Ask a question to see semantic caching in action
            </p>
            <p style={{ color: 'rgba(255,255,255,0.2)', fontSize: '13px', margin: '6px 0 0' }}>
              Responses are streamed in real-time with markdown formatting
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} style={{
            ...styles.messageBubbleWrap,
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            {msg.role === 'assistant' && (
              <div style={styles.avatarBot}><Bot size={16} /></div>
            )}

            <div style={{
              ...(msg.role === 'user' ? styles.userBubble : styles.assistantBubble),
              maxWidth: msg.role === 'user' ? '70%' : '85%',
            }}>
              {msg.role === 'user' ? (
                <p style={{ margin: 0, lineHeight: '1.5' }}>{msg.content}</p>
              ) : (
                <>
                  {msg.content ? (
                    <MarkdownRenderer content={msg.content} />
                  ) : msg.isStreaming ? (
                    <div style={styles.typingIndicator}>
                      <span style={styles.dot} /><span style={{ ...styles.dot, animationDelay: '0.15s' }} /><span style={{ ...styles.dot, animationDelay: '0.3s' }} />
                    </div>
                  ) : null}

                  {msg.isStreaming && msg.content && (
                    <span style={styles.cursor}>▊</span>
                  )}

                  {/* Meta bar */}
                  {!msg.isStreaming && msg.meta && (
                    <div style={styles.metaBar}>
                      <span style={{
                        ...styles.metaChip,
                        background: getBadgeColor(msg.meta.hit) + '22',
                        color: getBadgeColor(msg.meta.hit),
                        border: `1px solid ${getBadgeColor(msg.meta.hit)}44`,
                      }}>
                        {getBadgeIcon(msg.meta.hit)}
                        {msg.meta.hit.toUpperCase()}
                      </span>
                      <span style={styles.metaChip}>
                        <Gauge size={12} />
                        {msg.meta.latency_ms.toFixed(0)}ms
                      </span>
                      {msg.meta.similarity > 0 && (
                        <span style={styles.metaChip}>
                          {(msg.meta.similarity * 100).toFixed(1)}% match
                        </span>
                      )}
                      {msg.usage && (
                        <span style={styles.metaChip}>
                          {msg.usage.total_tokens} tokens
                        </span>
                      )}
                      <button
                        onClick={() => copyContent(msg.content)}
                        style={styles.copyInline}
                        title="Copy response"
                      >
                        <Copy size={12} /> Copy
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>

            {msg.role === 'user' && (
              <div style={styles.avatarUser}><User size={16} /></div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to bottom button */}
      {showScrollBtn && (
        <button
          onClick={() => scrollToBottom(true)}
          style={{
            position: 'absolute',
            bottom: 90,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(59,130,246,0.85)',
            color: '#fff',
            border: 'none',
            borderRadius: '20px',
            padding: '6px 16px',
            fontSize: '13px',
            cursor: 'pointer',
            zIndex: 10,
            backdropFilter: 'blur(8px)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            transition: 'opacity 0.2s',
          }}
        >
          ↓ Scroll to bottom
        </button>
      )}

      {/* Input Bar */}
      <div style={styles.inputBar}>
        <div style={styles.inputRow}>
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            style={styles.settingsToggle}
            title="Model settings"
          >
            ⚙
          </button>

          {history.length > 0 && (
            <button
              type="button"
              onClick={() => setShowHistory(!showHistory)}
              style={styles.historyBtn}
              title="Query history"
            >
              <Clock size={14} /> {history.length}
            </button>
          )}

          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={autoResizeTextarea}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
            style={styles.chatInput}
            rows={1}
            disabled={isLoading || !hasApiKey()}
          />

          <button
            onClick={handleSubmit as any}
            disabled={isLoading || !prompt.trim() || !hasApiKey()}
            style={{
              ...styles.sendButton,
              opacity: isLoading || !prompt.trim() ? 0.4 : 1,
            }}
          >
            <Send size={18} />
          </button>
        </div>

        {/* Settings row */}
        {showSettings && (
          <div style={styles.settingsRow}>
            <div style={styles.settingItem}>
              <label style={styles.settingLabel}>Model</label>
              <select value={model} onChange={(e) => setModel(e.target.value)} style={styles.settingSelect}>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              </select>
            </div>
            <div style={styles.settingItem}>
              <label style={styles.settingLabel}>Temperature: {temperature}</label>
              <input
                type="range" min="0" max="1" step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                style={{ width: '120px', cursor: 'pointer' }}
              />
            </div>
          </div>
        )}

        {error && (
          <div style={styles.errorBar}>
            {error}
            {(error.includes('plan') || error.includes('limit reached')) && (
              <Link to="/settings" style={{ color: '#fbbf24', marginLeft: '8px', fontWeight: 600 }}>
                Upgrade Plan →
              </Link>
            )}
          </div>
        )}
      </div>

      {/* History Panel */}
      {showHistory && history.length > 0 && (
        <div style={styles.historyOverlay}>
          <div style={styles.historyPanel}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '15px', color: '#fff', fontWeight: 600, margin: 0 }}>
                History ({history.length})
              </h3>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={clearHistory} style={styles.clearBtn}>
                  <Trash2 size={13} /> Clear
                </button>
                <button onClick={() => setShowHistory(false)} style={styles.clearBtn}>
                  ✕
                </button>
              </div>
            </div>
            <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
              {history.map((entry) => (
                <button key={entry.id} onClick={() => loadFromHistory(entry)} style={styles.historyItem}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '13px', color: '#fff', flex: 1, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {entry.prompt}
                    </span>
                    <span style={{
                      fontSize: '11px', padding: '2px 8px', borderRadius: '4px', fontWeight: 600,
                      background: getBadgeColor(entry.response.meta.hit) + '22',
                      color: getBadgeColor(entry.response.meta.hit),
                    }}>
                      {entry.response.meta.hit.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', textAlign: 'left', marginTop: '4px' }}>
                    {new Date(entry.timestamp).toLocaleString()} · {entry.response.meta.latency_ms.toFixed(0)}ms
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    minHeight: '500px',
    maxHeight: 'calc(100vh - 180px)',
    width: '100%',
    position: 'relative',
  },

  // API Key
  apiKeyBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    background: 'rgba(59,130,246,0.1)',
    border: '1px solid rgba(59,130,246,0.2)',
    borderRadius: '10px',
    marginBottom: '12px',
    flexWrap: 'wrap',
  },
  apiKeyInlineInput: {
    padding: '6px 10px',
    fontSize: '13px',
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '6px',
    color: '#fff',
    fontFamily: 'monospace',
    width: '200px',
  },
  apiKeySaveBtn: {
    padding: '6px 14px',
    fontSize: '13px',
    fontWeight: 600,
    background: '#3b82f6',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },

  // Chat area
  chatArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px 0',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    padding: '60px 20px',
  },

  // Messages
  messageBubbleWrap: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    padding: '4px 0',
  },
  avatarBot: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    background: 'rgba(59,130,246,0.15)',
    border: '1px solid rgba(59,130,246,0.3)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#60a5fa',
    flexShrink: 0,
    marginTop: '4px',
  },
  avatarUser: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    background: 'rgba(139,92,246,0.15)',
    border: '1px solid rgba(139,92,246,0.3)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#a78bfa',
    flexShrink: 0,
    marginTop: '4px',
  },
  userBubble: {
    background: 'rgba(139,92,246,0.12)',
    border: '1px solid rgba(139,92,246,0.2)',
    borderRadius: '16px 16px 4px 16px',
    padding: '12px 16px',
    color: 'rgba(255,255,255,0.9)',
    fontSize: '14px',
  },
  assistantBubble: {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '16px 16px 16px 4px',
    padding: '14px 18px',
    color: 'rgba(255,255,255,0.88)',
    fontSize: '14px',
    lineHeight: '1.6',
  },

  // Typing indicator
  typingIndicator: {
    display: 'flex',
    gap: '4px',
    padding: '4px 0',
  },
  dot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#60a5fa',
    animation: 'bounce 1.4s infinite ease-in-out both',
  },
  cursor: {
    animation: 'blink 1s step-end infinite',
    color: '#60a5fa',
    fontSize: '14px',
  },

  // Meta bar
  metaBar: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    marginTop: '12px',
    paddingTop: '10px',
    borderTop: '1px solid rgba(255,255,255,0.06)',
    alignItems: 'center',
  },
  metaChip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '3px 8px',
    borderRadius: '5px',
    fontSize: '11px',
    fontWeight: 500,
    background: 'rgba(255,255,255,0.06)',
    color: 'rgba(255,255,255,0.5)',
    border: '1px solid rgba(255,255,255,0.08)',
  },
  copyInline: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '3px',
    padding: '3px 8px',
    borderRadius: '5px',
    fontSize: '11px',
    background: 'none',
    border: '1px solid rgba(255,255,255,0.08)',
    color: 'rgba(255,255,255,0.4)',
    cursor: 'pointer',
    marginLeft: 'auto',
  },

  // Input bar
  inputBar: {
    padding: '12px 0 0',
    borderTop: '1px solid rgba(255,255,255,0.06)',
  },
  inputRow: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '8px',
  },
  chatInput: {
    flex: 1,
    padding: '10px 14px',
    fontSize: '14px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '12px',
    color: '#fff',
    fontFamily: 'inherit',
    resize: 'none',
    lineHeight: '1.5',
    maxHeight: '150px',
    outline: 'none',
  },
  sendButton: {
    width: '42px',
    height: '42px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    border: 'none',
    color: '#fff',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    transition: 'opacity 0.15s',
  },
  settingsToggle: {
    width: '42px',
    height: '42px',
    borderRadius: '12px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: 'rgba(255,255,255,0.5)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    fontSize: '18px',
  },
  historyBtn: {
    height: '42px',
    padding: '0 12px',
    borderRadius: '12px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    color: 'rgba(255,255,255,0.5)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    fontSize: '13px',
    flexShrink: 0,
    fontFamily: 'inherit',
  },

  // Settings row
  settingsRow: {
    display: 'flex',
    gap: '16px',
    padding: '10px 0 0',
    flexWrap: 'wrap',
  },
  settingItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  settingLabel: {
    fontSize: '12px',
    color: 'rgba(255,255,255,0.45)',
    whiteSpace: 'nowrap',
  },
  settingSelect: {
    padding: '4px 8px',
    fontSize: '12px',
    background: 'rgba(0,0,0,0.3)',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
  },

  // Error
  errorBar: {
    marginTop: '8px',
    padding: '8px 12px',
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.25)',
    borderRadius: '8px',
    color: '#fca5a5',
    fontSize: '13px',
  },

  // History overlay
  historyOverlay: {
    position: 'absolute',
    bottom: '70px',
    left: 0,
    right: 0,
    zIndex: 10,
  },
  historyPanel: {
    background: 'rgba(15,15,20,0.97)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '12px',
    padding: '16px',
    backdropFilter: 'blur(20px)',
    boxShadow: '0 -8px 30px rgba(0,0,0,0.4)',
  },
  historyItem: {
    display: 'block',
    width: '100%',
    padding: '10px 12px',
    marginBottom: '6px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '8px',
    cursor: 'pointer',
    textDecoration: 'none',
    fontFamily: 'inherit',
    transition: 'background 0.15s',
  },
  clearBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 10px',
    fontSize: '12px',
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '6px',
    color: 'rgba(255,255,255,0.5)',
    cursor: 'pointer',
    fontFamily: 'inherit',
  },
};
