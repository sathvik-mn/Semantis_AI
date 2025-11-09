import { Event } from '../api/semanticAPI';

interface LogsTableProps {
  events: Event[];
  isLoading: boolean;
}

export function LogsTable({ events, isLoading }: LogsTableProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getDecisionColor = (decision: string) => {
    if (decision.includes('exact')) return '#10b981';
    if (decision.includes('semantic')) return '#3b82f6';
    return '#f59e0b';
  };

  const downloadCSV = () => {
    const headers = ['Timestamp', 'Decision', 'Similarity', 'Latency (ms)', 'Prompt Hash'];
    const rows = events.map((event) => [
      event.timestamp,
      event.decision,
      event.similarity.toFixed(3),
      event.latency_ms.toFixed(0),
      event.prompt_hash,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `semantic-cache-logs-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading events...</div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>
          No events yet. Run some queries in the playground to see cache decisions here.
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Recent Events</h3>
        <button onClick={downloadCSV} style={styles.downloadButton}>
          Download CSV
        </button>
      </div>

      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Timestamp</th>
              <th style={styles.th}>Decision</th>
              <th style={styles.th}>Similarity</th>
              <th style={styles.th}>Latency</th>
              <th style={styles.th}>Prompt Hash</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event, index) => (
              <tr key={index} style={styles.tr}>
                <td style={styles.td}>{formatTimestamp(event.timestamp)}</td>
                <td style={styles.td}>
                  <span
                    style={{
                      ...styles.badge,
                      backgroundColor: getDecisionColor(event.decision),
                    }}
                  >
                    {event.decision}
                  </span>
                </td>
                <td style={styles.td}>{(event.similarity * 100).toFixed(1)}%</td>
                <td style={styles.td}>{event.latency_ms.toFixed(0)}ms</td>
                <td style={styles.tdHash}>{event.prompt_hash.substring(0, 16)}...</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    backdropFilter: 'blur(10px)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  title: {
    fontSize: '18px',
    color: '#fff',
    fontWeight: '600',
  },
  downloadButton: {
    padding: '8px 16px',
    fontSize: '14px',
    fontWeight: '500',
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid rgba(59, 130, 246, 0.4)',
    borderRadius: '6px',
    color: '#60a5fa',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    fontSize: '13px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.7)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  tr: {
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
    transition: 'background-color 0.2s',
  },
  td: {
    padding: '12px',
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.9)',
  },
  tdHash: {
    padding: '12px',
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.6)',
    fontFamily: 'monospace',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: '6px',
    fontSize: '12px',
    fontWeight: '600',
    color: '#fff',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  empty: {
    textAlign: 'center',
    padding: '40px',
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
};
