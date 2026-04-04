import { Link } from 'react-router-dom';
import { TubesBackground } from '../components/TubesBackground';

export function PrivacyPage() {
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
          <h1 className="text-4xl font-bold text-white mb-8">Privacy Policy</h1>

          <div className="prose prose-invert max-w-none space-y-6 text-white/70 text-[15px] leading-relaxed">
            <p><strong className="text-white">Effective Date:</strong> April 4, 2026</p>

            <p>
              Semantys AI (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) operates the Semantys AI semantic caching
              platform (the &quot;Service&quot;). This Privacy Policy explains how we collect, use, disclose, and
              safeguard your information when you use our Service. By accessing or using the Service you agree to
              this policy. If you do not agree, please do not use the Service.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">1. Information We Collect</h2>

            <h3 className="text-lg font-medium text-white/90 mt-4">a. Account Information</h3>
            <p>
              When you register we collect your name, email address, and authentication credentials managed through
              our authentication provider (Supabase). If you sign up via a social login provider we receive the
              profile information that provider shares.
            </p>

            <h3 className="text-lg font-medium text-white/90 mt-4">b. API &amp; Usage Data</h3>
            <p>
              We automatically collect data about how you interact with the Service, including: API request and
              response metadata (timestamps, cache hit/miss status, latency), request counts, similarity scores,
              and error rates. We do not log the full content of your prompts or LLM responses in our analytics
              pipeline, though cached prompt-response pairs are stored to serve future semantically similar requests.
            </p>

            <h3 className="text-lg font-medium text-white/90 mt-4">c. Payment Information</h3>
            <p>
              If you subscribe to a paid plan, payment details (credit card number, billing address) are collected
              and processed directly by Stripe. We do not store your full card number on our servers; we retain
              only a Stripe customer ID and basic transaction metadata.
            </p>

            <h3 className="text-lg font-medium text-white/90 mt-4">d. Device &amp; Log Data</h3>
            <p>
              We collect IP addresses, browser type, operating system, referral URLs, and access timestamps for
              security monitoring, rate limiting, and abuse prevention.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">2. How We Use Your Information</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li>Provide, operate, and maintain the semantic caching Service.</li>
              <li>Authenticate your identity and manage your account.</li>
              <li>Process billing and enforce plan limits.</li>
              <li>Monitor system health, detect abuse, and enforce our Terms of Service.</li>
              <li>Send transactional emails (account confirmations, security alerts, billing receipts).</li>
              <li>Improve and develop new features based on aggregated, de-identified usage trends.</li>
            </ul>

            <h2 className="text-xl font-semibold text-white mt-8">3. How We Share Your Information</h2>
            <p>We do not sell your personal information. We share data only in these circumstances:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-white">Service Providers:</strong> We use third-party services to operate the platform, including Supabase (authentication &amp; database), OpenAI (embeddings &amp; LLM inference), Stripe (payments), Upstash (Redis caching), Pinecone (vector storage), Resend (transactional email), and Sentry (error tracking). Each provider processes data under its own privacy policy and our data processing agreements.</li>
              <li><strong className="text-white">Legal Obligations:</strong> We may disclose information if required by law, regulation, or valid legal process.</li>
              <li><strong className="text-white">Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets, your information may be transferred to the successor entity.</li>
            </ul>

            <h2 className="text-xl font-semibold text-white mt-8">4. Data Storage &amp; Security</h2>
            <p>
              Data is stored in encrypted PostgreSQL databases hosted on Supabase infrastructure in the United States.
              API keys and user-supplied OpenAI credentials are encrypted at rest using Fernet symmetric encryption
              with per-deployment keys. Cached prompt-response pairs can optionally be encrypted with AES-256-GCM
              per-tenant encryption. All data in transit is protected by TLS 1.2+.
            </p>
            <p>
              While we implement industry-standard safeguards, no method of electronic storage is 100% secure. We
              cannot guarantee absolute security.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">5. Data Retention</h2>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-white">Cached data:</strong> Retained according to your configured TTL (default: 7 days) and automatically purged thereafter.</li>
              <li><strong className="text-white">Account data:</strong> Retained while your account is active and for up to 30 days after deletion to allow recovery.</li>
              <li><strong className="text-white">Usage &amp; billing records:</strong> Retained for up to 2 years for accounting and dispute resolution.</li>
              <li><strong className="text-white">Security logs:</strong> Retained for up to 90 days.</li>
            </ul>

            <h2 className="text-xl font-semibold text-white mt-8">6. Your Rights</h2>
            <p>Depending on your jurisdiction you may have the right to:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-white">Access</strong> the personal data we hold about you.</li>
              <li><strong className="text-white">Correct</strong> inaccurate or incomplete data.</li>
              <li><strong className="text-white">Delete</strong> your account and associated data.</li>
              <li><strong className="text-white">Export</strong> your cache data via our API.</li>
              <li><strong className="text-white">Opt out</strong> of non-essential communications.</li>
            </ul>

            <h3 className="text-lg font-medium text-white/90 mt-4">Illinois Residents</h3>
            <p>
              If you are an Illinois resident, you may have additional rights under the Illinois Personal Information
              Protection Act (PIPA). We do not collect biometric data. To exercise any privacy right, contact us
              using the information below.
            </p>

            <h3 className="text-lg font-medium text-white/90 mt-4">California Residents</h3>
            <p>
              If you are a California resident, you may have additional rights under the California Consumer Privacy
              Act (CCPA) and the California Privacy Rights Act (CPRA), including the right to know what personal
              information we collect, request deletion, and opt out of the sale of personal information. We do not
              sell personal information.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">7. Children&apos;s Privacy</h2>
            <p>
              The Service is not directed to individuals under the age of 16. We do not knowingly collect personal
              information from children. If we learn that we have collected data from a child under 16, we will
              delete it promptly.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">8. International Transfers</h2>
            <p>
              Your data may be processed in the United States and other countries where our service providers
              operate. By using the Service you consent to the transfer of your information to these jurisdictions,
              which may have different data protection laws than your jurisdiction.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">9. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of material changes by
              posting the updated policy on this page and updating the &quot;Effective Date&quot; above. Continued
              use of the Service after changes constitutes acceptance of the updated policy.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">10. Contact Us</h2>
            <p>
              For privacy-related inquiries or to exercise your rights, contact us at{' '}
              <a href="mailto:contact@abodeex.com" className="text-white/80 no-underline hover:underline hover:text-white">contact@abodeex.com</a>.
            </p>
            <p className="text-white/50 text-sm mt-4">
              Semantys AI<br />
              Chicago, Illinois, United States
            </p>

            <div className="mt-12 pt-8 border-t border-white/[0.06] flex gap-4 text-sm">
              <Link to="/terms" className="text-white/50 hover:text-white no-underline transition-colors">Terms of Service</Link>
              <Link to="/cookies" className="text-white/50 hover:text-white no-underline transition-colors">Cookie Policy</Link>
            </div>
          </div>
        </div>
      </div>
    </TubesBackground>
  );
}
