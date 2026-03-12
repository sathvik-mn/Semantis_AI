import { Link } from 'react-router-dom';
import { TubesBackground } from '../components/TubesBackground';

export function LandingPage() {
  return (
    <TubesBackground className="min-h-screen" enableClickInteraction>
      <div className="pointer-events-auto">
        {/* Navigation */}
        <nav className="fixed top-0 inset-x-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/[0.06]">
          <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
            <div className="text-2xl font-extrabold text-gradient">Semantis AI</div>
            <div className="hidden md:flex gap-8">
              <Link to="/docs" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Docs</Link>
              <Link to="/pricing" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Pricing</Link>
              <Link to="/playground" className="text-white/60 hover:text-white text-sm font-medium no-underline transition-colors">Playground</Link>
            </div>
            <div className="flex gap-3">
              <Link to="/signin" className="btn-ghost no-underline">Sign In</Link>
              <Link to="/signup" className="btn-primary no-underline">Get Started</Link>
            </div>
          </div>
        </nav>

        {/* Hero */}
        <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
          <div className="relative z-10 text-center max-w-5xl mx-auto px-8 pt-32 pb-24">
            <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-8 animate-fade-in backdrop-blur-sm">
              Intelligent Semantic Caching for LLMs
            </div>

            <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-[1.08] tracking-tight animate-slide-up"
                style={{ textShadow: '0 0 30px rgba(10,10,11,0.9), 0 0 60px rgba(10,10,11,0.6)' }}>
              Cut Your LLM Costs{' '}
              <span className="text-gradient">By Up To 80%</span>
            </h1>

            <p className="text-lg md:text-xl text-white/70 max-w-3xl mx-auto mb-12 leading-relaxed animate-slide-up drop-shadow-[0_2px_12px_rgba(0,0,0,0.9)]"
               style={{ animationDelay: '0.1s', textShadow: '0 0 20px rgba(10,10,11,1), 0 0 40px rgba(10,10,11,0.8)' }}>
              An intelligent caching layer between your application and LLM providers.
              Reduce costs and latency by serving cached responses for semantically similar queries.
            </p>

            <div className="flex gap-4 justify-center flex-wrap mb-20 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Link to="/signup" className="btn-primary text-lg px-8 py-4 no-underline">
                Start Saving Now &rarr;
              </Link>
              <Link to="/docs" className="btn-ghost text-lg px-8 py-4 no-underline">
                View Documentation
              </Link>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[
                { num: '80%', label: 'Cost Reduction' },
                { num: '<50ms', label: 'Cache Response Time' },
                { num: '100%', label: 'LLM Compatible' },
              ].map((s) => (
                <div key={s.label} className="glass-card gradient-border p-8 text-center backdrop-blur-md">
                  <div className="text-4xl md:text-5xl font-bold text-gradient mb-2">{s.num}</div>
                  <div className="text-white/60 text-sm">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="py-24 px-8 max-w-6xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-white text-center mb-4">How It Works</h2>
          <p className="text-lg text-white/60 text-center mb-16">Simple, fast, and transparent caching</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            {[
              { icon: '1', title: 'Your App Sends Query', text: 'Your application makes an LLM request through Semantis AI', highlighted: false },
              { icon: '2', title: 'Semantis Checks Cache', text: 'We analyze semantic similarity against cached responses', highlighted: true },
              { icon: '3', title: 'Instant Response', text: 'Return cached result or fetch from LLM and cache it', highlighted: false },
            ].map((f) => (
              <div
                key={f.title}
                className={`glass-card p-8 text-center transition-all hover:-translate-y-1 ${
                  f.highlighted ? 'border-blue-500/30 bg-blue-500/[0.06]' : ''
                }`}
              >
                <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-xl">
                  {f.icon}
                </div>
                <h3 className="text-lg font-semibold text-white mb-3">{f.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{f.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section className="py-24 px-8 max-w-6xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-white text-center mb-4">Why Choose Semantis AI?</h2>
          <p className="text-lg text-white/60 text-center mb-16">Built for modern AI applications</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { icon: '📉', title: 'Massive Savings', text: 'Reduce LLM API costs by 60-80%' },
              { icon: '⚡', title: 'Lightning Fast', text: 'Cache hits return in milliseconds' },
              { icon: '🔌', title: 'Plug & Play', text: 'Integrate with just a few lines of code' },
              { icon: '🌐', title: 'Universal', text: 'Works with OpenAI, Anthropic, and more' },
              { icon: '🛡️', title: 'Enterprise Ready', text: 'Secure and built for production' },
              { icon: '🎯', title: 'Smart Matching', text: 'Advanced similarity with typo tolerance' },
              { icon: '👨‍💻', title: 'Developer First', text: 'Great docs, SDKs, and DX' },
              { icon: '📊', title: 'Real-time Analytics', text: 'Track cache performance live' },
            ].map((f) => (
              <div key={f.title} className="glass-card p-6 hover:-translate-y-1 transition-all group">
                <div className="text-3xl mb-3">{f.icon}</div>
                <h3 className="text-base font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">{f.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{f.text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Code Example */}
        <section className="py-24 px-8 max-w-4xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-white text-center mb-4">Start in Minutes</h2>
          <p className="text-lg text-white/60 text-center mb-12">Simple integration with any tech stack</p>

          <div className="glass-card overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 bg-black/30 border-b border-white/[0.06]">
              <div className="flex gap-2">
                <span className="w-3 h-3 rounded-full bg-red-500" />
                <span className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <span className="text-xs text-white/40 font-mono">Python</span>
            </div>
            <pre className="p-6 overflow-auto">
              <code className="text-sm text-white/80 font-mono leading-relaxed">{`from semantis_ai import SemantisClient

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
        <section className="py-24 px-8 max-w-5xl mx-auto">
          <div className="glass-card gradient-border p-16 md:p-20 text-center animate-glow">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Ready to Save on LLM Costs?</h2>
            <p className="text-lg text-white/70 mb-8">Join developers saving thousands on AI infrastructure costs every month.</p>
            <Link to="/signup" className="btn-primary text-lg px-10 py-4 no-underline inline-block">
              Get Started Free &rarr;
            </Link>
            <p className="text-sm text-white/40 mt-4">No credit card required</p>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/[0.06] px-8 py-16">
          <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-10 mb-10">
            <div>
              <div className="text-xl font-bold text-gradient mb-3">Semantis AI</div>
              <p className="text-sm text-white/40 leading-relaxed">Intelligent semantic caching for modern AI applications.</p>
            </div>
            <div className="flex flex-col gap-2.5">
              <h4 className="text-sm font-semibold text-white mb-1">Product</h4>
              <Link to="/docs" className="text-sm text-white/50 no-underline hover:text-white transition-colors">Documentation</Link>
              <Link to="/playground" className="text-sm text-white/50 no-underline hover:text-white transition-colors">Playground</Link>
              <Link to="/pricing" className="text-sm text-white/50 no-underline hover:text-white transition-colors">Pricing</Link>
            </div>
            <div className="flex flex-col gap-2.5">
              <h4 className="text-sm font-semibold text-white mb-1">Resources</h4>
              <a href="https://github.com" className="text-sm text-white/50 no-underline hover:text-white transition-colors" target="_blank" rel="noopener noreferrer">GitHub</a>
              <Link to="/docs" className="text-sm text-white/50 no-underline hover:text-white transition-colors">API Reference</Link>
            </div>
            <div className="flex flex-col gap-2.5">
              <h4 className="text-sm font-semibold text-white mb-1">Company</h4>
              <a href="mailto:contact@semantis.ai" className="text-sm text-white/50 no-underline hover:text-white transition-colors">Contact</a>
              <Link to="/privacy" className="text-sm text-white/50 no-underline hover:text-white transition-colors">Privacy</Link>
            </div>
          </div>
          <div className="max-w-6xl mx-auto pt-8 border-t border-white/[0.06] text-center">
            <p className="text-xs text-white/40">&copy; 2026 Semantis AI. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </TubesBackground>
  );
}
