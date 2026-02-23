import { useEffect, useState } from 'react';
import { Server, Database, Activity, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import { adminAPI } from '../api/adminAPI';

interface SystemStats {
  cache: {
    total_tenants: number;
    total_cache_entries: number;
    avg_entries_per_tenant: number;
  };
  database: {
    total_users: number;
    active_api_keys: number;
  };
  daily_usage: {
    requests_24h: number;
    cache_hits_24h: number;
    cache_misses_24h: number;
  };
}

export default function AdminSettings() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  useEffect(() => {
    loadSystemStats();
    const interval = setInterval(loadSystemStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminAPI.getSystemStats();
      setStats(data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error loading system stats:', err);
      setError('Failed to load system stats');
    } finally {
      setLoading(false);
    }
  };

  const hitRate24h = stats
    ? ((stats.daily_usage.cache_hits_24h / (stats.daily_usage.requests_24h || 1)) * 100)
    : 0;

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading system stats...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Health</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Live system metrics from Supabase & cache engine
          </p>
        </div>
        <button
          onClick={loadSystemStats}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="mr-4 text-green-600 dark:text-green-400">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                System Healthy
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Last checked: {lastRefresh.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Requests (24h)</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(stats?.daily_usage.requests_24h ?? 0).toLocaleString()}
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <Activity className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Cache Hits (24h)</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(stats?.daily_usage.cache_hits_24h ?? 0).toLocaleString()}
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <Activity className="w-5 h-5 text-purple-600 dark:text-purple-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Hit Rate (24h)</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {hitRate24h.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Server className="w-6 h-6 text-blue-600 dark:text-blue-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Cache Statistics
            </h2>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Active Tenants</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.cache.total_tenants ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Cache Entries</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {(stats?.cache.total_cache_entries ?? 0).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Avg Entries/Tenant</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.cache.avg_entries_per_tenant ?? 0}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Database className="w-6 h-6 text-purple-600 dark:text-purple-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Database Statistics
            </h2>
          </div>

          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Users</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.database.total_users ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Active API Keys</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.database.active_api_keys ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Cache Misses (24h)</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {(stats?.daily_usage.cache_misses_24h ?? 0).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
