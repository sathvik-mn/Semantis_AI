import { Metrics } from '../api/semanticAPI';

interface KpiCardsProps {
  metrics: Metrics | null;
  isLoading: boolean;
}

export function KpiCards({ metrics, isLoading }: KpiCardsProps) {
  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatNumber = (value: number) => {
    return value.toLocaleString();
  };

  const formatLatency = (value: number) => {
    return `${value.toFixed(0)}ms`;
  };

  const kpis = [
    {
      label: 'Hit Ratio',
      value: metrics ? formatPercentage(metrics.hit_ratio) : '--',
      description: 'Overall cache hit rate',
    },
    {
      label: 'Semantic Hit Ratio',
      value: metrics ? formatPercentage(metrics.semantic_hit_ratio) : '--',
      description: 'Semantic match rate',
    },
    {
      label: 'Avg Latency',
      value: metrics ? formatLatency(metrics.avg_latency_ms) : '--',
      description: 'Average response time',
    },
    {
      label: 'Total Requests',
      value: metrics ? formatNumber(metrics.total_requests) : '--',
      description: 'Total queries processed',
    },
    {
      label: 'Tokens Saved',
      value: metrics ? formatNumber(metrics.tokens_saved_est) : '--',
      description: 'Estimated tokens saved',
    },
  ];

  if (isLoading) {
    return (
      <div style={styles.grid}>
        {kpis.map((_kpi, index) => (
          <div key={index} style={styles.card}>
            <div style={styles.loading}></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div style={styles.grid}>
      {kpis.map((kpi, index) => (
        <div key={index} style={styles.card}>
          <div style={styles.label}>{kpi.label}</div>
          <div style={styles.value}>{kpi.value}</div>
          <div style={styles.description}>{kpi.description}</div>
        </div>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px',
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    backdropFilter: 'blur(10px)',
    transition: 'transform 0.2s, border-color 0.2s',
    cursor: 'default',
  },
  label: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: '8px',
    fontWeight: '500',
  },
  value: {
    fontSize: '32px',
    color: '#fff',
    fontWeight: '700',
    marginBottom: '4px',
  },
  description: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.4)',
  },
  loading: {
    width: '100%',
    height: '80px',
    background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
    animation: 'shimmer 1.5s infinite',
    borderRadius: '8px',
  },
};
