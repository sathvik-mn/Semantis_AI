import { Link } from 'react-router-dom';
import { Check, ArrowRight, Mail } from 'lucide-react';
import { TubesBackground } from '../components/TubesBackground';

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
        'Advanced security',
        'Dedicated account manager',
      ],
      cta: 'Contact Sales',
      ctaLink: 'mailto:sales@semantis.ai',
    },
  ];

  return (
    <TubesBackground className="min-h-screen" enableClickInteraction>
      <div className="pointer-events-auto">
        {/* Nav */}
        <nav className="fixed top-0 inset-x-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/[0.06]">
          <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
            <Link to="/" className="text-xl font-bold text-gradient no-underline">Semantis AI</Link>
            <div className="flex gap-3 items-center">
              <Link to="/" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Home</Link>
              <Link to="/signin" className="btn-primary text-sm no-underline">Sign In</Link>
            </div>
          </div>
        </nav>

        <div className="max-w-6xl mx-auto pt-32 pb-20 px-5 relative z-10">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-4 tracking-tight">Simple, Transparent Pricing</h1>
            <p className="text-lg text-white/60 max-w-2xl mx-auto leading-relaxed">
              Choose the plan that fits your needs. Scale as you grow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
            {tiers.map((tier) => (
              <div
                key={tier.name}
                className={`glass-card flex flex-col p-8 transition-all hover:-translate-y-1 relative ${
                  tier.popular ? 'border-blue-500/40 bg-blue-500/[0.06] md:scale-105' : ''
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full
                                  bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-bold uppercase tracking-wider">
                    Most Popular
                  </div>
                )}

                <div className="mb-8">
                  <h3 className="text-xl font-bold text-white mb-3">{tier.name}</h3>
                  <div className="flex items-baseline gap-1 mb-2">
                    <span className="text-5xl font-bold text-white tracking-tight">{tier.price}</span>
                    {tier.price !== 'Custom' && <span className="text-white/40 text-sm">/month</span>}
                  </div>
                  <p className="text-sm text-white/50">{tier.description}</p>
                </div>

                <div className="flex flex-col gap-3.5 mb-8 flex-1">
                  {tier.features.map((f) => (
                    <div key={f} className="flex items-center gap-3">
                      <Check size={16} className="text-emerald-500 shrink-0" />
                      <span className="text-sm text-white/70">{f}</span>
                    </div>
                  ))}
                </div>

                {tier.ctaLink.startsWith('mailto:') ? (
                  <a
                    href={tier.ctaLink}
                    className={`flex items-center justify-center gap-2 w-full py-3.5 rounded-xl font-semibold text-sm no-underline transition-all ${
                      tier.popular
                        ? 'btn-primary'
                        : 'bg-white/[0.06] border border-white/[0.1] text-white hover:bg-white/[0.1]'
                    }`}
                  >
                    <Mail size={16} /> {tier.cta}
                  </a>
                ) : (
                  <Link
                    to={tier.ctaLink}
                    className={`flex items-center justify-center gap-2 w-full py-3.5 rounded-xl font-semibold text-sm no-underline transition-all ${
                      tier.popular
                        ? 'btn-primary'
                        : 'bg-white/[0.06] border border-white/[0.1] text-white hover:bg-white/[0.1]'
                    }`}
                  >
                    {tier.cta} <ArrowRight size={16} />
                  </Link>
                )}
              </div>
            ))}
          </div>

          <div className="glass-card p-10 text-center">
            <h3 className="text-xl font-bold text-white mb-2">Questions about pricing?</h3>
            <p className="text-white/60">
              Contact our sales team at{' '}
              <a href="mailto:sales@semantis.ai" className="text-blue-400 font-semibold no-underline hover:underline">
                sales@semantis.ai
              </a>
            </p>
          </div>
        </div>
      </div>
    </TubesBackground>
  );
}
