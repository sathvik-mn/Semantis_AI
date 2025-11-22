import { Link } from 'react-router-dom';
import { Prism } from '../components/Prism';
import { ArrowLeft, Zap, Shield, Layers, TrendingDown, Clock, CheckCircle } from 'lucide-react';

export function LandingPage() {
  return (
    <div style={styles.container}>
      <Prism />

      {/* Header / Navbar */}
      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <div style={styles.leftNav}>
            <Link to="/" style={styles.backButton}>
              <ArrowLeft size={18} />
            </Link>
            <div style={styles.logo}>
              <span style={styles.logoText}>Semantis AI</span>
            </div>
            <div style={styles.navLinks}>
              <Link to="/" style={styles.navLink}>Home</Link>
              <Link to="/playground" style={styles.navLink}>Playground</Link>
              <Link to="/docs" style={styles.navLink}>Docs</Link>
              <Link to="/pricing" style={styles.navLink}>Pricing</Link>
            </div>
          </div>
          <div style={styles.authButtons}>
            <Link to="/signin" style={styles.signInButton}>Sign In</Link>
            <Link to="/signup" style={styles.signUpButton}>Sign Up</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={styles.heroSection}>
        <div style={styles.heroContent}>
          <h1 style={styles.heroTitle}>
            Semantis AI – The Semantic Cache Layer for AI Systems
          </h1>
          <p style={styles.heroSubtext}>
            Reduce your LLM cost by up to 80% using intelligent semantic caching.
          </p>
          <div style={styles.heroButtons}>
            <Link to="/signup" style={styles.ctaButton}>
              Get Started
            </Link>
            <Link to="/docs" style={styles.docsButton}>
              Read Docs
            </Link>
          </div>
        </div>
      </section>

      {/* What is Semantis AI Section */}
      <section style={styles.section}>
        <div style={styles.sectionContent}>
          <h2 style={styles.sectionTitle}>What is Semantis AI?</h2>
          <div style={styles.tilesGrid}>
            <div style={styles.tile}>
              <div style={styles.tileIcon}>
                <Layers size={32} color="#3b82f6" />
              </div>
              <h3 style={styles.tileTitle}>What is Semantis AI?</h3>
              <p style={styles.tileText}>
                A middleware semantic cache layer sitting between your application and LLM, intelligently caching responses based on semantic similarity.
              </p>
            </div>

            <div style={styles.tile}>
              <div style={styles.tileIcon}>
                <TrendingDown size={32} color="#10b981" />
              </div>
              <h3 style={styles.tileTitle}>How it Saves Cost</h3>
              <p style={styles.tileText}>
                Repeated or similar questions reuse previous responses, eliminating redundant API calls and reducing token consumption by 60-80%.
              </p>
            </div>

            <div style={styles.tile}>
              <div style={styles.tileIcon}>
                <Shield size={32} color="#8b5cf6" />
              </div>
              <h3 style={styles.tileTitle}>How We're Different</h3>
              <p style={styles.tileText}>
                Not a vector DB. Not a prompt store. We sit in the middle of your LLM infrastructure as an intelligent caching layer.
              </p>
            </div>

            <div style={styles.tile}>
              <div style={styles.tileIcon}>
                <CheckCircle size={32} color="#f59e0b" />
              </div>
              <h3 style={styles.tileTitle}>AI Infrastructure Layer</h3>
              <p style={styles.tileText}>
                We become an infrastructure layer for all AI applications, seamlessly integrating with any LLM provider.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section style={styles.section}>
        <div style={styles.sectionContent}>
          <h2 style={styles.sectionTitle}>How It Works</h2>
          <div style={styles.flowDiagram}>
            <div style={styles.flowBox}>
              <div style={styles.flowIcon}>🚀</div>
              <div style={styles.flowTitle}>Your App</div>
              <div style={styles.flowDescription}>Sends LLM Query</div>
            </div>

            <div style={styles.flowArrow}>→</div>

            <div style={{...styles.flowBox, ...styles.flowBoxHighlight}}>
              <div style={styles.flowIcon}>⚡</div>
              <div style={styles.flowTitle}>Semantis AI</div>
              <div style={styles.flowDescription}>Checks Similarity</div>
            </div>

            <div style={styles.flowArrow}>→</div>

            <div style={styles.flowBox}>
              <div style={styles.flowIcon}>🤖</div>
              <div style={styles.flowTitle}>LLM Provider</div>
              <div style={styles.flowDescription}>If Cache Miss</div>
            </div>
          </div>

          <div style={styles.flowSteps}>
            <div style={styles.step}>
              <div style={styles.stepNumber}>1</div>
              <div style={styles.stepContent}>
                <h4 style={styles.stepTitle}>Developer sends LLM query</h4>
                <p style={styles.stepText}>Your application makes a request to Semantis AI</p>
              </div>
            </div>

            <div style={styles.step}>
              <div style={styles.stepNumber}>2</div>
              <div style={styles.stepContent}>
                <h4 style={styles.stepTitle}>We check semantic similarity</h4>
                <p style={styles.stepText}>Advanced algorithms determine if a similar query was cached</p>
              </div>
            </div>

            <div style={styles.step}>
              <div style={styles.stepNumber}>3</div>
              <div style={styles.stepContent}>
                <h4 style={styles.stepTitle}>If hit → return cached</h4>
                <p style={styles.stepText}>Instant response from cache, saving time and money</p>
              </div>
            </div>

            <div style={styles.step}>
              <div style={styles.stepNumber}>4</div>
              <div style={styles.stepContent}>
                <h4 style={styles.stepTitle}>If miss → call LLM & store</h4>
                <p style={styles.stepText}>Forward to LLM provider and cache the response for future use</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Semantis AI Section */}
      <section style={styles.section}>
        <div style={styles.sectionContent}>
          <h2 style={styles.sectionTitle}>Why Choose Semantis AI?</h2>
          <div style={styles.benefitsGrid}>
            <div style={styles.benefitCard}>
              <TrendingDown size={40} style={styles.benefitIcon} />
              <h3 style={styles.benefitTitle}>60-80% Cost Reduction</h3>
              <p style={styles.benefitText}>
                Dramatically reduce your LLM API costs by eliminating redundant calls
              </p>
            </div>

            <div style={styles.benefitCard}>
              <Clock size={40} style={styles.benefitIcon} />
              <h3 style={styles.benefitTitle}>Faster Response Time</h3>
              <p style={styles.benefitText}>
                Cache hits return in milliseconds instead of seconds
              </p>
            </div>

            <div style={styles.benefitCard}>
              <Zap size={40} style={styles.benefitIcon} />
              <h3 style={styles.benefitTitle}>Plug & Play SDK</h3>
              <p style={styles.benefitText}>
                Easy integration with just a few lines of code
              </p>
            </div>

            <div style={styles.benefitCard}>
              <Layers size={40} style={styles.benefitIcon} />
              <h3 style={styles.benefitTitle}>Works with All LLMs</h3>
              <p style={styles.benefitText}>
                Compatible with OpenAI, Anthropic, Cohere, and more
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section style={styles.ctaSection}>
        <div style={styles.ctaSectionContent}>
          <h2 style={styles.ctaSectionTitle}>
            Stop burning money on repeated LLM calls.
          </h2>
          <p style={styles.ctaSectionText}>
            Join hundreds of developers saving thousands on their AI infrastructure costs.
          </p>
          <Link to="/signup" style={styles.ctaSectionButton}>
            Get Started - Generate API Key
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.footerContent}>
          <div style={styles.footerSection}>
            <h4 style={styles.footerTitle}>Product</h4>
            <Link to="/docs" style={styles.footerLink}>Docs</Link>
            <Link to="/playground" style={styles.footerLink}>Playground</Link>
            <Link to="/pricing" style={styles.footerLink}>Pricing</Link>
          </div>

          <div style={styles.footerSection}>
            <h4 style={styles.footerTitle}>Resources</h4>
            <a href="https://github.com" style={styles.footerLink} target="_blank" rel="noopener noreferrer">GitHub</a>
            <Link to="/docs" style={styles.footerLink}>API Reference</Link>
          </div>

          <div style={styles.footerSection}>
            <h4 style={styles.footerTitle}>Company</h4>
            <a href="mailto:contact@semantis.ai" style={styles.footerLink}>Contact</a>
            <Link to="/careers" style={styles.footerLink}>Careers</Link>
          </div>

          <div style={styles.footerSection}>
            <h4 style={styles.footerTitle}>Legal</h4>
            <Link to="/privacy" style={styles.footerLink}>Privacy</Link>
            <Link to="/terms" style={styles.footerLink}>Terms</Link>
          </div>
        </div>

        <div style={styles.footerBottom}>
          <p style={styles.footerCopyright}>
            © 2025 Semantis AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    position: 'relative',
    background: '#000',
  },

  // Navigation
  nav: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 100,
    background: 'rgba(0, 0, 0, 0.8)',
    backdropFilter: 'blur(20px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  },
  navContent: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '16px 32px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  leftNav: {
    display: 'flex',
    alignItems: 'center',
    gap: '32px',
  },
  backButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '8px',
    color: 'rgba(255, 255, 255, 0.7)',
    textDecoration: 'none',
    borderRadius: '6px',
    transition: 'all 0.2s',
    background: 'rgba(255, 255, 255, 0.05)',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
  },
  logoText: {
    fontSize: '22px',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  navLinks: {
    display: 'flex',
    gap: '8px',
  },
  navLink: {
    color: 'rgba(255, 255, 255, 0.7)',
    textDecoration: 'none',
    fontSize: '15px',
    fontWeight: '500',
    padding: '8px 16px',
    borderRadius: '6px',
    transition: 'all 0.2s',
  },
  authButtons: {
    display: 'flex',
    gap: '12px',
  },
  signInButton: {
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
  signUpButton: {
    padding: '10px 24px',
    fontSize: '15px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '8px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    transition: 'all 0.2s',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
  },

  // Hero Section
  heroSection: {
    paddingTop: '160px',
    paddingBottom: '120px',
    position: 'relative',
    zIndex: 1,
  },
  heroContent: {
    maxWidth: '900px',
    margin: '0 auto',
    textAlign: 'center',
    padding: '0 32px',
  },
  heroTitle: {
    fontSize: '64px',
    fontWeight: '800',
    color: '#fff',
    marginBottom: '24px',
    lineHeight: '1.1',
    letterSpacing: '-0.02em',
  },
  heroSubtext: {
    fontSize: '24px',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '48px',
    lineHeight: '1.5',
  },
  heroButtons: {
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
  },
  ctaButton: {
    padding: '16px 32px',
    fontSize: '18px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    transition: 'all 0.2s',
    boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
  },
  docsButton: {
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

  // Section Styles
  section: {
    padding: '100px 32px',
    position: 'relative',
    zIndex: 1,
  },
  sectionContent: {
    maxWidth: '1200px',
    margin: '0 auto',
  },
  sectionTitle: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '64px',
    textAlign: 'center',
  },

  // Tiles Grid
  tilesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '24px',
  },
  tile: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
    backdropFilter: 'blur(20px)',
    transition: 'all 0.3s',
  },
  tileIcon: {
    marginBottom: '20px',
  },
  tileTitle: {
    fontSize: '22px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '12px',
  },
  tileText: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.6',
  },

  // Flow Diagram
  flowDiagram: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '24px',
    marginBottom: '64px',
    flexWrap: 'wrap',
  },
  flowBox: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    padding: '24px',
    minWidth: '200px',
    textAlign: 'center',
  },
  flowBoxHighlight: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
  },
  flowIcon: {
    fontSize: '40px',
    marginBottom: '12px',
  },
  flowTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '8px',
  },
  flowDescription: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
  },
  flowArrow: {
    fontSize: '32px',
    color: 'rgba(255, 255, 255, 0.4)',
    fontWeight: 'bold',
  },

  // Flow Steps
  flowSteps: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '24px',
  },
  step: {
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

  // Benefits Grid
  benefitsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '24px',
  },
  benefitCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
    textAlign: 'center',
    transition: 'all 0.3s',
  },
  benefitIcon: {
    color: '#3b82f6',
    marginBottom: '20px',
  },
  benefitTitle: {
    fontSize: '22px',
    fontWeight: '600',
    color: '#fff',
    marginBottom: '12px',
  },
  benefitText: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.6',
  },

  // CTA Section
  ctaSection: {
    padding: '120px 32px',
    position: 'relative',
    zIndex: 1,
  },
  ctaSectionContent: {
    maxWidth: '800px',
    margin: '0 auto',
    textAlign: 'center',
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '24px',
    padding: '80px 40px',
    backdropFilter: 'blur(20px)',
  },
  ctaSectionTitle: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '24px',
    lineHeight: '1.2',
  },
  ctaSectionText: {
    fontSize: '20px',
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: '40px',
  },
  ctaSectionButton: {
    display: 'inline-block',
    padding: '18px 40px',
    fontSize: '18px',
    fontWeight: '600',
    color: '#fff',
    textDecoration: 'none',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    transition: 'all 0.2s',
    boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)',
  },

  // Footer
  footer: {
    borderTop: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '60px 32px 32px',
    position: 'relative',
    zIndex: 1,
  },
  footerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '40px',
    marginBottom: '40px',
  },
  footerSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  footerTitle: {
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
  footerCopyright: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
};
