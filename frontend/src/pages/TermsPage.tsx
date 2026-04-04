import { Link } from 'react-router-dom';
import { TubesBackground } from '../components/TubesBackground';

export function TermsPage() {
  return (
    <TubesBackground className="min-h-screen">
      <div className="pointer-events-auto">
        <nav className="fixed top-0 inset-x-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/[0.06]">
          <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
            <Link to="/" className="text-xl font-bold text-gradient no-underline">Semantys AI</Link>
            <div className="flex gap-3">
              <Link to="/" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Home</Link>
              <Link to="/signin" className="btn-primary text-sm no-underline">Sign In</Link>
            </div>
          </div>
        </nav>

        <div className="max-w-3xl mx-auto pt-32 pb-20 px-6 relative z-10">
          <h1 className="text-4xl font-bold text-white mb-8">Terms of Service</h1>

          <div className="prose prose-invert max-w-none space-y-6 text-white/70 text-[15px] leading-relaxed">
            <p><strong className="text-white">Effective Date:</strong> April 4, 2026</p>

            <p>
              These Terms of Service (&quot;Terms&quot;) govern your access to and use of the Semantys AI platform
              and related services (the &quot;Service&quot;) operated by Semantys AI (&quot;we,&quot; &quot;us,&quot;
              or &quot;our&quot;). By creating an account or using the Service you agree to be bound by these Terms.
              If you do not agree, do not use the Service.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">1. Eligibility</h2>
            <p>
              You must be at least 16 years old and capable of entering a binding agreement to use the Service.
              If you are using the Service on behalf of an organization, you represent that you have authority to
              bind that organization to these Terms.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">2. Account Registration</h2>
            <p>
              You must provide accurate and complete information when creating an account. You are responsible for
              maintaining the confidentiality of your credentials, including API keys, and for all activity that
              occurs under your account. Notify us immediately at{' '}
              <a href="mailto:contact@abodeex.com" className="text-white/80 no-underline hover:underline hover:text-white">contact@abodeex.com</a>{' '}
              if you suspect unauthorized access.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">3. Description of the Service</h2>
            <p>
              Semantys AI provides a semantic caching layer for large language model (LLM) applications. The Service
              intercepts API calls, identifies semantically similar queries, and returns cached responses when
              appropriate, reducing latency and cost. Features include a playground, analytics dashboard, API key
              management, organization workspaces, and optional bring-your-own-key (BYOK) OpenAI integration.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">4. Acceptable Use</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li>Use the Service for any unlawful purpose or in violation of any applicable law or regulation.</li>
              <li>Attempt to gain unauthorized access to other users&apos; accounts, data, or cache partitions.</li>
              <li>Reverse-engineer, decompile, or attempt to extract the source code of the Service.</li>
              <li>Interfere with or disrupt the Service, including through denial-of-service attacks, excessive automated requests beyond your plan limits, or injection of malicious content.</li>
              <li>Use the Service to store, cache, or transmit content that is illegal, harmful, defamatory, or infringes on intellectual property rights.</li>
              <li>Resell or sublicense access to the Service without our written consent.</li>
              <li>Circumvent rate limits, plan restrictions, or authentication mechanisms.</li>
            </ul>

            <h2 className="text-xl font-semibold text-white mt-8">5. API Keys &amp; Security</h2>
            <p>
              API keys are credentials that grant access to your cache partition. Treat them as secrets. Do not
              embed API keys in client-side code, public repositories, or share them with unauthorized parties. We
              are not responsible for unauthorized use resulting from your failure to secure your credentials.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">6. Plans, Billing &amp; Payments</h2>

            <h3 className="text-lg font-medium text-white/90 mt-4">a. Free Tier</h3>
            <p>
              We offer a free tier with limited request quotas. Free-tier accounts are subject to rate limits and
              may be suspended if they exceed fair-use thresholds.
            </p>

            <h3 className="text-lg font-medium text-white/90 mt-4">b. Paid Plans</h3>
            <p>
              Paid plans are billed on a monthly subscription basis through Stripe. By subscribing you authorize
              us to charge your payment method at the beginning of each billing cycle. All fees are stated in US
              dollars and are non-refundable except as required by law.
            </p>

            <h3 className="text-lg font-medium text-white/90 mt-4">c. Changes to Pricing</h3>
            <p>
              We may change pricing with at least 30 days&apos; notice. Continued use after the effective date of
              a price change constitutes acceptance. You may cancel your subscription before the change takes effect.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">7. Your Content &amp; Data</h2>
            <p>
              You retain ownership of all data you submit to the Service, including prompts and responses stored
              in the cache (&quot;Your Content&quot;). You grant us a limited, non-exclusive license to store,
              process, and serve Your Content solely for the purpose of operating the Service.
            </p>
            <p>
              We do not use Your Content to train machine learning models or share it with third parties except as
              necessary to provide the Service (e.g., sending prompts to OpenAI for embedding generation).
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">8. Bring-Your-Own-Key (BYOK)</h2>
            <p>
              If you provide your own OpenAI API key, it is encrypted at rest and used only to make API calls on
              your behalf. We do not use your key for any other purpose. You are responsible for any charges incurred
              on your OpenAI account through the Service.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">9. Service Availability &amp; SLA</h2>
            <p>
              We strive to maintain high availability but do not guarantee uninterrupted service. The Service is
              provided &quot;as is&quot; and &quot;as available.&quot; We may perform maintenance, updates, or
              experience outages that temporarily affect availability. We will make reasonable efforts to notify
              you of scheduled maintenance in advance.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">10. Intellectual Property</h2>
            <p>
              The Service, including its design, code, features, documentation, and branding, is owned by Semantys AI
              and protected by intellectual property laws. These Terms do not grant you any rights to our trademarks,
              logos, or brand assets.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">11. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, Semantys AI shall not be liable for any indirect, incidental,
              special, consequential, or punitive damages, including loss of profits, data, or business opportunities,
              arising from your use of or inability to use the Service, even if we have been advised of the
              possibility of such damages.
            </p>
            <p>
              Our total aggregate liability for any claims arising from these Terms or the Service shall not exceed
              the amount you paid us in the 12 months preceding the claim, or $100, whichever is greater.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">12. Indemnification</h2>
            <p>
              You agree to indemnify and hold harmless Semantys AI from any claims, damages, losses, or expenses
              (including reasonable attorney&apos;s fees) arising from your use of the Service, violation of these
              Terms, or infringement of any third-party rights.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">13. Termination</h2>
            <p>
              You may close your account at any time through the Settings page. We may suspend or terminate your
              access if you violate these Terms, engage in abusive behavior, or fail to pay applicable fees. Upon
              termination, your right to use the Service ceases immediately. Cached data will be purged according
              to our standard retention schedule.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">14. Governing Law &amp; Disputes</h2>
            <p>
              These Terms are governed by the laws of the State of Illinois, United States, without regard to
              conflict-of-law principles. Any disputes arising from these Terms or the Service shall be resolved
              in the state or federal courts located in Cook County, Illinois.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">15. Changes to These Terms</h2>
            <p>
              We may update these Terms from time to time. We will notify you of material changes by posting the
              updated Terms on this page and updating the Effective Date. Continued use of the Service after changes
              constitutes acceptance. If you do not agree with updated Terms, you must stop using the Service.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">16. Severability</h2>
            <p>
              If any provision of these Terms is found to be unenforceable, the remaining provisions will continue
              in full force and effect.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">17. Contact Us</h2>
            <p>
              If you have questions about these Terms, contact us at{' '}
              <a href="mailto:contact@abodeex.com" className="text-white/80 no-underline hover:underline hover:text-white">contact@abodeex.com</a>.
            </p>
            <p className="text-white/50 text-sm mt-4">
              Semantys AI<br />
              Chicago, Illinois, United States
            </p>

            <div className="mt-12 pt-8 border-t border-white/[0.06] flex gap-4 text-sm">
              <Link to="/privacy" className="text-white/50 hover:text-white no-underline transition-colors">Privacy Policy</Link>
              <Link to="/cookies" className="text-white/50 hover:text-white no-underline transition-colors">Cookie Policy</Link>
            </div>
          </div>
        </div>
      </div>
    </TubesBackground>
  );
}
