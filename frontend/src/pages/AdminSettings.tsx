import { useEffect, useState, useCallback } from 'react';
import {
  Server,
  Database,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Shield,
  Key,
  Globe,
  CreditCard,
  Cpu,
  FileText,
  Settings,
  Minus,
} from 'lucide-react';
import { adminAPI } from '../api/adminAPI';

// ── Types ──────────────────────────────────────────────────────────────────────

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

interface ServiceCheck {
  status: 'up' | 'down' | 'configured' | 'not_configured';
  latency_ms?: number;
  tenants?: number;
  total_entries?: number;
  error?: string;
}

interface HealthCheckResponse {
  status: 'healthy' | 'degraded';
  checks: {
    database: ServiceCheck;
    cache_engine: ServiceCheck;
    redis: ServiceCheck;
    openai: ServiceCheck;
    stripe: ServiceCheck;
  };
  config: {
    encryption_key: boolean;
    encryption_salt: boolean;
    admin_api_key: boolean;
    frontend_url: string;
    allowed_origins: string;
  };
}

interface AuditLog {
  id: string;
  created_at: string;
  email?: string;
  user_name?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  org_id?: string;
  user_id?: string;
}

interface AuditLogsResponse {
  total: number;
  logs: AuditLog[];
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatTime(date: Date): string {
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function StatusDot({ status }: { status: string }) {
  const isUp = status === 'up' || status === 'configured';
  const isDown = status === 'down';
  const color = isUp
    ? 'bg-green-500'
    : isDown
      ? 'bg-red-500'
      : 'bg-gray-400';
  return (
    <span className={`inline-block w-3 h-3 rounded-full ${color}`} />
  );
}

function statusLabel(status: string): string {
  switch (status) {
    case 'up':
      return 'Operational';
    case 'down':
      return 'Down';
    case 'configured':
      return 'Configured';
    case 'not_configured':
      return 'Not Configured';
    default:
      return status;
  }
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function AdminSettings() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);

  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(true);

  const [errorStats, setErrorStats] = useState<string | null>(null);
  const [errorHealth, setErrorHealth] = useState<string | null>(null);
  const [errorLogs, setErrorLogs] = useState<string | null>(null);

  const [lastHealthCheck, setLastHealthCheck] = useState<Date | null>(null);
  const [lastStatsRefresh, setLastStatsRefresh] = useState<Date | null>(null);

  // ── Loaders ────────────────────────────────────────────────────────────────

  const loadHealth = useCallback(async () => {
    try {
      setLoadingHealth(true);
      setErrorHealth(null);
      const data = await adminAPI.getHealthCheck();
      setHealth(data);
      setLastHealthCheck(new Date());
    } catch (err) {
      console.error('Health check failed:', err);
      setErrorHealth('Failed to fetch health status');
    } finally {
      setLoadingHealth(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      setLoadingStats(true);
      setErrorStats(null);
      const data = await adminAPI.getSystemStats();
      setStats(data);
      setLastStatsRefresh(new Date());
    } catch (err) {
      console.error('Stats load failed:', err);
      setErrorStats('Failed to load system stats');
    } finally {
      setLoadingStats(false);
    }
  }, []);

  const loadAuditLogs = useCallback(async () => {
    try {
      setLoadingLogs(true);
      setErrorLogs(null);
      const data: AuditLogsResponse = await adminAPI.getAuditLogs(20, 0);
      setAuditLogs(data.logs);
      setAuditTotal(data.total);
    } catch (err) {
      console.error('Audit logs load failed:', err);
      setErrorLogs('Failed to load audit logs');
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  // ── Effects ────────────────────────────────────────────────────────────────

  useEffect(() => {
    loadHealth();
    loadStats();
    loadAuditLogs();

    const healthInterval = setInterval(loadHealth, 30000);
    const statsInterval = setInterval(loadStats, 30000);

    return () => {
      clearInterval(healthInterval);
      clearInterval(statsInterval);
    };
  }, [loadHealth, loadStats, loadAuditLogs]);

  // ── Derived values ─────────────────────────────────────────────────────────

  const hitRate24h = stats
    ? (stats.daily_usage.cache_hits_24h / (stats.daily_usage.requests_24h || 1)) * 100
    : 0;

  const isHealthy = health?.status === 'healthy';
  const refreshing = loadingHealth || loadingStats;

  // ── Initial loading state ──────────────────────────────────────────────────

  if (loadingHealth && !health && loadingStats && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 text-gray-400 animate-spin mr-3" />
        <span className="text-lg text-gray-600 dark:text-gray-400">
          Loading system health...
        </span>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            System Health & Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Live health checks, metrics, configuration, and audit trail
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            loadHealth();
            loadStats();
            loadAuditLogs();
          }}
          disabled={refreshing}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh All
        </button>
      </div>

      {/* Errors */}
      {(errorHealth || errorStats) && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm space-y-1">
          {errorHealth && <p>{errorHealth}</p>}
          {errorStats && <p>{errorStats}</p>}
        </div>
      )}

      {/* ─── 1. Overall Status Banner ─────────────────────────────────────── */}
      <div
        className={`rounded-lg shadow p-6 ${
          health
            ? isHealthy
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
              : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
        }`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {health ? (
              isHealthy ? (
                <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400 mr-4" />
              ) : (
                <AlertTriangle className="w-8 h-8 text-yellow-600 dark:text-yellow-400 mr-4" />
              )
            ) : (
              <Minus className="w-8 h-8 text-gray-400 mr-4" />
            )}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                {health
                  ? isHealthy
                    ? 'All Systems Operational'
                    : 'System Degraded'
                  : 'Status Unknown'}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {lastHealthCheck
                  ? `Last checked: ${formatTime(lastHealthCheck)}`
                  : 'Checking...'}
                {loadingHealth && ' (refreshing...)'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={loadHealth}
            disabled={loadingHealth}
            className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            title="Refresh health check"
          >
            <RefreshCw className={`w-5 h-5 text-gray-500 dark:text-gray-400 ${loadingHealth ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ─── 2. Service Health Checks ─────────────────────────────────────── */}
      {health && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
            Service Health Checks
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Database */}
            <ServiceCard
              name="Database"
              icon={<Database className="w-5 h-5" />}
              check={health.checks.database}
            />
            {/* Cache Engine */}
            <ServiceCard
              name="Cache Engine"
              icon={<Server className="w-5 h-5" />}
              check={health.checks.cache_engine}
              extraInfo={
                health.checks.cache_engine.status === 'up'
                  ? `${health.checks.cache_engine.tenants ?? 0} tenants, ${(health.checks.cache_engine.total_entries ?? 0).toLocaleString()} entries`
                  : undefined
              }
            />
            {/* Redis */}
            <ServiceCard
              name="Redis"
              icon={<Cpu className="w-5 h-5" />}
              check={health.checks.redis}
            />
            {/* OpenAI */}
            <ServiceCard
              name="OpenAI"
              icon={<Globe className="w-5 h-5" />}
              check={health.checks.openai}
            />
            {/* Stripe */}
            <ServiceCard
              name="Stripe"
              icon={<CreditCard className="w-5 h-5" />}
              check={health.checks.stripe}
            />
          </div>
        </div>
      )}

      {/* ─── 3. Daily Metrics ─────────────────────────────────────────────── */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
          <Clock className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
          Daily Metrics (24h)
          {lastStatsRefresh && (
            <span className="ml-2 text-xs font-normal text-gray-400">
              Updated {formatTime(lastStatsRefresh)}
            </span>
          )}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="Requests"
            value={(stats?.daily_usage.requests_24h ?? 0).toLocaleString()}
            icon={<Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
          />
          <MetricCard
            label="Cache Hits"
            value={(stats?.daily_usage.cache_hits_24h ?? 0).toLocaleString()}
            icon={<CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />}
          />
          <MetricCard
            label="Hit Rate"
            value={`${hitRate24h.toFixed(1)}%`}
            icon={<Activity className="w-5 h-5 text-purple-600 dark:text-purple-400" />}
          />
          <MetricCard
            label="Cache Misses"
            value={(stats?.daily_usage.cache_misses_24h ?? 0).toLocaleString()}
            icon={<XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />}
          />
        </div>
      </div>

      {/* ─── 4 & 5. Cache + Database Statistics ───────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cache Statistics */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Server className="w-6 h-6 text-blue-600 dark:text-blue-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Cache Statistics
            </h3>
          </div>
          <div className="space-y-4">
            <StatRow label="Active Tenants" value={stats?.cache.total_tenants ?? 0} />
            <StatRow
              label="Total Cache Entries"
              value={(stats?.cache.total_cache_entries ?? 0).toLocaleString()}
            />
            <StatRow label="Avg Entries/Tenant" value={stats?.cache.avg_entries_per_tenant ?? 0} />
          </div>
        </div>

        {/* Database Statistics */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Database className="w-6 h-6 text-purple-600 dark:text-purple-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Database Statistics
            </h3>
          </div>
          <div className="space-y-4">
            <StatRow label="Total Users" value={stats?.database.total_users ?? 0} />
            <StatRow label="Active API Keys" value={stats?.database.active_api_keys ?? 0} />
          </div>
        </div>
      </div>

      {/* ─── 6. Environment Configuration ─────────────────────────────────── */}
      {health && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Settings className="w-6 h-6 text-gray-600 dark:text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Environment Configuration
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <EnvRow
              name="ENCRYPTION_KEY"
              configured={health.config.encryption_key}
              icon={<Key className="w-4 h-4" />}
            />
            <EnvRow
              name="ENCRYPTION_SALT"
              configured={health.config.encryption_salt}
              icon={<Shield className="w-4 h-4" />}
            />
            <EnvRow
              name="ADMIN_API_KEY"
              configured={health.config.admin_api_key}
              icon={<Key className="w-4 h-4" />}
            />
            <EnvValueRow
              name="FRONTEND_URL"
              value={health.config.frontend_url}
              icon={<Globe className="w-4 h-4" />}
            />
            <EnvValueRow
              name="ALLOWED_ORIGINS"
              value={health.config.allowed_origins}
              icon={<Globe className="w-4 h-4" />}
            />
          </div>
        </div>
      )}

      {/* ─── 7. Recent Audit Logs ─────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <FileText className="w-6 h-6 text-gray-600 dark:text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Audit Logs
            </h3>
            {auditTotal > 0 && (
              <span className="ml-2 text-xs text-gray-400">
                ({auditTotal} total)
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={loadAuditLogs}
            disabled={loadingLogs}
            className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            title="Refresh audit logs"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 dark:text-gray-400 ${loadingLogs ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {errorLogs && (
          <div className="p-3 mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-red-700 dark:text-red-300 text-sm">
            {errorLogs}
          </div>
        )}

        {loadingLogs && auditLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
            Loading audit logs...
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
            No audit logs found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
                  <th className="pb-2 pr-4 font-medium">Time</th>
                  <th className="pb-2 pr-4 font-medium">User</th>
                  <th className="pb-2 pr-4 font-medium">Action</th>
                  <th className="pb-2 pr-4 font-medium">Resource</th>
                  <th className="pb-2 font-medium">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="text-gray-700 dark:text-gray-300">
                    <td className="py-2 pr-4 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                      {formatTimestamp(log.created_at)}
                    </td>
                    <td className="py-2 pr-4 whitespace-nowrap">
                      {log.email || log.user_name || <span className="text-gray-400">system</span>}
                    </td>
                    <td className="py-2 pr-4 whitespace-nowrap">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2 pr-4 whitespace-nowrap text-xs font-mono">
                      {log.resource_type ? `${log.resource_type}${log.resource_id ? `:${log.resource_id}` : ''}` : <span className="text-gray-400">-</span>}
                    </td>
                    <td className="py-2 text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs">
                      {log.details && Object.keys(log.details).length > 0 ? JSON.stringify(log.details) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ServiceCard({
  name,
  icon,
  check,
  extraInfo,
}: {
  name: string;
  icon: React.ReactNode;
  check: ServiceCheck;
  extraInfo?: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center text-gray-600 dark:text-gray-400">
          {icon}
          <span className="ml-2 text-sm font-medium">{name}</span>
        </div>
        <StatusDot status={check.status} />
      </div>
      <p className="text-sm font-semibold text-gray-900 dark:text-white">
        {statusLabel(check.status)}
      </p>
      {check.latency_ms !== undefined && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {check.latency_ms}ms latency
        </p>
      )}
      {extraInfo && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{extraInfo}</p>
      )}
      {check.error && (
        <p className="text-xs text-red-500 dark:text-red-400 mt-1 truncate" title={check.error}>
          {check.error}
        </p>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex items-center mb-2">
        {icon}
        <span className="ml-2 text-sm font-medium text-gray-600 dark:text-gray-400">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <span className="text-lg font-semibold text-gray-900 dark:text-white">{value}</span>
    </div>
  );
}

function EnvRow({
  name,
  configured,
  icon,
}: {
  name: string;
  configured: boolean;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between border border-gray-200 dark:border-gray-700 rounded-lg p-3">
      <div className="flex items-center text-gray-600 dark:text-gray-400">
        {icon}
        <span className="ml-2 text-sm font-mono">{name}</span>
      </div>
      {configured ? (
        <CheckCircle className="w-5 h-5 text-green-500" />
      ) : (
        <XCircle className="w-5 h-5 text-red-500" />
      )}
    </div>
  );
}

function EnvValueRow({
  name,
  value,
  icon,
}: {
  name: string;
  value: string;
  icon: React.ReactNode;
}) {
  const isSet = value && value !== 'not set' && value !== '';
  return (
    <div className="flex items-center justify-between border border-gray-200 dark:border-gray-700 rounded-lg p-3">
      <div className="flex items-center text-gray-600 dark:text-gray-400">
        {icon}
        <span className="ml-2 text-sm font-mono">{name}</span>
      </div>
      <span
        className={`text-xs font-mono truncate max-w-[200px] ${
          isSet ? 'text-gray-700 dark:text-gray-300' : 'text-red-500 dark:text-red-400'
        }`}
        title={value || 'not set'}
      >
        {isSet ? value : 'not set'}
      </span>
    </div>
  );
}
