import { useState } from 'react';
import { Link } from 'react-router-dom';

const ONBOARDING_KEY = 'semantis_onboarding_complete';

export function useOnboarding() {
  const [dismissed, setDismissed] = useState(() =>
    localStorage.getItem(ONBOARDING_KEY) === 'true'
  );

  const complete = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setDismissed(true);
  };

  return { show: !dismissed, complete };
}

interface OnboardingWizardProps {
  onComplete: () => void;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: 'Welcome to Semantys AI',
      body: 'Semantic caching for LLM applications. Reduce costs and latency by caching similar queries.',
      cta: 'Get Started',
    },
    {
      title: 'Get Your API Key',
      body: 'Go to Settings to generate an API key. Use it to connect your app to our OpenAI-compatible endpoint.',
      cta: 'Go to Settings',
      link: '/settings',
    },
    {
      title: 'Try the Playground',
      body: 'Test semantic caching with sample queries. Watch how similar questions hit the cache.',
      cta: 'Open Playground',
      link: '/playground',
    },
    {
      title: 'Monitor Your Savings',
      body: 'Check the Metrics page for hit ratios, latency, and cost savings from your cached requests.',
      cta: 'View Metrics',
      link: '/metrics',
    },
  ];

  const current = steps[step];
  const isLast = step === steps.length - 1;

  const handleNext = () => {
    if (isLast) {
      onComplete();
    } else {
      setStep((s) => s + 1);
    }
  };

  const handleCtaClick = () => {
    if (current.link) {
      onComplete();
    } else {
      handleNext();
    }
  };

  const handleSkip = () => onComplete();

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.progress}>
          {steps.map((_, i) => (
            <div
              key={i}
              style={{
                ...styles.dot,
                ...(i <= step ? styles.dotActive : {}),
              }}
            />
          ))}
        </div>
        <h2 style={styles.title}>{current.title}</h2>
        <p style={styles.body}>{current.body}</p>
        <div style={styles.actions}>
          {current.link ? (
            <Link
              to={current.link}
              style={styles.primaryBtn}
              onClick={handleCtaClick}
            >
              {current.cta}
            </Link>
          ) : (
            <button style={styles.primaryBtn} onClick={handleNext}>
              {current.cta}
            </button>
          )}
          <button style={styles.skipBtn} onClick={handleSkip}>
            Skip
          </button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    backdropFilter: 'blur(8px)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  modal: {
    background: 'linear-gradient(180deg, rgba(30, 30, 40, 0.98), rgba(20, 20, 28, 0.98))',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '32px',
    maxWidth: '420px',
    width: '90%',
  },
  progress: {
    display: 'flex',
    gap: '8px',
    marginBottom: '24px',
  },
  dot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: 'rgba(255, 255, 255, 0.2)',
  },
  dotActive: {
    background: 'rgba(255, 255, 255, 0.7)',
  },
  title: {
    fontSize: '22px',
    color: '#fff',
    marginBottom: '12px',
    fontWeight: '600',
  },
  body: {
    fontSize: '15px',
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: '1.6',
    marginBottom: '24px',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  primaryBtn: {
    padding: '10px 20px',
    background: 'linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04))',
    border: '1px solid rgba(255,255,255,0.18)',
    borderRadius: '12px',
    color: '#fff',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    textDecoration: 'none',
    backdropFilter: 'blur(20px)',
    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2), 0 4px 24px rgba(0,0,0,0.3)',
  },
  skipBtn: {
    padding: '10px 16px',
    background: 'transparent',
    border: 'none',
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: '14px',
    cursor: 'pointer',
  },
};
