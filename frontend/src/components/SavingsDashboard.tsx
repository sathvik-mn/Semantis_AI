import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/semanticAPI';

export function SavingsDashboard() {
  const [billing, setBilling] = useState<api.BillingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBilling = useCallback(async () => {
    try {
      setError(null);
      const data = await api.getBillingStatus();
      setBilling(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load savings');
      setBilling(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBilling();
  }, [fetchBilling]);

  if (isLoading) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>Cost Savings</h2>
        <div style={styles.loading}></div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>Cost Savings</h2>
        <div style={styles.error}>{error}</div>
      </div>
    );
  }

  const savings = billing?.savings_estimate;
  const total = savings?.total_requests ?? 0;
  const cached = savings?.cached_requests ?? 0;
  const savingsUsd = savings?.estimated_savings_usd ?? 0;
  const hitRate = total > 0 ? (cached / total) * 100 : 0;

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Cost Savings</h2>
      <p style={styles.subtitle}>
        Real cost estimates from your usage over the last 30 days
      </p>
      <div style={styles.grid}>
        <div style={styles.card}>
          <div style={styles.cardLabel}>Cached Requests</div>
          <div style={styles.cardValue}>{cached.toLocaleString()}</div>
          <div style={styles.cardDesc}>Requests served from cache</div>
        </div>
        <div style={styles.card}>
          <div style={styles.cardLabel}>Total Requests</div>
          <div style={styles.cardValue}>{total.toLocaleString()}</div>
          <div style={styles.cardDesc}>All requests in last 30 days</div>
        </div>
        <div style={styles.card}>
          <div style={styles.cardLabel}>Cache Hit Rate</div>
          <div style={styles.cardValue}>{hitRate.toFixed(1)}%</div>
          <div style={styles.cardDesc}>Share served from cache</div>
        </div>
        <div style={styles.cardHighlight}>
          <div style={styles.cardLabel}>Estimated Savings</div>
          <div style={styles.cardValue}>${savingsUsd.toFixed(2)}</div>
          <div style={styles.cardDesc}>Avoided LLM API costs (30 days)</div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginBottom: '40px',
  },
  title: {
    fontSize: '24px',
    color: '#fff',
    marginBottom: '8px',
    fontWeight: '600',
  },
  subtitle: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: '20px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '16px',
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '20px',
    backdropFilter: 'blur(10px)',
  },
  cardHighlight: {
    background: 'rgba(16, 185, 129, 0.15)',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    borderRadius: '12px',
    padding: '20px',
    backdropFilter: 'blur(10px)',
  },
  cardLabel: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
    marginBottom: '8px',
    fontWeight: '500',
  },
  cardValue: {
    fontSize: '28px',
    color: '#fff',
    fontWeight: '700',
    marginBottom: '4px',
  },
  cardDesc: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.4)',
  },
  loading: {
    width: '100%',
    height: '120px',
    background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
    animation: 'shimmer 1.5s infinite',
    borderRadius: '12px',
  },
  error: {
    padding: '16px',
    background: 'rgba(239, 68, 68, 0.15)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: '14px',
  },
};
