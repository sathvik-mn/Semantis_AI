import { useState } from 'react';

export function SettingsPanel() {
  const [threshold, setThreshold] = useState(0.83);
  const [ttl, setTtl] = useState(7);

  return (
    <div style={styles.container}>
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
};
