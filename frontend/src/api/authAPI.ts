/**
 * Legacy auth API adapter.
 * Signup/login/logout are now handled by Supabase via AuthContext.
 * This module is kept for backward compatibility with components
 * that import authAPI but all auth state should come from useAuth().
 */
import { supabase } from '../lib/supabase';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const authAPI = {
  getCurrentUser: async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('Not authenticated');

    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch user');
    return res.json();
  },

  getAccessToken: async (): Promise<string | null> => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  },

  isAuthenticated: (): boolean => {
    // Synchronous best-effort check; real check is async via getSession
    return false; // callers should use useAuth().isAuthenticated instead
  },
};
