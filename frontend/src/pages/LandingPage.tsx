import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Prism } from '../components/Prism';
import * as api from '../api/semanticAPI';

export function LandingPage() {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!apiKey.trim()) {
      setError('Please enter your API key');
      return;
    }

    if (!apiKey.startsWith('sc-')) {
      setError('API key should start with "sc-"');
      return;
    }

    api.setApiKey(apiKey);
    navigate('/playground');
  };

  return (
    <div style={styles.container}>
      <Prism />

      <div style={styles.content}>
        <div style={styles.hero}>
          <h1 style={styles.title}>
            Semantic Caching
            <br />
            for LLM APIs
          </h1>
          <p style={styles.subtitle}>
            Reduce costs by up to 70% and accelerate response times with intelligent semantic
            caching
          </p>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Get Started</h2>
          <p style={styles.cardSubtitle}>
            Enter your API key to access the dashboard and start saving on LLM costs
          </p>

          <form onSubmit={handleSubmit} style={styles.form}>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sc-your-api-key-here"
              style={styles.input}
            />
            {error && <div style={styles.error}>{error}</div>}
            <button type="submit" style={styles.button}>
              Access Dashboard
            </button>
          </form>

          <div style={styles.note}>
            Your API key is stored locally and never transmitted except for authenticated requests
            to the backend.
          </div>
        </div>

        <div style={styles.features}>
          <div style={styles.feature}>
            <div style={styles.featureIcon}>⚡</div>
            <h3 style={styles.featureTitle}>Lightning Fast</h3>
            <p style={styles.featureText}>
              Cache hits return in milliseconds, dramatically reducing latency
            </p>
          </div>
          <div style={styles.feature}>
            <div style={styles.featureIcon}>💰</div>
            <h3 style={styles.featureTitle}>Cost Savings</h3>
            <p style={styles.featureText}>
              Save 50-70% on token costs with intelligent semantic matching
            </p>
          </div>
          <div style={styles.feature}>
            <div style={styles.featureIcon}>🎯</div>
            <h3 style={styles.featureTitle}>High Accuracy</h3>
            <p style={styles.featureText}>
              Hybrid exact + semantic matching ensures relevant cache hits
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px',
    position: 'relative',
  },
  content: {
    maxWidth: '600px',
    width: '100%',
    position: 'relative',
    zIndex: 1,
  },
  hero: {
    textAlign: 'center',
    marginBottom: '48px',
  },
  title: {
    fontSize: '48px',
    fontWeight: '800',
    color: '#fff',
    marginBottom: '20px',
    lineHeight: '1.2',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: '20px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.5',
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
    backdropFilter: 'blur(20px)',
    marginBottom: '48px',
  },
  cardTitle: {
    fontSize: '24px',
    color: '#fff',
    marginBottom: '8px',
    fontWeight: '600',
  },
  cardSubtitle: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: '24px',
    lineHeight: '1.5',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    fontSize: '15px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#fff',
    fontFamily: 'monospace',
  },
  button: {
    width: '100%',
    padding: '16px',
    fontSize: '16px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  error: {
    padding: '12px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    color: '#fca5a5',
    fontSize: '14px',
  },
  note: {
    marginTop: '16px',
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
    lineHeight: '1.5',
  },
  features: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
    gap: '20px',
  },
  feature: {
    textAlign: 'center',
  },
  featureIcon: {
    fontSize: '40px',
    marginBottom: '12px',
  },
  featureTitle: {
    fontSize: '16px',
    color: '#fff',
    marginBottom: '8px',
    fontWeight: '600',
  },
  featureText: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: '1.5',
  },
};
