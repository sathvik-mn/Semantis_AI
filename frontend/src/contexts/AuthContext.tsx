import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase } from '../lib/supabase';
import type { User as SupabaseUser, Session } from '@supabase/supabase-js';

interface User {
  id: string;
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
  resetPassword: (email: string) => Promise<void>;
  updatePassword: (newPassword: string) => Promise<void>;
  loadUser: () => Promise<User | null>;
  getAccessToken: () => Promise<string | null>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function mapSupabaseUser(su: SupabaseUser): User {
  return {
    id: su.id,
    email: su.email ?? '',
    name: su.user_metadata?.name ?? su.email?.split('@')[0] ?? '',
  };
}

async function enrichUserFromBackend(token: string, user: User): Promise<User> {
  try {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    const res = await fetch(`${backendUrl}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      return {
        ...user,
        name: data.name || user.name,
        is_admin: data.is_admin ?? false,
      };
    }
  } catch {
    // Backend might not be running yet; fall back to Supabase data
  }
  return user;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      try {
        const sessionPromise = supabase.auth.getSession();
        const timeoutPromise = new Promise<null>((resolve) =>
          setTimeout(() => {
            console.warn('Auth session fetch timed out, continuing without session');
            resolve(null);
          }, 3000)
        );

        const result = await Promise.race([sessionPromise, timeoutPromise]);
        if (cancelled) return;
        const session = result && 'data' in result ? result.data.session : null;

        if (session?.user) {
          const mapped = mapSupabaseUser(session.user);
          setUser(mapped);
          setLoading(false);

          // Enrich from backend and load API key in background (non-blocking)
          enrichUserFromBackend(session.access_token, mapped).then((enriched) => {
            if (!cancelled) setUser(enriched);
          }).catch(() => {});
          import('../api/semanticAPI').then(async ({ getCurrentApiKey, setApiKey: setKey }) => {
            try {
              const data = await getCurrentApiKey();
              if (data.exists && data.api_key) setKey(data.api_key);
            } catch {}
          }).catch(() => {});
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error('Auth init failed:', err);
        if (!cancelled) setLoading(false);
      }
    };
    init();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (cancelled) return;
        if (session?.user) {
          const mapped = mapSupabaseUser(session.user);
          setUser(mapped);

          enrichUserFromBackend(session.access_token, mapped).then((enriched) => {
            if (!cancelled) setUser(enriched);
          }).catch(() => {});
          import('../api/semanticAPI').then(async ({ getCurrentApiKey, setApiKey: setKey }) => {
            try {
              const data = await getCurrentApiKey();
              if (data.exists && data.api_key) setKey(data.api_key);
            } catch {}
          }).catch(() => {});
        } else {
          setUser(null);
        }
      }
    );

    return () => {
      cancelled = true;
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    const { clearApiKey, getCurrentApiKey, setApiKey } = await import('../api/semanticAPI');
    clearApiKey();

    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(error.message);

    const mapped = mapSupabaseUser(data.user);
    const enriched = await enrichUserFromBackend(data.session.access_token, mapped);
    setUser(enriched);

    try {
      const apiKeyData = await getCurrentApiKey();
      if (apiKeyData.exists && apiKeyData.api_key) {
        setApiKey(apiKeyData.api_key);
      }
    } catch { /* ok */ }
  };

  const signup = async (email: string, password: string, name?: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name: name || email.split('@')[0] } },
    });
    if (error) throw new Error(error.message);
    if (data.user) {
      setUser(mapSupabaseUser(data.user));
    }
  };

  const logout = async () => {
    const { clearApiKey } = await import('../api/semanticAPI');
    clearApiKey();
    await supabase.auth.signOut();
    setUser(null);
  };

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    if (error) throw new Error(error.message);
  };

  const updatePassword = async (newPassword: string) => {
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
  };

  const loadUser = async (): Promise<User | null> => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.user) {
      let mapped = mapSupabaseUser(session.user);
      mapped = await enrichUserFromBackend(session.access_token, mapped);
      setUser(mapped);
      return mapped;
    }
    setUser(null);
    return null;
  };

  const getAccessToken = async (): Promise<string | null> => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        resetPassword,
        updatePassword,
        loadUser,
        getAccessToken,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
