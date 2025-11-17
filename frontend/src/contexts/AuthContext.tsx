import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../api/authAPI';

interface User {
  id: number;
  email: string;
  name?: string;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      try {
        if (authAPI.isAuthenticated()) {
          const userData = await authAPI.getCurrentUser();
          setUser(userData);
        }
      } catch (error) {
        console.error('Failed to load user:', error);
        authAPI.clearAuthToken();
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login({ email, password });
      authAPI.setAuthToken(response.access_token);
      setUser(response.user);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const signup = async (email: string, password: string, name?: string) => {
    try {
      await authAPI.signUp({ email, password, name });
      // Auto-login after signup
      await login(email, password);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed');
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
      setUser(null);
    } catch (error) {
      // Clear token anyway
      authAPI.clearAuthToken();
      setUser(null);
    }
  };

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
