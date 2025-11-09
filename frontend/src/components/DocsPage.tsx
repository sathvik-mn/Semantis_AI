import { useState } from 'react';
import * as api from '../api/semanticAPI';

export function DocsPage() {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  const apiKey = api.hasApiKey()
    ? localStorage.getItem('semantic_api_key') || 'YOUR_API_KEY'
    : 'YOUR_API_KEY';

  const copyToClipboard = (text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const pythonExample = `from semantis import Client

client = Client(api_key="${apiKey}")
response = client.chat("Explain reinforcement learning")
print(response.text, response.meta)`;

  const nodeExample = `import { Semantis } from "semantis";

const client = new Semantis("${apiKey}");
const res = await client.chat("Explain embeddings");
console.log(res.text, res.meta);`;

  const curlExample = `curl -X POST http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${apiKey}" \\
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Explain semantic caching"}
    ],
    "temperature": 0.2
  }'`;

  return (
    <div style={styles.container}>
      <div style={styles.hero}>
        <h1 style={styles.heroTitle}>Integration Documentation</h1>
        <p style={styles.heroSubtitle}>
          Get started with Semantis AI in minutes. Copy the code snippets below to integrate
          semantic caching into your application.
        </p>
      </div>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Quick Start</h2>
        <p style={styles.text}>
          Semantis AI provides a drop-in replacement for your existing LLM API calls. Simply wrap
          your requests with our SDK to automatically benefit from semantic caching.
        </p>

        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <h3 style={styles.cardTitle}>Python</h3>
            <button
              onClick={() => copyToClipboard(pythonExample, 'python')}
              style={styles.copyButton}
            >
              {copiedSection === 'python' ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre style={styles.code}>{pythonExample}</pre>
        </div>

        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <h3 style={styles.cardTitle}>Node.js / TypeScript</h3>
            <button
              onClick={() => copyToClipboard(nodeExample, 'node')}
              style={styles.copyButton}
            >
              {copiedSection === 'node' ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre style={styles.code}>{nodeExample}</pre>
        </div>

        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <h3 style={styles.cardTitle}>cURL</h3>
            <button onClick={() => copyToClipboard(curlExample, 'curl')} style={styles.copyButton}>
              {copiedSection === 'curl' ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre style={styles.code}>{curlExample}</pre>
        </div>
      </section>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Understanding the Response</h2>
        <p style={styles.text}>
          Every response includes metadata about the cache decision:
        </p>
        <ul style={styles.list}>
          <li>
            <strong>hit:</strong> "exact" (identical match), "semantic" (similar match), or "miss"
            (no match)
          </li>
          <li>
            <strong>similarity:</strong> Cosine similarity score between 0 and 1
          </li>
          <li>
            <strong>latency_ms:</strong> Response time in milliseconds
          </li>
          <li>
            <strong>strategy:</strong> Caching strategy used (hybrid, exact, semantic)
          </li>
        </ul>
      </section>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Configuration</h2>
        <div style={styles.configGrid}>
          <div style={styles.configCard}>
            <h4 style={styles.configTitle}>Similarity Threshold</h4>
            <p style={styles.configText}>
              Control how strict semantic matching should be. Default is 0.83. Higher values
              require closer matches.
            </p>
          </div>
          <div style={styles.configCard}>
            <h4 style={styles.configTitle}>TTL</h4>
            <p style={styles.configText}>
              Cache entries expire after 7 days by default. Popular entries are automatically
              extended to 30 days.
            </p>
          </div>
          <div style={styles.configCard}>
            <h4 style={styles.configTitle}>Models</h4>
            <p style={styles.configText}>
              Supports OpenAI models: gpt-4, gpt-4o-mini, gpt-3.5-turbo. Each model maintains a
              separate cache namespace.
            </p>
          </div>
        </div>
      </section>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Best Practices</h2>
        <div style={styles.tipBox}>
          <p style={styles.tipText}>
            Start with the default threshold (0.83) and adjust based on your hit ratio and quality
            requirements.
          </p>
          <p style={styles.tipText}>
            Monitor your semantic hit ratio in the Metrics dashboard to optimize cache
            effectiveness.
          </p>
          <p style={styles.tipText}>
            Use consistent temperature values for better cache utilization across similar queries.
          </p>
        </div>
      </section>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '900px',
    margin: '0 auto',
  },
  hero: {
    textAlign: 'center',
    marginBottom: '48px',
  },
  heroTitle: {
    fontSize: '36px',
    color: '#fff',
    marginBottom: '16px',
    fontWeight: '700',
  },
  heroSubtitle: {
    fontSize: '18px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.6',
    maxWidth: '700px',
    margin: '0 auto',
  },
  section: {
    marginBottom: '48px',
  },
  sectionTitle: {
    fontSize: '24px',
    color: '#fff',
    marginBottom: '16px',
    fontWeight: '600',
  },
  text: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.6',
    marginBottom: '24px',
  },
  card: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '20px',
    backdropFilter: 'blur(10px)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  cardTitle: {
    fontSize: '16px',
    color: '#fff',
    fontWeight: '600',
  },
  copyButton: {
    padding: '6px 16px',
    fontSize: '13px',
    fontWeight: '500',
    background: 'rgba(59, 130, 246, 0.2)',
    border: '1px solid rgba(59, 130, 246, 0.4)',
    borderRadius: '6px',
    color: '#60a5fa',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  code: {
    fontSize: '14px',
    color: '#e5e7eb',
    background: 'rgba(0, 0, 0, 0.4)',
    padding: '16px',
    borderRadius: '8px',
    overflowX: 'auto',
    lineHeight: '1.5',
    fontFamily: 'monospace',
  },
  list: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.8',
    paddingLeft: '24px',
  },
  configGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '16px',
    marginTop: '20px',
  },
  configCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    padding: '16px',
  },
  configTitle: {
    fontSize: '15px',
    color: '#60a5fa',
    marginBottom: '8px',
    fontWeight: '600',
  },
  configText: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.5',
  },
  tipBox: {
    background: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
    borderRadius: '8px',
    padding: '20px',
    marginTop: '20px',
  },
  tipText: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.6',
    marginBottom: '12px',
  },
};
