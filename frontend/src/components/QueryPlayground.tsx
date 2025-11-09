import { useState } from 'react';
import { useSemanticCache } from '../hooks/useSemanticCache';
import { ChatResponse } from '../api/semanticAPI';

interface QueryPlaygroundProps {
  onQueryComplete?: () => void;
}

export function QueryPlayground({ onQueryComplete }: QueryPlaygroundProps) {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.2);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const { sendQuery, isLoading, error } = useSemanticCache();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prompt.trim()) return;

    try {
      const result = await sendQuery({
        model,
        messages: [{ role: 'user', content: prompt }],
        temperature,
      });

      setResponse(result);
      if (onQueryComplete) onQueryComplete();
    } catch (err) {
      console.error('Query failed:', err);
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

        <button type="submit" disabled={isLoading || !prompt.trim()} style={styles.button}>
          {isLoading ? 'Processing...' : 'Run Query'}
        </button>

        {error && <div style={styles.error}>{error}</div>}
      </form>

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
};
