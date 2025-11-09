import { QueryPlayground } from '../components/QueryPlayground';
import { useMetrics, useEvents } from '../hooks/useSemanticCache';
import { LightRays } from '../components/LightRays';

export function PlaygroundPage() {
  const { metrics, refetch: refetchMetrics } = useMetrics();
  const { events, refetch: refetchEvents } = useEvents(10);

  const handleQueryComplete = () => {
    refetchMetrics();
    refetchEvents();
  };

  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Query Playground</h1>
          <p style={styles.subtitle}>
            Test LLM queries and see semantic caching in action
          </p>
        </div>

        <QueryPlayground onQueryComplete={handleQueryComplete} />

        {metrics && (
          <div style={styles.quickStats}>
            <h3 style={styles.statsTitle}>Quick Stats</h3>
            <div style={styles.statsGrid}>
              <div style={styles.stat}>
                <span style={styles.statLabel}>Hit Ratio:</span>
                <span style={styles.statValue}>{(metrics.hit_ratio * 100).toFixed(1)}%</span>
              </div>
              <div style={styles.stat}>
                <span style={styles.statLabel}>Avg Latency:</span>
                <span style={styles.statValue}>{metrics.avg_latency_ms.toFixed(0)}ms</span>
              </div>
              <div style={styles.stat}>
                <span style={styles.statLabel}>Total Requests:</span>
                <span style={styles.statValue}>{metrics.total_requests}</span>
              </div>
            </div>
          </div>
        )}

        {events.length > 0 && (
          <div style={styles.recentActivity}>
            <h3 style={styles.activityTitle}>Recent Activity</h3>
            <div style={styles.eventList}>
              {events.slice(0, 5).map((event, index) => (
                <div key={index} style={styles.event}>
                  <span style={styles.eventDecision}>{event.decision}</span>
                  <span style={styles.eventDetails}>
                    Similarity: {(event.similarity * 100).toFixed(1)}% | Latency:{' '}
                    {event.latency_ms.toFixed(0)}ms
                  </span>
                </div>
              ))}
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
    maxWidth: '900px',
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
  quickStats: {
    marginTop: '32px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '20px',
    backdropFilter: 'blur(10px)',
  },
  statsTitle: {
    fontSize: '16px',
    color: '#fff',
    marginBottom: '16px',
    fontWeight: '600',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  statLabel: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  statValue: {
    fontSize: '18px',
    color: '#60a5fa',
    fontWeight: '600',
  },
  recentActivity: {
    marginTop: '32px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '20px',
    backdropFilter: 'blur(10px)',
  },
  activityTitle: {
    fontSize: '16px',
    color: '#fff',
    marginBottom: '16px',
    fontWeight: '600',
  },
  eventList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  event: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px',
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '6px',
    fontSize: '13px',
  },
  eventDecision: {
    color: '#60a5fa',
    fontWeight: '600',
  },
  eventDetails: {
    color: 'rgba(255, 255, 255, 0.6)',
  },
};
