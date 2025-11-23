import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { SignInPage } from './pages/SignInPage';
import { SignUpPage } from './pages/SignUpPage';
import { PricingPage } from './pages/PricingPage';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { MetricsPage } from './pages/MetricsPage';
import { LogsPage } from './pages/LogsPage';
import { SettingsPage } from './pages/SettingsPage';
import { DocsPageWrapper } from './pages/DocsPageWrapper';
import { Layout } from './components/Layout';
import { hasApiKey } from './api/semanticAPI';
import AdminLayout from './components/AdminLayout';
import AdminDashboard from './pages/AdminDashboard';
import AdminUsers from './pages/AdminUsers';
import AdminTopUsers from './pages/AdminTopUsers';
import AdminAnalytics from './pages/AdminAnalytics';
import AdminSettings from './pages/AdminSettings';
import AdminLoginPage from './pages/AdminLoginPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  // Wait for auth check to complete before redirecting
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        color: '#fff'
      }}>
        Loading...
      </div>
    );
  }

  // Require authentication - users must sign up/login to access protected routes
  if (!isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }

  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, loading } = useAuth();

  // Wait for auth check to complete before redirecting
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        color: '#fff'
      }}>
        Loading...
      </div>
    );
  }

  // Check if user is authenticated and is admin
  if (!isAuthenticated || !user?.is_admin) {
    return <Navigate to="/admin/login" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/signin" element={<SignInPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/home" element={<PlaygroundPage />} />
        <Route path="/playground" element={<PlaygroundPage />} />
        <Route path="/metrics" element={<MetricsPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/docs" element={<DocsPageWrapper />} />
      </Route>
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminLayout />
          </AdminRoute>
        }
      >
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<AdminUsers />} />
        <Route path="top-users" element={<AdminTopUsers />} />
        <Route path="analytics" element={<AdminAnalytics />} />
        <Route path="settings" element={<AdminSettings />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
