import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
const ADMIN_API_KEY = import.meta.env.VITE_ADMIN_API_KEY || '';

const adminApi = axios.create({
  baseURL: `${API_BASE_URL}/admin`,
  params: {
    api_key: ADMIN_API_KEY
  }
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
  tenant_id: string;
  email: string;
  company_name: string;
  plan_name: string;
  status: string;
  created_at: string;
  total_requests: number;
  cache_hits: number;
}

export interface UserDetail {
  tenant_id: string;
  email: string;
  company_name: string;
  plan_name: string;
  status: string;
  created_at: string;
  total_requests: number;
  cache_hits: number;
  cache_hit_ratio: number;
  total_cost_saved: number;
  api_keys: Array<{
    key_id: string;
    key_name: string;
    created_at: string;
    last_used: string;
  }>;
}

export interface TopUser {
  tenant_id: string;
  email: string;
  company_name: string;
  total_requests: number;
  cache_hits: number;
  cost_saved: number;
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
    const response = await adminApi.get('/summary');
    return response.data;
  },

  getAllUsers: async (page: number = 1, limit: number = 20, search?: string) => {
    const response = await adminApi.get('/users', {
      params: { page, limit, search }
    });
    return response.data;
  },

  getUserDetails: async (tenantId: string): Promise<UserDetail> => {
    const response = await adminApi.get(`/users/${tenantId}`);
    return response.data;
  },

  updateUserStatus: async (tenantId: string, status: string) => {
    const response = await adminApi.patch(`/users/${tenantId}/status`, { status });
    return response.data;
  },

  updateUserPlan: async (tenantId: string, planName: string) => {
    const response = await adminApi.patch(`/users/${tenantId}/plan`, { plan_name: planName });
    return response.data;
  },

  getTopUsers: async (limit: number = 100, sortBy: string = 'requests'): Promise<TopUser[]> => {
    const response = await adminApi.get('/top-users', {
      params: { limit, sort_by: sortBy }
    });
    return response.data.users;
  },

  getGrowthData: async (days: number = 30): Promise<GrowthData[]> => {
    const response = await adminApi.get('/analytics/growth', {
      params: { days }
    });
    return response.data;
  },

  getUsageData: async (days: number = 30): Promise<UsageData[]> => {
    const response = await adminApi.get('/analytics/usage', {
      params: { days }
    });
    return response.data;
  },

  getPlanDistribution: async (): Promise<PlanDistribution[]> => {
    const response = await adminApi.get('/analytics/plans');
    return response.data;
  }
};
