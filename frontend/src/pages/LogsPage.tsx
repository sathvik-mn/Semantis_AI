import { LogsTable } from '../components/LogsTable';
import { useEvents } from '../hooks/useSemanticCache';
import { LightRays } from '../components/LightRays';

export function LogsPage() {
  const { events, isLoading } = useEvents(100, 10000);

  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Event Logs</h1>
          <p style={styles.subtitle}>
            View recent semantic cache decisions and performance data
          </p>
        </div>

        <LogsTable events={events} isLoading={isLoading} />
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
};
