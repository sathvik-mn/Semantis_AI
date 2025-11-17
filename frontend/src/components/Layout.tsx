import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useHealthCheck } from '../hooks/useSemanticCache';
import * as api from '../api/semanticAPI';
import { useAuth } from '../contexts/AuthContext';
import { AccountMenu } from './AccountMenu';

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const isHealthy = useHealthCheck(30000);
  const { user, isAuthenticated, logout: authLogout } = useAuth();

  const handleLogout = async () => {
    // Clear both auth token and API key
    if (isAuthenticated) {
      await authLogout();
    }
    api.clearApiKey();
    navigate('/');
  };

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/playground', label: 'Playground' },
    { path: '/metrics', label: 'Metrics' },
    { path: '/logs', label: 'Logs' },
    { path: '/settings', label: 'Settings' },
    { path: '/docs', label: 'Docs' },
  ];

  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <Link to="/" style={styles.logo}>
            Semantis AI
          </Link>

          <div style={styles.navLinks}>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  ...styles.navLink,
                  ...(isActive(item.path) ? styles.navLinkActive : {}),
                }}
              >
                {item.label}
              </Link>
            ))}
          </div>

          <div style={styles.navRight}>
            <div style={styles.healthIndicator}>
              <div
                style={{
                  ...styles.healthDot,
                  backgroundColor: isHealthy ? '#10b981' : isHealthy === null ? '#f59e0b' : '#ef4444',
                }}
              />
              <span style={styles.healthText}>
                {isHealthy ? 'Connected' : isHealthy === null ? 'Checking...' : 'Disconnected'}
              </span>
            </div>

            <AccountMenu onLogout={handleLogout} />
          </div>
        </div>
      </nav>

      <main style={styles.main}>
        <Outlet />
      </main>

      <footer style={styles.footer}>
        <p style={styles.footerText}>
          Semantis AI - Semantic Caching Platform
        </p>
      </footer>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  nav: {
    position: 'sticky',
    top: 0,
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
    alignItems: 'center',
    gap: '32px',
  },
  logo: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#fff',
    textDecoration: 'none',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  navLinks: {
    display: 'flex',
    gap: '8px',
    flex: 1,
  },
  navLink: {
    padding: '8px 16px',
    fontSize: '14px',
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.7)',
    textDecoration: 'none',
    borderRadius: '6px',
    transition: 'all 0.2s',
  },
  navLinkActive: {
    color: '#fff',
    background: 'rgba(59, 130, 246, 0.2)',
  },
  navRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  healthIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  healthDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  healthText: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.7)',
  },
  main: {
    flex: 1,
  },
  footer: {
    padding: '20px',
    textAlign: 'center',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
  },
  footerText: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
};
