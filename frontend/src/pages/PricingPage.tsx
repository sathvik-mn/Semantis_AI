import { Link } from 'react-router-dom';
import { Check, ArrowRight, Mail } from 'lucide-react';
import { Prism } from '../components/Prism';

interface PricingTier {
  name: string;
  price: string;
  description: string;
  features: string[];
  cta: string;
  ctaLink: string;
  popular?: boolean;
}

export function PricingPage() {
  const tiers: PricingTier[] = [
    {
      name: 'Free',
      price: '$0',
      description: 'Perfect for trying out Semantis AI',
      features: [
        'Free for 1 month',
        '10,000 API requests/month',
        '100K tokens included',
        'Basic semantic caching',
        'Community support',
        'Email support',
      ],
      cta: 'Get Started',
      ctaLink: '/signup',
    },
    {
      name: 'Pro',
      price: '$49',
      description: 'For growing teams and projects',
      features: [
        'Everything in Free',
        '500,000 API requests/month',
        '5M tokens included',
        'Advanced caching algorithms',
        'Priority support',
        'Custom cache TTL',
        'Analytics dashboard',
        'API key management',
      ],
      cta: 'Get Started',
      ctaLink: '/signup',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      description: 'For large-scale production deployments',
      features: [
        'Everything in Pro',
        'Unlimited API requests',
        'Unlimited tokens',
        'Dedicated infrastructure',
        'Custom SLA guarantees',
        '24/7 priority support',
        'Advanced security features',
        'Custom integrations',
        'Dedicated account manager',
      ],
      cta: 'Contact Sales',
      ctaLink: 'mailto:sales@semantis.ai',
    },
  ];

  return (
    <div style={styles.container}>
      <Prism />

      <nav style={styles.nav}>
        <div style={styles.navContent}>
          <Link to="/" style={styles.logo}>
            <span style={styles.logoText}>Semantis AI</span>
          </Link>
          <div style={styles.navLinks}>
            <Link to="/" style={styles.navLink}>Home</Link>
            <Link to="/pricing" style={styles.navLink}>Pricing</Link>
            <Link to="/signin" style={styles.signinButton}>Sign In</Link>
          </div>
        </div>
      </nav>

      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Simple, Transparent Pricing</h1>
          <p style={styles.subtitle}>
            Semantis AI pricing is based on token usage and LLM API calls.
            <br />
            Choose the plan that fits your needs and scale as you grow.
          </p>
        </div>

        <div style={styles.tiersContainer}>
          {tiers.map((tier, index) => (
            <div
              key={tier.name}
              style={{
                ...styles.tierCard,
                ...(tier.popular ? styles.popularCard : {}),
              }}
            >
              {tier.popular && (
                <div style={styles.popularBadge}>Most Popular</div>
              )}

              <div style={styles.tierHeader}>
                <h3 style={styles.tierName}>{tier.name}</h3>
                <div style={styles.priceContainer}>
                  <span style={styles.price}>{tier.price}</span>
                  {tier.price !== 'Custom' && (
                    <span style={styles.priceFrequency}>/month</span>
                  )}
                </div>
                <p style={styles.tierDescription}>{tier.description}</p>
              </div>

              <div style={styles.featuresContainer}>
                {tier.features.map((feature, featureIndex) => (
                  <div key={featureIndex} style={styles.feature}>
                    <Check size={18} style={styles.checkIcon} />
                    <span style={styles.featureText}>{feature}</span>
                  </div>
                ))}
              </div>

              {tier.ctaLink.startsWith('mailto:') ? (
                <a
                  href={tier.ctaLink}
                  style={{
                    ...styles.ctaButton,
                    ...(tier.popular ? styles.popularButton : styles.regularButton),
                  }}
                >
                  <Mail size={18} />
                  <span>{tier.cta}</span>
                </a>
              ) : (
                <Link
                  to={tier.ctaLink}
                  style={{
                    ...styles.ctaButton,
                    ...(tier.popular ? styles.popularButton : styles.regularButton),
                  }}
                >
                  <span>{tier.cta}</span>
                  <ArrowRight size={18} />
                </Link>
              )}
            </div>
          ))}
        </div>

        <div style={styles.faq}>
          <h3 style={styles.faqTitle}>Questions about pricing?</h3>
          <p style={styles.faqText}>
            Contact our sales team at{' '}
            <a href="mailto:sales@semantis.ai" style={styles.emailLink}>
              sales@semantis.ai
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    position: 'relative',
    padding: '0 20px 80px',
  },
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
    padding: '16px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    textDecoration: 'none',
  },
  logoText: {
    fontSize: '20px',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  navLinks: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  navLink: {
    padding: '8px 16px',
    color: 'rgba(255, 255, 255, 0.7)',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '500',
    borderRadius: '8px',
    transition: 'all 0.2s',
  },
  signinButton: {
    padding: '10px 20px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    textDecoration: 'none',
    fontSize: '14px',
    fontWeight: '600',
    borderRadius: '8px',
    transition: 'all 0.2s',
    boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    paddingTop: '120px',
    position: 'relative',
    zIndex: 1,
  },
  header: {
    textAlign: 'center',
    marginBottom: '64px',
  },
  title: {
    fontSize: '56px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '16px',
    letterSpacing: '-0.02em',
  },
  subtitle: {
    fontSize: '18px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.6',
    maxWidth: '700px',
    margin: '0 auto',
  },
  tiersContainer: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '32px',
    marginBottom: '80px',
  },
  tierCard: {
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '24px',
    padding: '40px 32px',
    backdropFilter: 'blur(40px)',
    transition: 'all 0.4s ease',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
  },
  popularCard: {
    background: 'rgba(59, 130, 246, 0.08)',
    border: '2px solid rgba(59, 130, 246, 0.4)',
    transform: 'scale(1.05)',
  },
  popularBadge: {
    position: 'absolute',
    top: '-12px',
    left: '50%',
    transform: 'translateX(-50%)',
    padding: '6px 16px',
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    fontSize: '12px',
    fontWeight: '700',
    borderRadius: '20px',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  tierHeader: {
    marginBottom: '32px',
  },
  tierName: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '16px',
  },
  priceContainer: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '8px',
    marginBottom: '12px',
  },
  price: {
    fontSize: '48px',
    fontWeight: '700',
    color: '#fff',
    letterSpacing: '-0.02em',
  },
  priceFrequency: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  tierDescription: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: '1.5',
  },
  featuresContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '14px',
    marginBottom: '32px',
    flex: 1,
  },
  feature: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  checkIcon: {
    color: '#10b981',
    flexShrink: 0,
  },
  featureText: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.5',
  },
  ctaButton: {
    width: '100%',
    padding: '16px 24px',
    fontSize: '16px',
    fontWeight: '600',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    textDecoration: 'none',
    border: 'none',
  },
  popularButton: {
    background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
    color: '#fff',
    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)',
  },
  regularButton: {
    background: 'rgba(255, 255, 255, 0.08)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    color: '#fff',
  },
  faq: {
    textAlign: 'center',
    padding: '48px 32px',
    background: 'rgba(255, 255, 255, 0.04)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '24px',
    backdropFilter: 'blur(40px)',
  },
  faqTitle: {
    fontSize: '24px',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '12px',
  },
  faqText: {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: '1.6',
  },
  emailLink: {
    color: '#3b82f6',
    textDecoration: 'none',
    fontWeight: '600',
  },
};
