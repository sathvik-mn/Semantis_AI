import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { generateApiKey, setApiKey, hasApiKey, getApiKey, getSettings, updateSettings } from '../api/semanticAPI';
import { Key, Copy, Check, AlertCircle, Save, Loader2, RefreshCw } from 'lucide-react';
import { CacheWarmup } from './CacheWarmup';

export function SettingsPanel() {
  const [threshold, setThreshold] = useState(0.75);
  const [ttl, setTtl] = useState(7);
  const [apiKey, setApiKeyState] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [dirty, setDirty] = useState(false);
  const [serverThreshold, setServerThreshold] = useState(0.75);
  const [serverTtl, setServerTtl] = useState(7);
  const [entries, setEntries] = useState(0);
  const { user } = useAuth();

  const loadSettings = useCallback(async () => {
    if (!hasApiKey()) {
      setLoadingSettings(false);
      return;
    }
    try {
      const s = await getSettings();
      setThreshold(s.sim_threshold);
      setServerThreshold(s.sim_threshold);
      setTtl(s.ttl_days);
      setServerTtl(s.ttl_days);
      setEntries(s.entries);
    } catch {
      // backend might not be up yet
    } finally {
      setLoadingSettings(false);
    }
  }, []);

  useEffect(() => {
    const existingKey = getApiKey();
    if (existingKey) setApiKeyState(existingKey);
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    setDirty(threshold !== serverThreshold || ttl !== serverTtl);
    setSaveSuccess(false);
  }, [threshold, ttl, serverThreshold, serverTtl]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const result = await updateSettings({ sim_threshold: threshold, ttl_days: ttl });
      const updated = result.settings;
      if (updated.sim_threshold !== undefined) {
        setServerThreshold(updated.sim_threshold);
        setThreshold(updated.sim_threshold);
      }
      if (updated.ttl_days !== undefined) {
        setServerTtl(updated.ttl_days);
        setTtl(updated.ttl_days);
      }
      setDirty(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateApiKey = async () => {
    setGenerating(true);
    setError(null);
    try {
      const result = await generateApiKey({ plan: 'free' });
      setApiKeyState(result.api_key);
      setApiKey(result.api_key);
      setCopied(false);
      loadSettings();
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
      {/* API Key Management */}
      <div style={styles.apiKeyContainer}>
        <div style={styles.apiKeyHeader}>
          <Key size={20} style={{ color: '#60a5fa' }} />
          <h3 style={styles.sectionTitle}>API Key Management</h3>
        </div>
        <p style={styles.description}>
          Generate an API key to use the playground and make API calls.
        </p>
        {apiKey ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={styles.apiKeyValue}>
              <code style={styles.apiKeyCode}>{apiKey}</code>
              <button onClick={handleCopyApiKey} style={styles.iconButton} title="Copy API key">
                {copied ? <Check size={16} /> : <Copy size={16} />}
              </button>
            </div>
            <p style={styles.warning}>
              <AlertCircle size={14} style={{ color: '#f59e0b', flexShrink: 0 }} />
              Save this key securely — it won't be shown again after you refresh.
            </p>
            <button onClick={handleGenerateApiKey} disabled={generating} style={styles.secondaryButton}>
              {generating ? 'Generating...' : 'Generate New Key'}
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button onClick={handleGenerateApiKey} disabled={generating} style={styles.primaryButton}>
              {generating ? 'Generating...' : 'Generate API Key'}
            </button>
          </div>
        )}
      </div>

      {/* Cache Settings */}
      <div style={styles.settingsSection}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={styles.sectionTitle}>Cache Settings</h3>
          <button
            onClick={loadSettings}
            style={styles.iconButton}
            title="Refresh settings from server"
          >
            <RefreshCw size={16} />
          </button>
        </div>
        <p style={styles.description}>
          Adjust similarity threshold and TTL for your semantic cache. Changes apply immediately after saving.
        </p>

        {loadingSettings ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'rgba(255,255,255,0.5)' }}>
            <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} />
            <p>Loading settings...</p>
          </div>
        ) : (
          <>
            {/* Similarity Threshold */}
            <div style={styles.setting}>
              <div style={styles.settingHeader}>
                <label style={styles.label}>Similarity Threshold</label>
                <span style={styles.valueDisplay}>{threshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.99"
                step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                style={styles.slider}
              />
              <div style={styles.sliderLabels}>
                <span>0.50 (lenient)</span>
                <span>0.99 (strict)</span>
              </div>
              <p style={styles.hint}>
                Minimum cosine similarity for a semantic cache hit. Lower = more matches but less precise. Higher = fewer matches but higher quality.
              </p>
            </div>

            {/* TTL */}
            <div style={styles.setting}>
              <div style={styles.settingHeader}>
                <label style={styles.label}>Default TTL (days)</label>
                <span style={styles.valueDisplay}>{ttl}</span>
              </div>
              <input
                type="number"
                min="1"
                max="90"
                value={ttl}
                onChange={(e) => setTtl(parseInt(e.target.value) || 1)}
                style={styles.numberInput}
              />
              <p style={styles.hint}>How long cache entries are retained before expiring.</p>
            </div>

            {/* Save button */}
            <button
              onClick={handleSave}
              disabled={saving || !dirty || !hasApiKey()}
              style={{
                ...styles.saveButton,
                opacity: (saving || !dirty || !hasApiKey()) ? 0.5 : 1,
                cursor: (saving || !dirty || !hasApiKey()) ? 'default' : 'pointer',
              }}
            >
              {saving ? (
                <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Saving...</>
              ) : saveSuccess ? (
                <><Check size={16} /> Saved!</>
              ) : (
                <><Save size={16} /> Save Settings</>
              )}
            </button>

            {saveSuccess && (
              <div style={styles.successMessage}>
                <Check size={16} /> Settings saved successfully.
              </div>
            )}
          </>
        )}
      </div>

      {/* Cache Warm-Up */}
      <CacheWarmup />

      {/* Summary */}
      <div style={styles.infoBox}>
        <h4 style={styles.infoTitle}>Current Settings Summary</h4>
        <ul style={styles.list}>
          <li>Threshold: <strong>{serverThreshold.toFixed(2)}</strong> — controls semantic matching strictness</li>
          <li>TTL: <strong>{serverTtl}</strong> days — cache entry lifetime</li>
          <li>Cache entries: <strong>{entries}</strong></li>
          <li>Strategy: Exact match + FAISS cosine similarity</li>
        </ul>
      </div>

      {error && (
        <div style={styles.errorMessage}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
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
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  sectionTitle: {
    fontSize: '20px',
    color: '#fff',
    margin: 0,
    fontWeight: '600',
  },
  description: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: '16px',
    lineHeight: '1.5',
    marginTop: '4px',
  },
  apiKeyContainer: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '12px',
    padding: '24px',
  },
  apiKeyHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '8px',
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
    wordBreak: 'break-all' as const,
  },
  warning: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: 0,
  },
  settingsSection: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '24px',
  },
  setting: {
    marginBottom: '24px',
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
  valueDisplay: {
    fontSize: '16px',
    color: '#60a5fa',
    fontWeight: '700',
    fontFamily: 'monospace',
    background: 'rgba(96, 165, 250, 0.1)',
    padding: '4px 10px',
    borderRadius: '6px',
  },
  slider: {
    width: '100%',
    cursor: 'pointer',
    marginBottom: '4px',
    accentColor: '#3b82f6',
  },
  sliderLabels: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '11px',
    color: 'rgba(255, 255, 255, 0.35)',
    marginBottom: '8px',
  },
  numberInput: {
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
    color: 'rgba(255, 255, 255, 0.45)',
    lineHeight: '1.4',
    margin: 0,
  },
  saveButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    width: '100%',
    padding: '14px 24px',
    fontSize: '15px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    transition: 'all 0.2s',
    marginTop: '4px',
  },
  successMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px',
    background: 'rgba(34, 197, 94, 0.15)',
    border: '1px solid rgba(34, 197, 94, 0.3)',
    borderRadius: '8px',
    color: '#86efac',
    fontSize: '14px',
    marginTop: '8px',
  },
  infoBox: {
    padding: '16px',
    background: 'rgba(59, 130, 246, 0.08)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    borderRadius: '8px',
  },
  infoTitle: {
    fontSize: '15px',
    color: '#60a5fa',
    marginBottom: '12px',
    fontWeight: '600',
    marginTop: 0,
  },
  list: {
    margin: 0,
    paddingLeft: '20px',
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '2',
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
  iconButton: {
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
  primaryButton: {
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
  secondaryButton: {
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
};
