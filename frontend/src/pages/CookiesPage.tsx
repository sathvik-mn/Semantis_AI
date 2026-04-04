import { Link } from 'react-router-dom';
import { TubesBackground } from '../components/TubesBackground';

export function CookiesPage() {
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
          <h1 className="text-4xl font-bold text-white mb-8">Cookie Policy</h1>

          <div className="prose prose-invert max-w-none space-y-6 text-white/70 text-[15px] leading-relaxed">
            <p><strong className="text-white">Effective Date:</strong> April 4, 2026</p>

            <p>
              This Cookie Policy explains how Semantys AI (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) uses
              cookies and similar technologies when you visit or use our platform. By continuing to use the Service
              you consent to the use of cookies as described below.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">1. What Are Cookies?</h2>
            <p>
              Cookies are small text files placed on your device by a website or application. They are widely used
              to make services work efficiently, remember your preferences, and provide usage analytics. Similar
              technologies include localStorage, sessionStorage, and web beacons.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">2. Cookies We Use</h2>

            <div className="overflow-x-auto mt-4">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.1]">
                    <th className="text-left py-3 pr-4 text-white font-semibold">Category</th>
                    <th className="text-left py-3 pr-4 text-white font-semibold">Purpose</th>
                    <th className="text-left py-3 text-white font-semibold">Duration</th>
                  </tr>
                </thead>
                <tbody className="text-white/60">
                  <tr className="border-b border-white/[0.06]">
                    <td className="py-3 pr-4 text-white/80 font-medium">Essential</td>
                    <td className="py-3 pr-4">Authentication session tokens (Supabase). Required for the Service to function. Cannot be disabled.</td>
                    <td className="py-3">Session / 7 days</td>
                  </tr>
                  <tr className="border-b border-white/[0.06]">
                    <td className="py-3 pr-4 text-white/80 font-medium">Functional</td>
                    <td className="py-3 pr-4">API key storage in localStorage for playground access. Theme and UI preferences.</td>
                    <td className="py-3">Persistent</td>
                  </tr>
                  <tr className="border-b border-white/[0.06]">
                    <td className="py-3 pr-4 text-white/80 font-medium">Analytics</td>
                    <td className="py-3 pr-4">PostHog analytics to understand usage patterns and improve the product. Collects anonymized interaction data.</td>
                    <td className="py-3">1 year</td>
                  </tr>
                  <tr className="border-b border-white/[0.06]">
                    <td className="py-3 pr-4 text-white/80 font-medium">Error Tracking</td>
                    <td className="py-3 pr-4">Sentry error monitoring to detect and fix bugs. Collects error context and session replay data.</td>
                    <td className="py-3">Session</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h2 className="text-xl font-semibold text-white mt-8">3. Local Storage</h2>
            <p>
              In addition to cookies, we use browser localStorage to store:
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-white">Supabase session:</strong> Your authentication token for maintaining login state.</li>
              <li><strong className="text-white">API key:</strong> Your Semantys AI API key for making requests from the playground.</li>
              <li><strong className="text-white">UI preferences:</strong> Display settings and dashboard configurations.</li>
            </ul>
            <p>
              These values remain on your device until you sign out or clear your browser data.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">4. Third-Party Cookies</h2>
            <p>Some cookies are set by third-party services we integrate with:</p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong className="text-white">Stripe:</strong> May set cookies during the checkout and billing portal flow for fraud prevention and payment processing.</li>
              <li><strong className="text-white">Supabase:</strong> Sets authentication-related cookies and tokens.</li>
              <li><strong className="text-white">PostHog:</strong> Sets analytics cookies to track product usage. You can opt out via your browser settings.</li>
              <li><strong className="text-white">Sentry:</strong> May set cookies for error session tracking.</li>
            </ul>

            <h2 className="text-xl font-semibold text-white mt-8">5. How to Manage Cookies</h2>
            <p>
              Most browsers allow you to control cookies through their settings. You can typically:
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>View and delete existing cookies.</li>
              <li>Block all or specific cookies.</li>
              <li>Set preferences for certain websites.</li>
            </ul>
            <p>
              Note that blocking essential cookies will prevent you from using the Service. Blocking analytics
              cookies will not affect functionality.
            </p>
            <p>
              To clear localStorage data, use your browser&apos;s developer tools (Application &gt; Local Storage)
              or sign out of your account, which clears stored credentials.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">6. Do Not Track</h2>
            <p>
              Some browsers send a &quot;Do Not Track&quot; (DNT) signal. There is no industry standard for how
              websites should respond to DNT signals. We do not currently alter our data collection practices in
              response to DNT signals, but you can manage cookies and analytics as described above.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">7. Changes to This Policy</h2>
            <p>
              We may update this Cookie Policy from time to time. Changes will be posted on this page with an
              updated Effective Date.
            </p>

            <h2 className="text-xl font-semibold text-white mt-8">8. Contact Us</h2>
            <p>
              If you have questions about our use of cookies, contact us at{' '}
              <a href="mailto:contact@abodeex.com" className="text-white/80 no-underline hover:underline hover:text-white">contact@abodeex.com</a>.
            </p>
            <p className="text-white/50 text-sm mt-4">
              Semantys AI<br />
              Chicago, Illinois, United States
            </p>

            <div className="mt-12 pt-8 border-t border-white/[0.06] flex gap-4 text-sm">
              <Link to="/privacy" className="text-white/50 hover:text-white no-underline transition-colors">Privacy Policy</Link>
              <Link to="/terms" className="text-white/50 hover:text-white no-underline transition-colors">Terms of Service</Link>
            </div>
          </div>
        </div>
      </div>
    </TubesBackground>
  );
}
