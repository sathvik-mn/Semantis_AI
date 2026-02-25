import { LightRays } from '../components/LightRays';

export function SecurityPage() {
  return (
    <div style={styles.container}>
      <LightRays />
      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Security Overview</h1>
          <p style={styles.subtitle}>
            How Semantis AI protects your data and API keys
          </p>
        </div>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Data Security</h2>
          <ul style={styles.list}>
            <li><strong>Encryption at rest:</strong> Cache entries and embeddings are stored with encryption where supported by the storage backend.</li>
            <li><strong>Encryption in transit:</strong> All API traffic uses HTTPS/TLS.</li>
            <li><strong>Tenant isolation:</strong> Data is strictly isolated by organization and API key. No cross-tenant access.</li>
            <li><strong>Minimal retention:</strong> Cache entries expire by TTL (default 7 days). You control retention via settings.</li>
          </ul>
        </section>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>API Key Security</h2>
          <ul style={styles.list}>
            <li><strong>Secure storage:</strong> API keys are hashed and stored in the database. Plaintext keys are shown only once at creation.</li>
            <li><strong>Scoped access:</strong> Keys can be scoped to read-only or read-write. Optional IP allowlists.</li>
            <li><strong>Rotation:</strong> Generate new keys and revoke old ones from Settings at any time.</li>
          </ul>
        </section>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Authentication</h2>
          <ul style={styles.list}>
            <li><strong>Supabase Auth:</strong> User authentication is handled by Supabase with secure session management.</li>
            <li><strong>JWT validation:</strong> Backend validates Supabase JWTs for all authenticated endpoints.</li>
            <li><strong>Organization membership:</strong> Access to org resources is enforced by role-based membership.</li>
          </ul>
        </section>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Compliance & Best Practices</h2>
          <ul style={styles.list}>
            <li><strong>Audit logs:</strong> Organization actions (API key creation, member changes) are logged for compliance.</li>
            <li><strong>BYOK (Bring Your Own Key):</strong> Enterprise plans support using your own OpenAI key; we never store or log it.</li>
            <li><strong>No training on your data:</strong> Your prompts and responses are not used for model training.</li>
          </ul>
        </section>

        <section style={styles.section}>
          <h2 style={styles.sectionTitle}>Reporting</h2>
          <p style={styles.text}>
            To report a security vulnerability, contact us at security@semantis.ai. We respond to valid reports promptly.
          </p>
        </section>
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
    maxWidth: '720px',
    margin: '0 auto',
    position: 'relative',
    zIndex: 1,
  },
  header: {
    marginBottom: '40px',
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
  section: {
    marginBottom: '32px',
  },
  sectionTitle: {
    fontSize: '20px',
    color: '#60a5fa',
    marginBottom: '12px',
    fontWeight: '600',
  },
  list: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.85)',
    lineHeight: '1.8',
    paddingLeft: '24px',
  },
  text: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.85)',
    lineHeight: '1.6',
  },
};
