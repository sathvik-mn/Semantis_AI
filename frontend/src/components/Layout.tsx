import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useHealthCheck } from '../hooks/useSemanticCache';
import * as api from '../api/semanticAPI';
import { useAuth } from '../contexts/AuthContext';
import { AccountMenu } from './AccountMenu';

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const isHealthy = useHealthCheck(30000);
  const { isAuthenticated, user, logout: authLogout } = useAuth();

  const handleLogout = async () => {
    if (isAuthenticated) await authLogout();
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
    <div className="min-h-screen flex flex-col bg-surface noise">
      {/* Top accent line */}
      <div className="h-[2px] bg-gradient-to-r from-transparent via-blue-500 to-transparent" />

      <nav className="sticky top-0 z-50 bg-black/70 backdrop-blur-xl border-b border-white/[0.06]">
        <div className="max-w-[1400px] mx-auto px-5 py-3.5 flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-gradient no-underline shrink-0">
            Semantis AI
          </Link>

          <div className="flex gap-1 flex-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 text-sm font-medium rounded-lg no-underline transition-all ${
                  isActive(item.path)
                    ? 'text-white bg-white/[0.08]'
                    : 'text-white/60 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                {item.label}
              </Link>
            ))}
            {user?.is_admin && (
              <Link
                to="/admin"
                className={`px-4 py-2 text-sm font-medium rounded-lg no-underline transition-all ${
                  location.pathname.startsWith('/admin')
                    ? 'text-amber-300 bg-amber-500/10'
                    : 'text-amber-400/70 hover:text-amber-300 hover:bg-amber-500/10'
                }`}
              >
                Admin
              </Link>
            )}
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isHealthy ? 'bg-emerald-500' : isHealthy === null ? 'bg-amber-500' : 'bg-red-500'
                }`}
              />
              <span className="text-xs text-white/50">
                {isHealthy ? 'Connected' : isHealthy === null ? 'Checking...' : 'Offline'}
              </span>
            </div>
            <AccountMenu onLogout={handleLogout} />
          </div>
        </div>
      </nav>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="px-5 py-5 text-center border-t border-white/[0.06]">
        <p className="text-xs text-white/30">
          Semantis AI &mdash; Semantic Caching Platform
          <Link to="/status" className="ml-2 text-white/40 hover:text-white/60 no-underline">Status</Link>
          <Link to="/security" className="ml-2 text-white/40 hover:text-white/60 no-underline">Security</Link>
        </p>
      </footer>
    </div>
  );
}
