import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../api/authAPI';

interface User {
  id: number;
  email: string;
  name?: string;
  is_admin?: boolean;
  created_at?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<User | null>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true); // Start with loading=true to check auth

  // Load user from token on mount if token exists (for page refresh persistence)
  useEffect(() => {
    const loadUserOnMount = async () => {
      try {
        if (authAPI.isAuthenticated()) {
          try {
            const userData = await authAPI.getCurrentUser();
            setUser(userData);
            
            // Also load API key if user is authenticated
            try {
              const { getCurrentApiKey, setApiKey } = await import('../api/semanticAPI');
              const apiKeyData = await getCurrentApiKey();
              if (apiKeyData.exists && apiKeyData.api_key) {
                setApiKey(apiKeyData.api_key);
              }
            } catch (err) {
              // Silently fail - user can generate API key manually
              console.debug('Could not load API key on mount:', err);
            }
          } catch (error: any) {
            // Token is invalid or expired - clear it
            console.debug('Token validation failed:', error);
            authAPI.clearAuthToken();
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Failed to load user on mount:', error);
        authAPI.clearAuthToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    loadUserOnMount();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // Clear any existing API key from previous sessions
      const { clearApiKey, getCurrentApiKey, setApiKey } = await import('../api/semanticAPI');
      clearApiKey();
      
      const response = await authAPI.login({ email, password });
      authAPI.setAuthToken(response.access_token);
      setUser(response.user);
      
      // Automatically load user's API key if it exists
      try {
        const apiKeyData = await getCurrentApiKey();
        if (apiKeyData.exists && apiKeyData.api_key) {
          setApiKey(apiKeyData.api_key);
        }
      } catch (err) {
        // Silently fail - user can generate API key manually
        console.debug('Could not load API key:', err);
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  // Load user from token (for admin login and explicit checks)
  const loadUser = async () => {
    try {
      if (authAPI.isAuthenticated()) {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
        return userData;
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      authAPI.clearAuthToken();
      setUser(null);
    }
    return null;
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
    loadUser,
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
