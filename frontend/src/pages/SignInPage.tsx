import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, AlertCircle, ArrowLeft, Chrome } from 'lucide-react';
import { Prism } from '../components/Prism';
import { useAuth } from '../contexts/AuthContext';

export function SignInPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/playground', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);

    try {
      await login(email, password);
      // Login successful - navigate to playground
      navigate('/playground');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // Mock Google sign-in
    alert('Google Sign In - Coming Soon!');
  };

  return (
    <div style={styles.container}>
      <Prism />

      {/* Back Arrow */}
      <Link to="/" style={styles.backButton}>
        <ArrowLeft size={20} />
      </Link>

      <div style={styles.content}>
        <div style={styles.card}>
          <div style={styles.header}>
            <h1 style={styles.title}>Welcome Back</h1>
            <p style={styles.subtitle}>Sign in to your Semantis AI account</p>
          </div>

          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>
                <Mail size={16} />
                <span>Email Address</span>
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                style={styles.input}
                required
                autoFocus
              />
            </div>

            <div style={styles.inputGroup}>
              <label style={styles.label}>
                <Lock size={16} />
                <span>Password</span>
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                style={styles.input}
                required
              />
            </div>

            {error && (
              <div style={styles.error}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                ...styles.submitButton,
                opacity: loading ? 0.7 : 1,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div style={styles.divider}>
            <span style={styles.dividerLine} />
            <span style={styles.dividerText}>OR</span>
            <span style={styles.dividerLine} />
          </div>

          <button onClick={handleGoogleSignIn} style={styles.googleButton}>
            <Chrome size={20} />
            <span>Continue with Google</span>
          </button>

          <div style={styles.footer}>
            Don't have an account?{' '}
            <Link to="/signup" style={styles.link}>
              Sign up
            </Link>
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
    padding: '20px',
    position: 'relative',
    overflow: 'hidden',
  },
  backButton: {
    position: 'fixed',
    top: '24px',
    left: '24px',
    zIndex: 100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '44px',
    height: '44px',
    borderRadius: '12px',
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    color: 'rgba(255, 255, 255, 0.8)',
    textDecoration: 'none',
    backdropFilter: 'blur(10px)',
    transition: 'all 0.3s ease',
    cursor: 'pointer',
  },
  content: {
    maxWidth: '440px',
    width: '100%',
    position: 'relative',
    zIndex: 1,
  },
  card: {
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '24px',
    padding: '48px 40px',
    backdropFilter: 'blur(40px)',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    animation: 'slideUp 0.6s ease',
  },
  header: {
    textAlign: 'center',
    marginBottom: '40px',
  },
  title: {
    fontSize: '32px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '8px',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: '1.5',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  label: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    fontSize: '15px',
    background: 'rgba(0, 0, 0, 0.4)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '12px',
    color: '#fff',
    outline: 'none',
    transition: 'all 0.3s ease',
    boxSizing: 'border-box',
  },
  submitButton: {
    width: '100%',
    padding: '16px',
    fontSize: '16px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)',
    marginTop: '8px',
  },
  error: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '12px 16px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '12px',
    color: '#fca5a5',
    fontSize: '14px',
  },
  divider: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    margin: '32px 0',
  },
  dividerLine: {
    flex: 1,
    height: '1px',
    background: 'rgba(255, 255, 255, 0.1)',
  },
  dividerText: {
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: '13px',
    fontWeight: '600',
    letterSpacing: '0.05em',
  },
  googleButton: {
    width: '100%',
    padding: '16px',
    fontSize: '15px',
    fontWeight: '600',
    background: 'rgba(255, 255, 255, 0.08)',
    color: '#fff',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
  },
  footer: {
    marginTop: '32px',
    textAlign: 'center',
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  link: {
    color: '#3b82f6',
    textDecoration: 'none',
    fontWeight: '600',
    transition: 'color 0.2s',
  },
};
