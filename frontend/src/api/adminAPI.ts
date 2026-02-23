import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const ADMIN_API_KEY = import.meta.env.VITE_ADMIN_API_KEY || 'admin-secret-key-change-me';

const adminApi = axios.create({
  baseURL: `${API_BASE_URL}/admin`,
});

adminApi.interceptors.request.use(async (config) => {
  config.params = { ...config.params, api_key: ADMIN_API_KEY };
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export interface AnalyticsSummary {
  total_users: number;
  active_users: number;
  total_requests: number;
  cache_hit_ratio: number;
  total_revenue: number;
  active_api_keys: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string | null;
  api_key_count: number;
  total_usage: number;
  last_used_at: string | null;
}

export interface TopUser {
  tenant_id: string;
  email: string;
  name: string;
  plan: string;
  total_requests: number;
  total_cache_hits: number;
  total_cost: number;
  usage_count: number;
  rank: number;
}

export interface GrowthData {
  date: string;
  new_users: number;
  active_users: number;
  total_users: number;
}

export interface UsageData {
  date: string;
  requests: number;
  cache_hits: number;
  cache_misses: number;
}

export interface PlanDistribution {
  plan_name: string;
  user_count: number;
  percentage: number;
}

export const adminAPI = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const response = await adminApi.get('/analytics/summary');
    const d = response.data;
    return {
      total_users: d.total_users ?? 0,
      active_users: d.active_users ?? 0,
      total_requests: d.total_requests ?? 0,
      cache_hit_ratio: d.cache_hit_ratio ?? 0,
      total_revenue: d.total_cost_estimate ?? 0,
      active_api_keys: d.total_api_keys ?? 0,
    };
  },

  getAllUsers: async (page: number = 1, limit: number = 20, search?: string) => {
    const offset = (page - 1) * limit;
    const response = await adminApi.get('/users', {
      params: { limit, offset, search: search || undefined }
    });
    const data = response.data;
    return {
      users: data.users ?? [],
      total: data.total ?? 0,
      pages: Math.ceil((data.total ?? 0) / limit),
    };
  },

  getUserDetails: async (userId: string) => {
    const response = await adminApi.get(`/users/${userId}/details`);
    return response.data;
  },

  getTopUsers: async (limit: number = 100, sortBy: string = 'requests'): Promise<TopUser[]> => {
    const backendSort = sortBy === 'hits' ? 'requests' : sortBy === 'savings' ? 'cost' : 'usage_count';
    const response = await adminApi.get('/analytics/top-users', {
      params: { limit, sort_by: backendSort }
    });
    const users = response.data.users ?? [];
    return users.map((u: any, i: number) => ({
      tenant_id: u.tenant_id,
      email: u.email ?? '',
      name: u.name ?? '',
      plan: u.plan ?? 'free',
      total_requests: u.total_requests ?? 0,
      total_cache_hits: u.total_cache_hits ?? 0,
      total_cost: u.total_cost ?? 0,
      usage_count: u.usage_count ?? 0,
      rank: i + 1,
    }));
  },

  getGrowthData: async (days: number = 30): Promise<GrowthData[]> => {
    const response = await adminApi.get('/analytics/user-growth', {
      params: { days, period: 'daily' }
    });
    const raw = response.data.data ?? [];
    return raw.map((r: any) => ({
      date: r.date ?? '',
      new_users: r.new_users ?? 0,
      active_users: r.new_api_keys ?? 0,
      total_users: r.total_users ?? 0,
    }));
  },

  getUsageData: async (days: number = 30): Promise<UsageData[]> => {
    const response = await adminApi.get('/analytics/usage-trends', {
      params: { days, period: 'daily' }
    });
    const raw = response.data.data ?? [];
    return raw.map((r: any) => ({
      date: r.date ?? '',
      requests: r.requests ?? 0,
      cache_hits: r.cache_hits ?? 0,
      cache_misses: r.cache_misses ?? 0,
    }));
  },

  getPlanDistribution: async (): Promise<PlanDistribution[]> => {
    const response = await adminApi.get('/analytics/plan-distribution');
    const plans = response.data.plans ?? [];
    return plans.map((p: any) => ({
      plan_name: p.plan ?? 'unknown',
      user_count: p.count ?? 0,
      percentage: p.percentage ?? 0,
    }));
  },

  getSystemStats: async () => {
    const response = await adminApi.get('/system/stats');
    return response.data;
  },
};
