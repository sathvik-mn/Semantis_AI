import { KpiCards } from '../components/KpiCards';
import { useMetrics } from '../hooks/useSemanticCache';
import { LightRays } from '../components/LightRays';

export function MetricsPage() {
  const { metrics, isLoading } = useMetrics(15000);

  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Performance Metrics</h1>
          <p style={styles.subtitle}>
            Monitor your semantic cache performance and cost savings
          </p>
        </div>

        <KpiCards metrics={metrics} isLoading={isLoading} />

        {metrics && (
          <div style={styles.insightsSection}>
            <h2 style={styles.sectionTitle}>Insights</h2>

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

            <div style={styles.insightCard}>
              <h3 style={styles.insightTitle}>Semantic Matching</h3>
              <p style={styles.insightText}>
                {(metrics.semantic_hit_ratio * 100).toFixed(1)}% of your hits are from semantic
                matching, demonstrating the value of AI-powered caching beyond exact matches.
              </p>
            </div>

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

            <div style={styles.insightCard}>
              <h3 style={styles.insightTitle}>Cost Savings</h3>
              <p style={styles.insightText}>
                Approximately {metrics.tokens_saved_est.toLocaleString()} tokens saved through
                caching. Based on typical pricing, this translates to significant cost reduction
                over time.
              </p>
            </div>
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
};
