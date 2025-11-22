import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const AUTH_TOKEN_KEY = 'auth_token';

interface SignUpData {
  email: string;
  password: string;
  name?: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface User {
  id: number;
  email: string;
  name?: string;
  is_admin?: boolean;
  created_at?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authAPI = {
  /**
   * Sign up a new user
   */
  signUp: async (data: SignUpData): Promise<{ user_id: number; email: string; name?: string }> => {
    const response = await axios.post(`${API_BASE_URL}/api/auth/signup`, data);
    return response.data;
  },

  /**
   * Login with email and password
   */
  login: async (data: LoginData): Promise<AuthResponse> => {
    const response = await axios.post(`${API_BASE_URL}/api/auth/login`, data);
    return response.data;
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const token = authAPI.getAuthToken();
    if (!token) {
      throw new Error('No auth token');
    }

    const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  },

  /**
   * Logout (clear token)
   */
  logout: async (): Promise<void> => {
    await axios.post(`${API_BASE_URL}/api/auth/logout`);
    authAPI.clearAuthToken();
  },

  /**
   * Set auth token in localStorage
   */
  setAuthToken: (token: string): void => {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  },

  /**
   * Get auth token from localStorage
   */
  getAuthToken: (): string | null => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },

  /**
   * Clear auth token from localStorage
   */
  clearAuthToken: (): void => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: (): boolean => {
    return !!authAPI.getAuthToken();
  }
};
