import { useEffect, useState } from 'react';
import { Server, Database, Activity, AlertCircle, CheckCircle, Clock, Cpu, HardDrive } from 'lucide-react';

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  last_check: string;
}

interface CacheStats {
  total_entries: number;
  memory_used: string;
  hit_rate: number;
  avg_latency: number;
}

interface DatabaseStats {
  connection_pool_size: number;
  active_connections: number;
  query_performance: number;
  storage_used: string;
}

export default function AdminSettings() {
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    status: 'healthy',
    uptime: 0,
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    last_check: new Date().toISOString()
  });

  const [cacheStats, setCacheStats] = useState<CacheStats>({
    total_entries: 0,
    memory_used: '0 MB',
    hit_rate: 0,
    avg_latency: 0
  });

  const [databaseStats, setDatabaseStats] = useState<DatabaseStats>({
    connection_pool_size: 20,
    active_connections: 0,
    query_performance: 0,
    storage_used: '0 GB'
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSystemStats();
    const interval = setInterval(loadSystemStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemStats = async () => {
    try {
      setLoading(true);
      setSystemHealth({
        status: 'healthy',
        uptime: Math.floor(Math.random() * 1000000),
        cpu_usage: Math.random() * 100,
        memory_usage: Math.random() * 100,
        disk_usage: Math.random() * 100,
        last_check: new Date().toISOString()
      });

      setCacheStats({
        total_entries: Math.floor(Math.random() * 100000),
        memory_used: `${(Math.random() * 1000).toFixed(2)} MB`,
        hit_rate: Math.random() * 100,
        avg_latency: Math.random() * 100
      });

      setDatabaseStats({
        connection_pool_size: 20,
        active_connections: Math.floor(Math.random() * 20),
        query_performance: Math.random() * 100,
        storage_used: `${(Math.random() * 100).toFixed(2)} GB`
      });
    } catch (error) {
      console.error('Error loading system stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'degraded':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'down':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-6 h-6" />;
      case 'degraded':
        return <AlertCircle className="w-6 h-6" />;
      case 'down':
        return <AlertCircle className="w-6 h-6" />;
      default:
        return <Activity className="w-6 h-6" />;
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading system stats...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Settings & Health</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Monitor system health and configuration
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className={`mr-4 ${getStatusColor(systemHealth.status)}`}>
              {getStatusIcon(systemHealth.status)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white capitalize">
                System {systemHealth.status}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Last checked: {new Date(systemHealth.last_check).toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={loadSystemStats}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Uptime</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatUptime(systemHealth.uptime)}
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <Cpu className="w-5 h-5 text-purple-600 dark:text-purple-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">CPU Usage</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {systemHealth.cpu_usage.toFixed(1)}%
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <Activity className="w-5 h-5 text-green-600 dark:text-green-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Memory</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {systemHealth.memory_usage.toFixed(1)}%
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center mb-2">
              <HardDrive className="w-5 h-5 text-orange-600 dark:text-orange-400 mr-2" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Disk</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {systemHealth.disk_usage.toFixed(1)}%
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
              <span className="text-sm text-gray-600 dark:text-gray-400">Total Entries</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {cacheStats.total_entries.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Memory Used</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {cacheStats.memory_used}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</span>
              <span className="text-lg font-semibold text-green-600 dark:text-green-400">
                {cacheStats.hit_rate.toFixed(2)}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Avg Latency</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {cacheStats.avg_latency.toFixed(2)}ms
              </span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
              Clear Cache
            </button>
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
              <span className="text-sm text-gray-600 dark:text-gray-400">Connection Pool Size</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {databaseStats.connection_pool_size}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Active Connections</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {databaseStats.active_connections}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Query Performance</span>
              <span className="text-lg font-semibold text-green-600 dark:text-green-400">
                {databaseStats.query_performance.toFixed(2)}ms
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Storage Used</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {databaseStats.storage_used}
              </span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Optimize Database
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Admin Configuration
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              System Maintenance Mode
            </label>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              <span className="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">
                Enable maintenance mode
              </span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Auto-refresh Interval (seconds)
            </label>
            <input
              type="number"
              defaultValue={30}
              min={10}
              max={300}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Cache TTL (seconds)
            </label>
            <input
              type="number"
              defaultValue={3600}
              min={60}
              max={86400}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
