import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Prism } from '../components/Prism';
import * as api from '../api/semanticAPI';
import { useAuth } from '../contexts/AuthContext';

export function LandingPage() {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState('');
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

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

  const handleGenerateKey = async () => {
    setIsGenerating(true);
    setGenerateError('');
    setGeneratedKey(null);

    try {
      const response = await api.generateApiKey({ length: 32 });
      setGeneratedKey(response.api_key);
      setApiKey(response.api_key); // Auto-fill the input field
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Failed to generate API key');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyKey = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={styles.container}>
      <Prism />

      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <div style={styles.logo}>
            <span style={styles.logoText}>Semantis AI</span>
          </div>
          <div style={styles.navLinks}>
            <a href="#features" style={styles.navLink}>Features</a>
            <a href="#pricing" style={styles.navLink}>Pricing</a>
            <a href="#docs" style={styles.navLink}>Docs</a>
          </div>
          <div style={styles.authButtons}>
            {isAuthenticated ? (
              <>
                <span style={styles.userInfo}>{user?.email}</span>
                <Link to="/playground" style={styles.dashboardButton}>Go to Dashboard</Link>
              </>
            ) : (
              <>
                <Link to="/login" style={styles.loginButton}>Sign In</Link>
                <Link to="/signup" style={styles.signupButton}>Get Started</Link>
              </>
            )}
          </div>
        </div>
      </nav>

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
            Generate a new API key or enter your existing one to access the dashboard
          </p>

          {/* Generate API Key Section */}
          <div style={styles.generateSection}>
            <button
              onClick={handleGenerateKey}
              disabled={isGenerating}
              style={{
                ...styles.generateButton,
                opacity: isGenerating ? 0.6 : 1,
                cursor: isGenerating ? 'not-allowed' : 'pointer',
              }}
            >
              {isGenerating ? 'Generating...' : '🔑 Generate API Key'}
            </button>
            
            {generateError && (
              <div style={styles.error}>{generateError}</div>
            )}

            {generatedKey && (
              <div style={styles.generatedKeyContainer}>
                <div style={styles.generatedKeyHeader}>
                  <strong>✅ API Key Generated!</strong>
                  <button
                    onClick={handleCopyKey}
                    style={styles.copyButton}
                    title="Copy to clipboard"
                  >
                    {copied ? '✓ Copied' : '📋 Copy'}
                  </button>
                </div>
                <div style={styles.generatedKey}>
                  {generatedKey}
                </div>
                <div style={styles.warning}>
                  ⚠️ Save this key securely - it won't be shown again!
                </div>
              </div>
            )}
          </div>

          {/* Divider */}
          <div style={styles.divider}>
            <span style={styles.dividerText}>OR</span>
          </div>

          {/* Enter Existing API Key */}
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
    padding: '100px 20px 40px',
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
  generateSection: {
    marginBottom: '24px',
  },
  generateButton: {
    width: '100%',
    padding: '14px 16px',
    fontSize: '15px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #10b981, #059669)',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.2s',
    marginBottom: '16px',
  },
  generatedKeyContainer: {
    background: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    borderRadius: '8px',
    padding: '16px',
    marginTop: '16px',
  },
  generatedKeyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
    color: '#34d399',
    fontSize: '14px',
  },
  copyButton: {
    padding: '6px 12px',
    fontSize: '12px',
    background: 'rgba(16, 185, 129, 0.2)',
    border: '1px solid rgba(16, 185, 129, 0.4)',
    borderRadius: '6px',
    color: '#34d399',
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
  generatedKey: {
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '6px',
    padding: '12px',
    marginBottom: '12px',
    wordBreak: 'break-all',
    color: '#34d399',
    fontSize: '13px',
    fontFamily: 'monospace',
  },
  warning: {
    fontSize: '12px',
    color: 'rgba(251, 191, 36, 0.9)',
    textAlign: 'center',
    fontStyle: 'italic',
  },
  divider: {
    display: 'flex',
    alignItems: 'center',
    margin: '24px 0',
    textAlign: 'center',
  },
  dividerText: {
    flex: 1,
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: '13px',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
  nav: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 100,
    background: 'rgba(0, 0, 0, 0.8)',
    backdropFilter: 'blur(20px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  navContent: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '16px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
  },
  logoText: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#fff',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    letterSpacing: '-0.02em',
  },
  navLinks: {
    display: 'flex',
    gap: '8px',
    alignItems: 'center',
  },
  navLink: {
    color: 'rgba(255, 255, 255, 0.7)',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '500',
    padding: '8px 16px',
    borderRadius: '6px',
    transition: 'all 0.2s',
  },
  authButtons: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  loginButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.8)',
    textDecoration: 'none',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    transition: 'all 0.2s',
    background: 'rgba(255, 255, 255, 0.05)',
  },
  signupButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '8px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    transition: 'all 0.2s',
  },
  userInfo: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    marginRight: '8px',
  },
  dashboardButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '8px',
    border: 'none',
    transition: 'all 0.2s',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
  },
};
