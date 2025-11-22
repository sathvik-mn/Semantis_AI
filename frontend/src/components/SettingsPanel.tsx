import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { generateApiKey } from '../api/semanticAPI';
import { setApiKey, hasApiKey, getApiKey } from '../api/semanticAPI';
import { Key, Copy, Check, AlertCircle } from 'lucide-react';

export function SettingsPanel() {
  const [threshold, setThreshold] = useState(0.83);
  const [ttl, setTtl] = useState(7);
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    // Load existing API key from localStorage
    const existingKey = getApiKey();
    if (existingKey) {
      setApiKeyState(existingKey);
    }
  }, []);

  const handleGenerateApiKey = async () => {
    setGenerating(true);
    setError(null);
    try {
      const result = await generateApiKey({
        email: user?.email,
        name: user?.name,
        plan: 'free',
      });
      setApiKeyState(result.api_key);
      setApiKey(result.api_key);
      setCopied(false);
    } catch (err: any) {
      setError(err.message || 'Failed to generate API key');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopyApiKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={styles.container}>
      {/* API Key Management Section */}
      <div style={styles.apiKeyContainer}>
        <div style={styles.apiKeyHeader}>
          <Key size={20} style={styles.apiKeyIcon} />
          <h3 style={styles.apiKeyTitle}>API Key Management</h3>
        </div>
        <p style={styles.apiKeyDescription}>
          Generate an API key to use the playground and make API calls. Keep your API key secure and don't share it publicly.
        </p>

        {apiKey ? (
          <div style={styles.apiKeyDisplay}>
            <div style={styles.apiKeyValue}>
              <code style={styles.apiKeyCode}>{apiKey}</code>
              <button
                onClick={handleCopyApiKey}
                style={styles.copyButton}
                title="Copy API key"
              >
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
            </div>
            <p style={styles.apiKeyWarning}>
              <AlertCircle size={14} style={styles.warningIcon} />
              Save this key securely - it won't be shown again after you refresh the page.
            </p>
            <button
              onClick={handleGenerateApiKey}
              disabled={generating}
              style={styles.regenerateButton}
            >
              {generating ? 'Generating...' : 'Generate New Key'}
            </button>
          </div>
        ) : (
          <div style={styles.apiKeyGenerate}>
            <button
              onClick={handleGenerateApiKey}
              disabled={generating}
              style={styles.generateButton}
            >
              {generating ? 'Generating...' : 'Generate API Key'}
            </button>
            {error && (
              <div style={styles.errorMessage}>
                <AlertCircle size={16} />
                {error}
              </div>
            )}
          </div>
        )}
      </div>

      <h3 style={styles.title}>Cache Settings</h3>
      <p style={styles.description}>
        Adjust cache behavior settings. Note: Some settings may require backend support.
      </p>

      <div style={styles.setting}>
        <div style={styles.settingHeader}>
          <label style={styles.label}>Similarity Threshold</label>
          <span style={styles.value}>{threshold.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="1"
          step="0.01"
          value={threshold}
          onChange={(e) => setThreshold(parseFloat(e.target.value))}
          style={styles.slider}
        />
        <p style={styles.hint}>
          Minimum similarity score required for semantic cache hits. Higher values require closer
          matches.
        </p>
      </div>

      <div style={styles.setting}>
        <div style={styles.settingHeader}>
          <label style={styles.label}>Default TTL (days)</label>
          <span style={styles.value}>{ttl}</span>
        </div>
        <input
          type="number"
          min="1"
          max="90"
          value={ttl}
          onChange={(e) => setTtl(parseInt(e.target.value))}
          style={styles.input}
        />
        <p style={styles.hint}>How long cache entries should be retained before expiring.</p>
      </div>

      <div style={styles.infoBox}>
        <h4 style={styles.infoTitle}>Current Settings Summary</h4>
        <ul style={styles.list}>
          <li>Threshold: {threshold.toFixed(2)} - Controls semantic matching strictness</li>
          <li>TTL: {ttl} days - Cache entry lifetime</li>
          <li>Strategy: Hybrid (exact + semantic)</li>
        </ul>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    backdropFilter: 'blur(10px)',
    maxWidth: '600px',
  },
  title: {
    fontSize: '20px',
    color: '#fff',
    marginBottom: '8px',
    fontWeight: '600',
  },
  description: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: '24px',
    lineHeight: '1.5',
  },
  setting: {
    marginBottom: '28px',
  },
  settingHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  label: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '500',
  },
  value: {
    fontSize: '15px',
    color: '#60a5fa',
    fontWeight: '600',
  },
  slider: {
    width: '100%',
    cursor: 'pointer',
    marginBottom: '8px',
  },
  input: {
    width: '100%',
    padding: '12px',
    fontSize: '14px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    marginBottom: '8px',
  },
  hint: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.5)',
    lineHeight: '1.4',
  },
  infoBox: {
    marginTop: '28px',
    padding: '16px',
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: '8px',
  },
  infoTitle: {
    fontSize: '15px',
    color: '#60a5fa',
    marginBottom: '12px',
    fontWeight: '600',
  },
  list: {
    margin: 0,
    paddingLeft: '20px',
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.8',
  },
  apiKeyContainer: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '32px',
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
    fontSize: '20px',
    color: '#fff',
    margin: 0,
    fontWeight: '600',
  },
  apiKeyDescription: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '20px',
    lineHeight: '1.5',
  },
  apiKeyDisplay: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  apiKeyValue: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
  },
  apiKeyCode: {
    flex: 1,
    fontSize: '13px',
    fontFamily: 'monospace',
    color: '#60a5fa',
    wordBreak: 'break-all',
  },
  copyButton: {
    padding: '8px',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 0.2s',
  },
  apiKeyWarning: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: 0,
  },
  warningIcon: {
    color: '#f59e0b',
  },
  regenerateButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    background: 'rgba(255, 255, 255, 0.1)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
  apiKeyGenerate: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  generateButton: {
    padding: '12px 24px',
    fontSize: '15px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'opacity 0.2s',
  },
  errorMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    color: '#fca5a5',
    fontSize: '14px',
  },
};
