import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/semanticAPI';
import { LightRays } from '../components/LightRays';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export function StatusPage() {
  const [status, setStatus] = useState<api.HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setError(null);
      const data = await api.checkHealth();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const overallOk = status?.status === 'ok';
  const redisOk = status?.redis?.status === 'ok' || status?.redis?.status === 'healthy';

  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>System Status</h1>
          <p style={styles.subtitle}>
            Real-time status of Semantis AI services
          </p>
        </div>

        {loading ? (
          <div style={styles.loading}></div>
        ) : error ? (
          <div style={styles.error}>
            <h3 style={styles.errorTitle}>Unable to reach API</h3>
            <p style={styles.errorText}>{error}</p>
            <p style={styles.errorHint}>
              Ensure the backend is running at {BACKEND_URL}
            </p>
          </div>
        ) : (
          <div style={styles.grid}>
            <div style={statusCardStyle(overallOk)}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>API</span>
                <span style={badgeStyle(overallOk)}>
                  {overallOk ? 'Operational' : 'Degraded'}
                </span>
              </div>
              <p style={styles.cardDesc}>
                {status?.service} v{status?.version || '—'}
              </p>
            </div>

            <div style={statusCardStyle(redisOk)}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Cache (Redis)</span>
                <span style={badgeStyle(redisOk)}>
                  {redisOk ? 'Operational' : 'Unavailable'}
                </span>
              </div>
              <p style={styles.cardDesc}>
                {status?.redis?.status || 'Unknown'}
              </p>
            </div>

            <div style={styles.card}>
              <div style={styles.cardHeader}>
                <span style={styles.cardTitle}>Cache Stats</span>
              </div>
              <p style={styles.cardDesc}>
                {status?.cache
                  ? `${status.cache.tenants} tenants, ${status.cache.total_entries.toLocaleString()} entries`
                  : '—'}
              </p>
            </div>

            {status?.system && (
              <div style={styles.card}>
                <div style={styles.cardHeader}>
                  <span style={styles.cardTitle}>System</span>
                </div>
                <p style={styles.cardDesc}>
                  CPU: {status.system.cpu_percent}% · Memory: {status.system.memory_percent}% · {status.system.memory_available_gb} GB free
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function statusCardStyle(ok: boolean): React.CSSProperties {
  return {
    ...styles.card,
    borderColor: ok ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
    background: ok ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
  };
}

function badgeStyle(ok: boolean): React.CSSProperties {
  return {
    fontSize: '12px',
    fontWeight: '600',
    padding: '4px 10px',
    borderRadius: '6px',
    background: ok ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
    color: ok ? '#34d399' : '#f87171',
  };
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    padding: '40px 20px',
    position: 'relative',
  },
  content: {
    maxWidth: '800px',
    margin: '0 auto',
    position: 'relative',
    zIndex: 1,
  },
  header: {
    marginBottom: '32px',
  },
  title: {
    fontSize: '36px',
    color: '#fff',
    marginBottom: '8px',
    fontWeight: '700',
  },
  subtitle: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: '20px',
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '20px',
    backdropFilter: 'blur(10px)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  cardTitle: {
    fontSize: '16px',
    color: '#fff',
    fontWeight: '600',
  },
  cardDesc: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    margin: 0,
  },
  loading: {
    height: '200px',
    background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
    animation: 'shimmer 1.5s infinite',
    borderRadius: '12px',
  },
  error: {
    padding: '24px',
    background: 'rgba(239, 68, 68, 0.15)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '12px',
  },
  errorTitle: {
    color: '#f87171',
    marginBottom: '8px',
    fontSize: '18px',
  },
  errorText: {
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: '8px',
  },
  errorHint: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: '13px',
    margin: 0,
  },
};
