import { useState, useMemo } from 'react';
import { LogsTable } from '../components/LogsTable';
import { useEvents } from '../hooks/useSemanticCache';
import { LightRays } from '../components/LightRays';

type DecisionFilter = 'all' | 'exact' | 'semantic' | 'miss';

const FILTER_OPTIONS: { value: DecisionFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'exact', label: 'Exact' },
  { value: 'semantic', label: 'Semantic' },
  { value: 'miss', label: 'Miss' },
];

export function LogsPage() {
  const { events, isLoading, error, refetch } = useEvents(100, 10000);
  const [filter, setFilter] = useState<DecisionFilter>('all');

  const filteredEvents = useMemo(() => {
    if (filter === 'all') return events;
    return events.filter((event) => event.decision.includes(filter));
  }, [events, filter]);

  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Event Logs</h1>
            <p style={styles.subtitle}>
              View recent semantic cache decisions and performance data
            </p>
          </div>
          <button onClick={refetch} style={styles.refreshButton} disabled={isLoading}>
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {error && (
          <div style={styles.errorBanner}>
            Failed to load events. Please check your API key and try again.
          </div>
        )}

        <div style={styles.filterBar}>
          <span style={styles.filterLabel}>Filter by decision:</span>
          <div style={styles.filterGroup}>
            {FILTER_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setFilter(opt.value)}
                style={{
                  ...styles.filterButton,
                  ...(filter === opt.value ? styles.filterButtonActive : {}),
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <LogsTable events={filteredEvents} isLoading={isLoading} />
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
  filterBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '20px',
  },
  filterLabel: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    whiteSpace: 'nowrap',
  },
  filterGroup: {
    display: 'flex',
    gap: '8px',
  },
  filterButton: {
    padding: '6px 14px',
    fontSize: '13px',
    fontWeight: '500',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '6px',
    color: 'rgba(255, 255, 255, 0.6)',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  filterButtonActive: {
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid rgba(59, 130, 246, 0.4)',
    color: '#60a5fa',
  },
};
