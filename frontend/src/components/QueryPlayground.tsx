import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSemanticCache } from '../hooks/useSemanticCache';
import { ChatResponse } from '../api/semanticAPI';
import { setApiKey, hasApiKey, getUserOpenAIKeyStatus } from '../api/semanticAPI';
import { Key, ExternalLink, AlertCircle } from 'lucide-react';

interface QueryPlaygroundProps {
  onQueryComplete?: () => void;
}

export function QueryPlayground({ onQueryComplete }: QueryPlaygroundProps) {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.2);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKeyInput, setShowApiKeyInput] = useState(!hasApiKey());
  const [openaiKeySet, setOpenaiKeySet] = useState<boolean | null>(null);
  const { sendQuery, isLoading, error } = useSemanticCache();

  useEffect(() => {
    // Check if API key exists in localStorage
    const storedKey = localStorage.getItem('semantic_api_key');
    if (storedKey) {
      setShowApiKeyInput(false);
    }

    // Check OpenAI key status
    const checkOpenAIKey = async () => {
      try {
        const status = await getUserOpenAIKeyStatus();
        setOpenaiKeySet(status.key_set);
      } catch (err) {
        console.error('Failed to check OpenAI key status:', err);
        setOpenaiKeySet(false);
      }
    };
    checkOpenAIKey();
  }, []);

  const handleApiKeySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (apiKeyInput.trim()) {
      setApiKey(apiKeyInput.trim());
      setShowApiKeyInput(false);
      setApiKeyInput('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prompt.trim()) return;

    // Check OpenAI key before submitting
    if (openaiKeySet === false) {
      alert('Please add your OpenAI API key in Account Settings first.');
      return;
    }

    try {
      const result = await sendQuery({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature,
      });

      setResponse(result);
      if (onQueryComplete) onQueryComplete();
    } catch (err: any) {
      console.error('Query failed:', err);
      // Show user-friendly error message
      if (err.message && err.message.includes('OpenAI API key')) {
        alert(err.message);
      }
    }
  };

  const getBadgeColor = (hit: string) => {
    switch (hit) {
      case 'exact':
        return '#10b981';
      case 'semantic':
        return '#3b82f6';
      case 'miss':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  return (
    <div style={styles.container}>
      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your query here..."
            style={styles.textarea}
            rows={4}
          />
        </div>

        <div style={styles.row}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Model</label>
            <select value={model} onChange={(e) => setModel(e.target.value)} style={styles.select}>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4">gpt-4</option>
              <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
            </select>
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Temperature: {temperature}</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              style={styles.slider}
            />
          </div>
        </div>

        <button type="submit" disabled={isLoading || !prompt.trim() || !hasApiKey() || openaiKeySet === false} style={styles.button}>
          {isLoading ? 'Processing...' : 'Run Query'}
        </button>

        {error && <div style={styles.error}>{error}</div>}
      </form>

      {showApiKeyInput && (
        <div style={styles.apiKeySection}>
          <div style={styles.apiKeyHeader}>
            <Key size={18} style={styles.apiKeyIcon} />
            <h3 style={styles.apiKeyTitle}>API Key Required</h3>
          </div>
          <p style={styles.apiKeyDescription}>
            You need an API key to use the playground. Generate one in Settings or paste an existing key below.
          </p>
          <form onSubmit={handleApiKeySubmit} style={styles.apiKeyForm}>
            <input
              type="text"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="Paste your API key here (e.g., sc-tenant-xxxxx)"
              style={styles.apiKeyInput}
            />
            <button type="submit" disabled={!apiKeyInput.trim()} style={styles.apiKeyButton}>
              Save API Key
            </button>
          </form>
          <div style={styles.apiKeyHelp}>
            <p style={styles.apiKeyHelpText}>
              Don't have an API key?{' '}
              <Link to="/settings" style={styles.apiKeyLink}>
                Go to Settings to generate one <ExternalLink size={14} style={styles.linkIcon} />
              </Link>
            </p>
          </div>
        </div>
      )}

      {response && (
        <div style={styles.responseContainer}>
          <div style={styles.metaPanel}>
            <h3 style={styles.metaTitle}>Cache Metadata</h3>
            <div style={styles.metaGrid}>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Hit Type:</span>
                <span
                  style={{
                    ...styles.badge,
                    backgroundColor: getBadgeColor(response.meta.hit),
                  }}
                >
                  {response.meta.hit.toUpperCase()}
                </span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Similarity:</span>
                <span style={styles.metaValue}>
                  {(response.meta.similarity * 100).toFixed(1)}%
                </span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Latency:</span>
                <span style={styles.metaValue}>{response.meta.latency_ms.toFixed(0)}ms</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Strategy:</span>
                <span style={styles.metaValue}>{response.meta.strategy}</span>
              </div>
            </div>
          </div>

          <div style={styles.responsePanel}>
            <h3 style={styles.responseTitle}>Response</h3>
            <div style={styles.responseText}>
              {response.choices[0]?.message.content}
            </div>
            <div style={styles.usage}>
              <span>Tokens: {response.usage.total_tokens}</span>
              <span>
                (Prompt: {response.usage.prompt_tokens}, Completion:{' '}
                {response.usage.completion_tokens})
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
  },
  form: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '20px',
    backdropFilter: 'blur(10px)',
  },
  inputGroup: {
    marginBottom: '20px',
    flex: 1,
  },
  label: {
    display: 'block',
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: '8px',
    fontWeight: '500',
  },
  textarea: {
    width: '100%',
    padding: '12px',
    fontSize: '14px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontFamily: 'inherit',
    resize: 'vertical',
  },
  row: {
    display: 'flex',
    gap: '20px',
    marginBottom: '20px',
  },
  select: {
    width: '100%',
    padding: '12px',
    fontSize: '14px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
  },
  slider: {
    width: '100%',
    cursor: 'pointer',
  },
  button: {
    width: '100%',
    padding: '14px',
    fontSize: '16px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.2s, opacity 0.2s',
  },
  error: {
    marginTop: '12px',
    padding: '12px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    color: '#fca5a5',
    fontSize: '14px',
  },
  responseContainer: {
    display: 'grid',
    gap: '20px',
  },
  metaPanel: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    backdropFilter: 'blur(10px)',
  },
  metaTitle: {
    fontSize: '18px',
    color: '#fff',
    marginBottom: '16px',
    fontWeight: '600',
  },
  metaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
  },
  metaItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  metaLabel: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  metaValue: {
    fontSize: '16px',
    color: '#fff',
    fontWeight: '600',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: '600',
    color: '#fff',
  },
  responsePanel: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    backdropFilter: 'blur(10px)',
  },
  responseTitle: {
    fontSize: '18px',
    color: '#fff',
    marginBottom: '16px',
    fontWeight: '600',
  },
  responseText: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.9)',
    lineHeight: '1.6',
    marginBottom: '16px',
    whiteSpace: 'pre-wrap',
  },
  usage: {
    display: 'flex',
    gap: '12px',
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  apiKeySection: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '12px',
    padding: '24px',
    marginTop: '20px',
    backdropFilter: 'blur(10px)',
  },
  apiKeyHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '12px',
  },
  apiKeyIcon: {
    color: '#60a5fa',
  },
  apiKeyTitle: {
    fontSize: '18px',
    color: '#fff',
    fontWeight: '600',
    margin: 0,
  },
  apiKeyDescription: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '16px',
    lineHeight: '1.5',
  },
  apiKeyForm: {
    display: 'flex',
    gap: '12px',
    marginBottom: '12px',
  },
  apiKeyInput: {
    flex: 1,
    padding: '12px',
    fontSize: '14px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontFamily: 'monospace',
  },
  apiKeyButton: {
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'opacity 0.2s',
  },
  apiKeyHelp: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
  },
  apiKeyHelpText: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: 0,
  },
  apiKeyLink: {
    color: '#60a5fa',
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    fontWeight: '500',
  },
  linkIcon: {
    display: 'inline-block',
  },
};
