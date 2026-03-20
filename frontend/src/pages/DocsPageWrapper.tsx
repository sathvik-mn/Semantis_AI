import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { DocsPage } from '../components/DocsPage';
import { LightRays } from '../components/LightRays';

export function DocsPageWrapper() {
  const { isAuthenticated } = useAuth();

  return (
    <div style={styles.container}>
      <LightRays />
      {/* Navigation Bar */}
      <nav className="fixed top-0 inset-x-0 z-50 bg-black/70 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
          <Link
            to={isAuthenticated ? '/playground' : '/'}
            className="text-2xl font-extrabold text-gradient no-underline"
          >
            Semantis AI
          </Link>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <Link to="/playground" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Playground</Link>
                <Link to="/settings" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Settings</Link>
                <Link to="/metrics" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Metrics</Link>
              </>
            ) : (
              <>
                <Link to="/signin" className="btn-ghost no-underline">Sign In</Link>
                <Link to="/signup" className="btn-primary no-underline">Get Started</Link>
              </>
            )}
          </div>
        </div>
      </nav>
      <div style={styles.content}>
        <DocsPage />
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    padding: '40px 20px',
    paddingTop: '80px',  // Space for fixed nav
    position: 'relative',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    position: 'relative',
    zIndex: 1,
  },
};
