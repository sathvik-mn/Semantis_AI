import { Link } from 'react-router-dom';
import { TubesBackground } from '../components/TubesBackground';

export function PrivacyPage() {
  return (
    <TubesBackground className="min-h-screen">
      <div className="pointer-events-auto">
        <nav className="fixed top-0 inset-x-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/[0.06]">
          <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
            <Link to="/" className="text-xl font-bold text-gradient no-underline">Semantis AI</Link>
            <div className="flex gap-3">
              <Link to="/" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Home</Link>
              <Link to="/signin" className="btn-primary text-sm no-underline">Sign In</Link>
            </div>
          </div>
        </nav>

        <div className="max-w-3xl mx-auto pt-32 pb-20 px-6 relative z-10">
          <h1 className="text-4xl font-bold text-white mb-8">Privacy Policy</h1>

          <div className="prose prose-invert max-w-none space-y-6 text-white/70 text-[15px] leading-relaxed">
            <p><strong className="text-white">Last updated:</strong> March 2026</p>

            <h2 className="text-xl font-semibold text-white mt-8">1. Information We Collect</h2>
            <p>
              When you use Semantis AI, we collect information necessary to provide our semantic caching service:
              account details (email, name), API usage data (request counts, cache hit/miss rates, latency metrics),
              and the queries you send through our API for caching purposes.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">2. How We Use Your Data</h2>
            <p>
              Your data is used to provide, maintain, and improve the caching service. Cached query-response pairs
              are stored to serve future semantically similar requests. Usage metrics power your dashboard analytics
              and billing calculations.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">3. Data Storage & Security</h2>
            <p>
              Data is stored in encrypted PostgreSQL databases hosted on Supabase infrastructure. API keys and
              OpenAI credentials are encrypted at rest using Fernet symmetric encryption. All data in transit
              is protected by TLS 1.2+.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">4. Data Retention</h2>
            <p>
              Cached responses are retained according to your configured TTL (default: 7 days). Account data is
              retained while your account is active. You can request deletion of your data at any time by
              contacting us.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">5. Third-Party Services</h2>
            <p>
              We use OpenAI for embedding generation and LLM calls, Supabase for authentication and database,
              and Stripe for payment processing. Each service has its own privacy policy governing how they
              handle data.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">6. Your Rights</h2>
            <p>
              You have the right to access, correct, or delete your personal data. You can export your cache
              data via our API and delete your account at any time through the settings page.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">7. Contact</h2>
            <p>
              For privacy-related inquiries, contact us at{' '}
              <a href="mailto:privacy@semantis.ai" className="text-blue-400 no-underline hover:underline">privacy@semantis.ai</a>.
            </p>
          </div>
        </div>
      </div>
    </TubesBackground>
  );
}
