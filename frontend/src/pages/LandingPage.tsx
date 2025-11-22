import { Link } from 'react-router-dom';

export function LandingPage() {
  return (
    <div style={styles.pageContainer}>
      {/* Navigation */}
      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <div style={styles.logo}>Semantis AI</div>
          <div style={styles.navLinks}>
            <Link to="/docs" style={styles.navLink}>Docs</Link>
            <Link to="/pricing" style={styles.navLink}>Pricing</Link>
            <Link to="/playground" style={styles.navLink}>Playground</Link>
          </div>
          <div style={styles.navButtons}>
            <Link to="/signin" style={styles.signInBtn}>Sign In</Link>
            <Link to="/signup" style={styles.getStartedBtn}>Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={styles.hero}>
        <div style={styles.badge}>
          <span style={styles.badgeIcon}>✨</span>
          Intelligent Semantic Caching for LLMs
        </div>
        <h1 style={styles.heroTitle}>
          Cut Your LLM Costs
          <br />
          <span style={styles.heroGradient}>By Up To 80%</span>
        </h1>
        <p style={styles.heroSubtitle}>
          Semantis AI is an intelligent caching layer that sits between your application and LLM providers,
          reducing costs and latency by serving cached responses for semantically similar queries.
        </p>
        <div style={styles.heroButtons}>
          <Link to="/signup" style={styles.primaryBtn}>
            Start Saving Now →
          </Link>
          <Link to="/docs" style={styles.secondaryBtn}>
            📖 View Documentation
          </Link>
        </div>

        {/* Stats */}
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>80%</div>
            <div style={styles.statLabel}>Cost Reduction</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>&lt;50ms</div>
            <div style={styles.statLabel}>Cache Response Time</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>100%</div>
            <div style={styles.statLabel}>LLM Compatible</div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>How It Works</h2>
        <p style={styles.sectionSubtitle}>Simple, fast, and transparent caching</p>

        <div style={styles.flowGrid}>
          <div style={styles.flowCard}>
            <div style={styles.flowIcon}>🚀</div>
            <h3 style={styles.flowTitle}>Your App Sends Query</h3>
            <p style={styles.flowText}>Your application makes an LLM request through Semantis AI</p>
          </div>

          <div style={{...styles.flowCard, ...styles.flowCardHighlight}}>
            <div style={styles.flowIcon}>⚡</div>
            <h3 style={styles.flowTitle}>Semantis Checks Cache</h3>
            <p style={styles.flowText}>We analyze semantic similarity against cached responses</p>
          </div>

          <div style={styles.flowCard}>
            <div style={styles.flowIcon}>✓</div>
            <h3 style={styles.flowTitle}>Instant Response</h3>
            <p style={styles.flowText}>Return cached result or fetch from LLM and cache it</p>
          </div>
        </div>

        <div style={styles.stepsContainer}>
          <div style={styles.stepRow}>
            <div style={styles.stepNumber}>1</div>
            <div style={styles.stepContent}>
              <h4 style={styles.stepTitle}>Query Received</h4>
              <p style={styles.stepText}>Your application sends an LLM query to our API endpoint</p>
            </div>
          </div>

          <div style={styles.stepRow}>
            <div style={styles.stepNumber}>2</div>
            <div style={styles.stepContent}>
              <h4 style={styles.stepTitle}>Semantic Analysis</h4>
              <p style={styles.stepText}>Advanced algorithms check for semantically similar cached queries</p>
            </div>
          </div>

          <div style={styles.stepRow}>
            <div style={styles.stepNumber}>3</div>
            <div style={styles.stepContent}>
              <h4 style={styles.stepTitle}>Cache Hit</h4>
              <p style={styles.stepText}>Return instant cached response, saving time and money</p>
            </div>
          </div>

          <div style={styles.stepRow}>
            <div style={styles.stepNumber}>4</div>
            <div style={styles.stepContent}>
              <h4 style={styles.stepTitle}>Cache Miss</h4>
              <p style={styles.stepText}>Forward to LLM provider and cache response for future queries</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={styles.featuresSection}>
        <h2 style={styles.sectionTitle}>Why Choose Semantis AI?</h2>
        <p style={styles.sectionSubtitle}>Built for modern AI applications</p>

        <div style={styles.featuresGrid}>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>📉</div>
            <h3 style={styles.featureTitle}>Massive Savings</h3>
            <p style={styles.featureText}>Reduce LLM API costs by 60-80% with intelligent caching</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>⚡</div>
            <h3 style={styles.featureTitle}>Lightning Fast</h3>
            <p style={styles.featureText}>Cache hits return in milliseconds, not seconds</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🔌</div>
            <h3 style={styles.featureTitle}>Plug & Play</h3>
            <p style={styles.featureText}>Integrate with just a few lines of code via our SDK</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🌐</div>
            <h3 style={styles.featureTitle}>Universal</h3>
            <p style={styles.featureText}>Works with OpenAI, Anthropic, Cohere, and more</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🛡️</div>
            <h3 style={styles.featureTitle}>Enterprise Ready</h3>
            <p style={styles.featureText}>Secure, scalable, and built for production workloads</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🎯</div>
            <h3 style={styles.featureTitle}>Smart Matching</h3>
            <p style={styles.featureText}>Advanced semantic similarity algorithms with typo tolerance</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>👨‍💻</div>
            <h3 style={styles.featureTitle}>Developer First</h3>
            <p style={styles.featureText}>Comprehensive docs, SDKs, and amazing developer experience</p>
          </div>

          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>📊</div>
            <h3 style={styles.featureTitle}>Real-time Analytics</h3>
            <p style={styles.featureText}>Track cache performance, costs, and usage in real-time</p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Start in Minutes</h2>
        <p style={styles.sectionSubtitle}>Simple integration with any tech stack</p>

        <div style={styles.codeContainer}>
          <div style={styles.codeHeader}>
            <div style={styles.codeButtons}>
              <span style={{...styles.codeDot, background: '#ff5f56'}}></span>
              <span style={{...styles.codeDot, background: '#ffbd2e'}}></span>
              <span style={{...styles.codeDot, background: '#27c93f'}}></span>
            </div>
            <span style={styles.codeLabel}>Python</span>
          </div>
          <pre style={styles.codeBlock}>
            <code style={styles.code}>{`from semantis_ai import SemantisClient

# Initialize client
client = SemantisClient(api_key="your_api_key")

# Make cached LLM call
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content)  # Lightning fast response!`}</code>
          </pre>
        </div>
      </section>

      {/* CTA */}
      <section style={styles.ctaSection}>
        <div style={styles.ctaContainer}>
          <h2 style={styles.ctaTitle}>Ready to Save on LLM Costs?</h2>
          <p style={styles.ctaSubtitle}>
            Join developers saving thousands on AI infrastructure costs every month.
          </p>
          <Link to="/signup" style={styles.ctaButton}>
            Get Started Free →
          </Link>
          <p style={styles.ctaFootnote}>No credit card required • Free tier available</p>
        </div>
      </section>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.footerContent}>
          <div style={styles.footerColumn}>
            <div style={styles.footerLogo}>Semantis AI</div>
            <p style={styles.footerDescription}>
              Intelligent semantic caching for modern AI applications.
            </p>
          </div>

          <div style={styles.footerColumn}>
            <h4 style={styles.footerHeading}>Product</h4>
            <Link to="/docs" style={styles.footerLink}>Documentation</Link>
            <Link to="/playground" style={styles.footerLink}>Playground</Link>
            <Link to="/pricing" style={styles.footerLink}>Pricing</Link>
          </div>

          <div style={styles.footerColumn}>
            <h4 style={styles.footerHeading}>Resources</h4>
            <a href="https://github.com" style={styles.footerLink} target="_blank" rel="noopener noreferrer">GitHub</a>
            <Link to="/docs" style={styles.footerLink}>API Reference</Link>
            <Link to="/docs" style={styles.footerLink}>Guides</Link>
          </div>

          <div style={styles.footerColumn}>
            <h4 style={styles.footerHeading}>Company</h4>
            <a href="mailto:contact@semantis.ai" style={styles.footerLink}>Contact</a>
            <Link to="/privacy" style={styles.footerLink}>Privacy</Link>
            <Link to="/terms" style={styles.footerLink}>Terms</Link>
          </div>
        </div>

        <div style={styles.footerBottom}>
          <p style={styles.copyright}>© 2025 Semantis AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  pageContainer: {
    minHeight: '100vh',
    background: 'linear-gradient(to bottom, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
  },

  // Navigation
  nav: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 100,
    background: 'rgba(15, 23, 42, 0.8)',
    backdropFilter: 'blur(20px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  navContent: {
    maxWidth: '1280px',
    margin: '0 auto',
    padding: '16px 32px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: '24px',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  navLinks: {
    display: 'flex',
    gap: '32px',
  },
  navLink: {
    color: 'rgba(255, 255, 255, 0.7)',
    textDecoration: 'none',
    fontSize: '15px',
    fontWeight: '500',
    transition: 'color 0.2s',
  },
  navButtons: {
    display: 'flex',
    gap: '12px',
  },
  signInBtn: {
    padding: '10px 24px',
    fontSize: '15px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
    textDecoration: 'none',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    background: 'rgba(255, 255, 255, 0.05)',
    transition: 'all 0.2s',
  },
  getStartedBtn: {
    padding: '10px 24px',
    fontSize: '15px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '8px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
    transition: 'all 0.2s',
  },

  // Hero
  hero: {
    paddingTop: '160px',
    paddingBottom: '100px',
    textAlign: 'center',
    maxWidth: '1100px',
    margin: '0 auto',
    padding: '160px 32px 100px',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 20px',
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '999px',
    color: '#60a5fa',
    fontSize: '14px',
    fontWeight: '500',
    marginBottom: '32px',
  },
  badgeIcon: {
    fontSize: '16px',
  },
  heroTitle: {
    fontSize: '64px',
    fontWeight: '800',
    color: '#fff',
    marginBottom: '24px',
    lineHeight: '1.1',
    letterSpacing: '-0.02em',
  },
  heroGradient: {
    background: 'linear-gradient(135deg, #3b82f6, #06b6d4, #14b8a6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  heroSubtitle: {
    fontSize: '20px',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '40px',
    lineHeight: '1.6',
    maxWidth: '800px',
    margin: '0 auto 40px',
  },
  heroButtons: {
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
    marginBottom: '80px',
    flexWrap: 'wrap',
  },
  primaryBtn: {
    padding: '16px 32px',
    fontSize: '18px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
    transition: 'all 0.2s',
  },
  secondaryBtn: {
    padding: '16px 32px',
    fontSize: '18px',
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
    textDecoration: 'none',
    borderRadius: '12px',
    border: '2px solid rgba(255, 255, 255, 0.2)',
    background: 'rgba(255, 255, 255, 0.05)',
    transition: 'all 0.2s',
  },

  // Stats
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '24px',
    maxWidth: '900px',
    margin: '0 auto',
  },
  statCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
  },
  statNumber: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#3b82f6',
    marginBottom: '8px',
  },
  statLabel: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.7)',
  },

  // Section
  section: {
    padding: '100px 32px',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  sectionTitle: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
    marginBottom: '16px',
  },
  sectionSubtitle: {
    fontSize: '20px',
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    marginBottom: '64px',
  },

  // Flow
  flowGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '24px',
    marginBottom: '64px',
  },
  flowCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
    textAlign: 'center',
  },
  flowCardHighlight: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
  },
  flowIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  flowTitle: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '12px',
  },
  flowText: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: '1.6',
  },

  // Steps
  stepsContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '32px',
  },
  stepRow: {
    display: 'flex',
    gap: '16px',
  },
  stepNumber: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    fontWeight: '700',
    flexShrink: 0,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '8px',
  },
  stepText: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: '1.5',
  },

  // Features
  featuresSection: {
    padding: '100px 32px',
    maxWidth: '1200px',
    margin: '0 auto',
    background: 'rgba(0, 0, 0, 0.2)',
  },
  featuresGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '24px',
  },
  featureCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
    transition: 'all 0.3s',
  },
  featureIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  featureTitle: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '12px',
  },
  featureText: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: '1.6',
  },

  // Code
  codeContainer: {
    maxWidth: '900px',
    margin: '0 auto',
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    overflow: 'hidden',
  },
  codeHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 24px',
    background: 'rgba(0, 0, 0, 0.2)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  codeButtons: {
    display: 'flex',
    gap: '8px',
  },
  codeDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
  },
  codeLabel: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  codeBlock: {
    padding: '24px',
    margin: 0,
    overflow: 'auto',
  },
  code: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '14px',
    lineHeight: '1.6',
    fontFamily: 'monospace',
  },

  // CTA
  ctaSection: {
    padding: '120px 32px',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  ctaContainer: {
    background: 'rgba(59, 130, 246, 0.1)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '24px',
    padding: '80px 40px',
    textAlign: 'center',
  },
  ctaTitle: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '16px',
    lineHeight: '1.2',
  },
  ctaSubtitle: {
    fontSize: '20px',
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: '32px',
  },
  ctaButton: {
    display: 'inline-block',
    padding: '18px 40px',
    fontSize: '18px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
    transition: 'all 0.2s',
  },
  ctaFootnote: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
    marginTop: '16px',
  },

  // Footer
  footer: {
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '60px 32px 32px',
  },
  footerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '40px',
    marginBottom: '40px',
  },
  footerColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  footerLogo: {
    fontSize: '20px',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
    marginBottom: '8px',
  },
  footerDescription: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
    lineHeight: '1.6',
  },
  footerHeading: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '8px',
  },
  footerLink: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    textDecoration: 'none',
    transition: 'color 0.2s',
  },
  footerBottom: {
    maxWidth: '1200px',
    margin: '0 auto',
    paddingTop: '32px',
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    textAlign: 'center',
  },
  copyright: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
};
