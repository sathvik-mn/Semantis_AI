import { SettingsPanel } from '../components/SettingsPanel';
import { BillingSection } from '../components/BillingSection';
import { LightRays } from '../components/LightRays';

export function SettingsPage() {
  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Settings</h1>
          <p style={styles.subtitle}>
            Configure cache behavior, billing, and performance parameters
          </p>
        </div>

        <BillingSection />
        <div style={{ height: '24px' }} />
        <SettingsPanel />
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
};
