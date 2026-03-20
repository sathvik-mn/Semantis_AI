import { KpiCards } from '../components/KpiCards';
import { SavingsDashboard } from '../components/SavingsDashboard';
import { useMetrics } from '../hooks/useSemanticCache';
import { LightRays } from '../components/LightRays';

export function MetricsPage() {
  const { metrics, isLoading, error, refetch } = useMetrics(15000);

  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Performance Metrics</h1>
            <p style={styles.subtitle}>
              Monitor your semantic cache performance and cost savings
            </p>
          </div>
          <button onClick={refetch} style={styles.refreshButton} disabled={isLoading}>
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div style={styles.errorBanner}>
            Failed to load metrics. Please check your API key and try again.
          </div>
        )}

        <SavingsDashboard />
        <KpiCards metrics={metrics} isLoading={isLoading} />

        {!isLoading && !error && metrics && metrics.total_requests === 0 && (
          <div style={styles.emptyState}>
            <p style={styles.emptyTitle}>No data yet</p>
            <p style={styles.emptyText}>
              Run queries in the Playground to see metrics and cache performance.
              You can also send requests via the API to start collecting data.
            </p>
          </div>
        )}

        {metrics && metrics.total_requests > 0 && (
          <div style={styles.insightsSection}>
            <h2 style={styles.sectionTitle}>Insights</h2>

            {metrics.hit_ratio != null && (
              <div style={styles.insightCard}>
                <h3 style={styles.insightTitle}>Cache Effectiveness</h3>
                <p style={styles.insightText}>
                  Your cache hit ratio of {(metrics.hit_ratio * 100).toFixed(1)}% indicates{' '}
                  {metrics.hit_ratio > 0.6
                    ? 'excellent'
                    : metrics.hit_ratio > 0.4
                    ? 'good'
                    : 'developing'}{' '}
                  cache utilization.
                  {metrics.hit_ratio < 0.5 &&
                    ' Consider lowering the similarity threshold for more semantic hits.'}
                </p>
              </div>
            )}

            {metrics.semantic_hit_ratio != null && (
              <div style={styles.insightCard}>
                <h3 style={styles.insightTitle}>Semantic Matching</h3>
                <p style={styles.insightText}>
                  {(metrics.semantic_hit_ratio * 100).toFixed(1)}% of your hits are from semantic
                  matching, demonstrating the value of AI-powered caching beyond exact matches.
                </p>
              </div>
            )}

            {metrics.avg_latency_ms != null && (
              <div style={styles.insightCard}>
                <h3 style={styles.insightTitle}>Performance</h3>
                <p style={styles.insightText}>
                  Average latency of {metrics.avg_latency_ms.toFixed(0)}ms provides{' '}
                  {metrics.avg_latency_ms < 200
                    ? 'exceptional'
                    : metrics.avg_latency_ms < 400
                    ? 'solid'
                    : 'baseline'}{' '}
                  response times for your users.
                </p>
              </div>
            )}

            {metrics.tokens_saved_est != null && (
              <div style={styles.insightCard}>
                <h3 style={styles.insightTitle}>Cost Savings</h3>
                <p style={styles.insightText}>
                  Approximately {metrics.tokens_saved_est.toLocaleString()} tokens saved through
                  caching. Based on typical pricing, this translates to significant cost reduction
                  over time.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    padding: '40px 20px',
    position: 'relative',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    position: 'relative',
    zIndex: 1,
  },
  header: {
    marginBottom: '32px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
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
  refreshButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '500',
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid rgba(59, 130, 246, 0.4)',
    borderRadius: '8px',
    color: '#60a5fa',
    cursor: 'pointer',
    transition: 'all 0.2s',
    whiteSpace: 'nowrap',
  },
  errorBanner: {
    padding: '14px 20px',
    background: 'rgba(239, 68, 68, 0.15)',
    border: '1px solid rgba(239, 68, 68, 0.4)',
    borderRadius: '10px',
    color: '#fca5a5',
    fontSize: '14px',
    marginBottom: '24px',
  },
  insightsSection: {
    marginTop: '40px',
  },
  sectionTitle: {
    fontSize: '24px',
    color: '#fff',
    marginBottom: '20px',
    fontWeight: '600',
  },
  insightCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '16px',
    backdropFilter: 'blur(10px)',
  },
  insightTitle: {
    fontSize: '16px',
    color: '#60a5fa',
    marginBottom: '8px',
    fontWeight: '600',
  },
  insightText: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.6',
  },
  emptyState: {
    padding: '32px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px dashed rgba(255, 255, 255, 0.2)',
    borderRadius: '12px',
    textAlign: 'center',
    marginTop: '24px',
  },
  emptyTitle: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: '17px',
    fontWeight: '600',
    marginBottom: '8px',
  },
  emptyText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: '15px',
    margin: 0,
  },
};
