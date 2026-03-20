import { useState, useEffect, useCallback } from 'react';
import { CreditCard, ArrowUpRight, Loader2, Check, AlertCircle, ExternalLink } from 'lucide-react';
import { getBillingStatus, upgradePlan, getBillingPortalUrl, getBillingPlans, BillingStatus, BillingPlan } from '../api/semanticAPI';

export function BillingSection() {
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [plans, setPlans] = useState<Record<string, BillingPlan>>({});
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchBilling = useCallback(async () => {
    try {
      setError(null);
      const [data, plansData] = await Promise.all([
        getBillingStatus(),
        getBillingPlans(),
      ]);
      setBilling(data);
      setPlans(plansData.plans);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load billing');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBilling();
    const params = new URLSearchParams(window.location.search);
    if (params.get('billing') === 'success') {
      setSuccessMsg('Plan upgraded successfully!');
      window.history.replaceState({}, '', window.location.pathname);
      setTimeout(() => setSuccessMsg(null), 5000);
    }
  }, [fetchBilling]);

  const handleUpgrade = async (plan: string) => {
    setUpgrading(plan);
    setError(null);
    try {
      const result = await upgradePlan(plan);
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
      } else {
        setSuccessMsg(result.message);
        await fetchBilling();
        setTimeout(() => setSuccessMsg(null), 5000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upgrade failed');
    } finally {
      setUpgrading(null);
    }
  };

  const handleManageSubscription = async () => {
    setError(null);
    try {
      const result = await getBillingPortalUrl();
      if (result.portal_url) {
        window.open(result.portal_url, '_blank');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open billing portal');
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={{ textAlign: 'center', padding: '32px', color: 'rgba(255,255,255,0.5)' }}>
          <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} />
          <p>Loading billing...</p>
        </div>
      </div>
    );
  }

  const formatPrice = (planKey: string) => {
    const plan = plans[planKey];
    if (!plan) return '';
    if (plan.price_monthly === null) return 'Contact us';
    return `$${plan.price_monthly}/mo`;
  };

  const currentPlan = billing?.plan || 'free';
  const limits = billing?.limits;
  const usage = billing?.usage_30d;
  const savings = billing?.savings_estimate;
  const usagePercent = limits?.max_requests_month && usage
    ? Math.min(100, Math.round((Number(usage.total_requests || 0) / limits.max_requests_month) * 100))
    : 0;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <CreditCard size={20} style={{ color: '#a78bfa' }} />
        <h3 style={styles.sectionTitle}>Billing & Plan</h3>
      </div>

      {successMsg && (
        <div style={styles.successMessage}>
          <Check size={16} /> {successMsg}
        </div>
      )}
      {error && (
        <div style={styles.errorMessage}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {/* Current Plan */}
      <div style={styles.planCard}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={styles.planLabel}>Current Plan</div>
            <div style={styles.planName}>{currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)}</div>
          </div>
          {currentPlan !== 'free' && (
            <button onClick={handleManageSubscription} style={styles.portalButton}>
              <ExternalLink size={14} /> Manage Subscription
            </button>
          )}
        </div>

        {/* Usage bar */}
        {limits?.max_requests_month && (
          <div style={{ marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
              <span style={styles.usageLabel}>Requests this month</span>
              <span style={styles.usageValue}>
                {Number(usage?.total_requests || 0).toLocaleString()} / {limits.max_requests_month.toLocaleString()}
              </span>
            </div>
            <div style={styles.progressBar}>
              <div style={{
                ...styles.progressFill,
                width: `${usagePercent}%`,
                background: usagePercent > 90 ? '#ef4444' : usagePercent > 70 ? '#f59e0b' : '#3b82f6',
              }} />
            </div>
          </div>
        )}

        {savings && savings.estimated_savings_usd > 0 && (
          <div style={styles.savingsChip}>
            You've saved ~${savings.estimated_savings_usd.toFixed(2)} this month with caching
          </div>
        )}
      </div>

      {/* Upgrade options */}
      {currentPlan === 'free' && (
        <div style={styles.upgradeSection}>
          <p style={styles.upgradeText}>Upgrade to unlock more requests, advanced features, and priority support.</p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleUpgrade('pro')}
              disabled={!!upgrading}
              style={styles.upgradeButton}
            >
              {upgrading === 'pro' ? (
                <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Upgrading...</>
              ) : (
                <><ArrowUpRight size={16} /> Upgrade to Pro — {formatPrice('pro')}</>
              )}
            </button>
            <button
              onClick={() => handleUpgrade('team')}
              disabled={!!upgrading}
              style={styles.upgradeButtonSecondary}
            >
              {upgrading === 'team' ? (
                <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Upgrading...</>
              ) : (
                <><ArrowUpRight size={16} /> Upgrade to Team — {formatPrice('team')}</>
              )}
            </button>
          </div>
        </div>
      )}
      {currentPlan === 'pro' && (
        <div style={styles.upgradeSection}>
          <p style={styles.upgradeText}>Need more capacity? Upgrade to Team for 500K requests/month.</p>
          <button
            onClick={() => handleUpgrade('team')}
            disabled={!!upgrading}
            style={styles.upgradeButton}
          >
            {upgrading === 'team' ? (
              <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Upgrading...</>
            ) : (
              <><ArrowUpRight size={16} /> Upgrade to Team — {formatPrice('team')}</>
            )}
          </button>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: 'rgba(167, 139, 250, 0.06)',
    border: '1px solid rgba(167, 139, 250, 0.2)',
    borderRadius: '12px',
    padding: '24px',
  },
  header: { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' },
  sectionTitle: { fontSize: '20px', color: '#fff', margin: 0, fontWeight: '600' },
  planCard: {
    background: 'rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '10px',
    padding: '20px',
  },
  planLabel: { fontSize: '12px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase' as const, letterSpacing: '0.05em', marginBottom: '4px' },
  planName: { fontSize: '24px', fontWeight: '700', color: '#fff' },
  portalButton: {
    display: 'flex', alignItems: 'center', gap: '6px',
    padding: '8px 14px', fontSize: '13px', fontWeight: '500',
    background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '8px', color: '#fff', cursor: 'pointer', transition: 'background 0.2s',
  },
  usageLabel: { fontSize: '13px', color: 'rgba(255,255,255,0.5)' },
  usageValue: { fontSize: '13px', color: 'rgba(255,255,255,0.8)', fontFamily: 'monospace' },
  progressBar: {
    height: '6px', borderRadius: '3px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden',
  },
  progressFill: { height: '100%', borderRadius: '3px', transition: 'width 0.5s ease' },
  savingsChip: {
    marginTop: '12px', padding: '8px 12px', borderRadius: '8px',
    background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)',
    fontSize: '13px', color: '#86efac',
  },
  upgradeSection: { marginTop: '16px' },
  upgradeText: { fontSize: '14px', color: 'rgba(255,255,255,0.6)', marginBottom: '12px', marginTop: 0 },
  upgradeButton: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '12px 20px', fontSize: '14px', fontWeight: '600',
    background: 'linear-gradient(135deg, #7c3aed, #6d28d9)', border: 'none',
    borderRadius: '10px', color: '#fff', cursor: 'pointer', transition: 'opacity 0.2s',
  },
  upgradeButtonSecondary: {
    display: 'flex', alignItems: 'center', gap: '8px',
    padding: '12px 20px', fontSize: '14px', fontWeight: '600',
    background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '10px', color: '#fff', cursor: 'pointer', transition: 'background 0.2s',
  },
  successMessage: {
    display: 'flex', alignItems: 'center', gap: '8px', padding: '12px',
    background: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.3)',
    borderRadius: '8px', color: '#86efac', fontSize: '14px', marginBottom: '12px',
  },
  errorMessage: {
    display: 'flex', alignItems: 'center', gap: '8px', padding: '12px',
    background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px', color: '#fca5a5', fontSize: '14px', marginBottom: '12px',
  },
};
