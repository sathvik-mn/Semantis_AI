import { Link } from 'react-router-dom';
import { Zap, Shield, TrendingDown, Clock, Layers, CheckCircle, ArrowRight, Code, Sparkles } from 'lucide-react';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-8">
            <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Semantis AI
            </div>
            <div className="hidden md:flex gap-6">
              <Link to="/docs" className="text-slate-300 hover:text-white transition-colors">Docs</Link>
              <Link to="/pricing" className="text-slate-300 hover:text-white transition-colors">Pricing</Link>
              <Link to="/playground" className="text-slate-300 hover:text-white transition-colors">Playground</Link>
            </div>
          </div>
          <div className="flex gap-3">
            <Link
              to="/signin"
              className="px-5 py-2 text-slate-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-all font-medium shadow-lg shadow-blue-500/30"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 text-sm font-medium mb-8">
            <Sparkles size={16} />
            <span>Intelligent Semantic Caching for LLMs</span>
          </div>

          <h1 className="text-6xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Cut Your LLM Costs
            <br />
            <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-teal-400 bg-clip-text text-transparent">
              By Up To 80%
            </span>
          </h1>

          <p className="text-xl text-slate-300 mb-10 max-w-3xl mx-auto leading-relaxed">
            Semantis AI is an intelligent caching layer that sits between your application and LLM providers,
            reducing costs and latency by serving cached responses for semantically similar queries.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              to="/signup"
              className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold text-lg transition-all shadow-xl shadow-blue-500/30 flex items-center gap-2"
            >
              Start Saving Now
              <ArrowRight size={20} />
            </Link>
            <Link
              to="/docs"
              className="px-8 py-4 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold text-lg transition-all border border-slate-600 flex items-center gap-2"
            >
              <Code size={20} />
              View Documentation
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20 max-w-4xl mx-auto">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6">
              <div className="text-4xl font-bold text-blue-400 mb-2">80%</div>
              <div className="text-slate-300">Cost Reduction</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6">
              <div className="text-4xl font-bold text-cyan-400 mb-2">&lt;50ms</div>
              <div className="text-slate-300">Cache Response Time</div>
            </div>
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6">
              <div className="text-4xl font-bold text-teal-400 mb-2">100%</div>
              <div className="text-slate-300">LLM Compatible</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">How It Works</h2>
            <p className="text-xl text-slate-300">Simple, fast, and transparent caching</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-8 text-center">
              <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🚀</span>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Your App Sends Query</h3>
              <p className="text-slate-400">Your application makes an LLM request through Semantis AI</p>
            </div>

            <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur border border-blue-500/30 rounded-xl p-8 text-center">
              <div className="w-16 h-16 bg-blue-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Semantis Checks Cache</h3>
              <p className="text-slate-300">We analyze semantic similarity against cached responses</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-8 text-center">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">✓</span>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Instant Response</h3>
              <p className="text-slate-400">Return cached result or fetch from LLM and cache it</p>
            </div>
          </div>

          <div className="bg-slate-800/30 backdrop-blur border border-slate-700/50 rounded-xl p-8">
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">1</div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-2">Query Received</h4>
                    <p className="text-slate-400">Your application sends an LLM query to our API endpoint</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">2</div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-2">Semantic Analysis</h4>
                    <p className="text-slate-400">Advanced algorithms check for semantically similar cached queries</p>
                  </div>
                </div>
              </div>
              <div>
                <div className="flex items-start gap-4 mb-6">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">3</div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-2">Cache Hit</h4>
                    <p className="text-slate-400">Return instant cached response, saving time and money</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-cyan-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">4</div>
                  <div>
                    <h4 className="text-lg font-semibold text-white mb-2">Cache Miss</h4>
                    <p className="text-slate-400">Forward to LLM provider and cache response for future queries</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-slate-900/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Why Choose Semantis AI?</h2>
            <p className="text-xl text-slate-300">Built for modern AI applications</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-blue-500/50 transition-all">
              <TrendingDown className="w-12 h-12 text-blue-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Massive Savings</h3>
              <p className="text-slate-400">Reduce LLM API costs by 60-80% with intelligent caching</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-cyan-500/50 transition-all">
              <Clock className="w-12 h-12 text-cyan-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Lightning Fast</h3>
              <p className="text-slate-400">Cache hits return in milliseconds, not seconds</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-teal-500/50 transition-all">
              <Zap className="w-12 h-12 text-teal-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Plug & Play</h3>
              <p className="text-slate-400">Integrate with just a few lines of code via our SDK</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-green-500/50 transition-all">
              <Layers className="w-12 h-12 text-green-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Universal</h3>
              <p className="text-slate-400">Works with OpenAI, Anthropic, Cohere, and more</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-purple-500/50 transition-all">
              <Shield className="w-12 h-12 text-purple-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Enterprise Ready</h3>
              <p className="text-slate-400">Secure, scalable, and built for production workloads</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-pink-500/50 transition-all">
              <CheckCircle className="w-12 h-12 text-pink-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Smart Matching</h3>
              <p className="text-slate-400">Advanced semantic similarity algorithms with typo tolerance</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-orange-500/50 transition-all">
              <Code className="w-12 h-12 text-orange-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Developer First</h3>
              <p className="text-slate-400">Comprehensive docs, SDKs, and amazing developer experience</p>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-6 hover:border-yellow-500/50 transition-all">
              <Sparkles className="w-12 h-12 text-yellow-400 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Real-time Analytics</h3>
              <p className="text-slate-400">Track cache performance, costs, and usage in real-time</p>
            </div>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Start in Minutes</h2>
            <p className="text-xl text-slate-300">Simple integration with any tech stack</p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur border border-slate-700/50 rounded-xl p-8">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span className="ml-4 text-slate-400 text-sm">Python</span>
            </div>
            <pre className="text-slate-300 overflow-x-auto">
              <code>{`from semantis_ai import SemantisClient

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
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 backdrop-blur border border-blue-500/30 rounded-2xl p-12 text-center">
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Ready to Save on LLM Costs?
            </h2>
            <p className="text-xl text-slate-300 mb-8">
              Join developers saving thousands on AI infrastructure costs every month.
            </p>
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold text-lg transition-all shadow-xl shadow-blue-500/30"
            >
              Get Started Free
              <ArrowRight size={20} />
            </Link>
            <p className="text-slate-400 text-sm mt-4">No credit card required • Free tier available</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="text-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent mb-4">
                Semantis AI
              </div>
              <p className="text-slate-400 text-sm">
                Intelligent semantic caching for modern AI applications.
              </p>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-3">Product</h4>
              <div className="space-y-2">
                <Link to="/docs" className="block text-slate-400 hover:text-white text-sm transition-colors">Documentation</Link>
                <Link to="/playground" className="block text-slate-400 hover:text-white text-sm transition-colors">Playground</Link>
                <Link to="/pricing" className="block text-slate-400 hover:text-white text-sm transition-colors">Pricing</Link>
              </div>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-3">Resources</h4>
              <div className="space-y-2">
                <a href="https://github.com" className="block text-slate-400 hover:text-white text-sm transition-colors">GitHub</a>
                <Link to="/docs" className="block text-slate-400 hover:text-white text-sm transition-colors">API Reference</Link>
                <Link to="/docs" className="block text-slate-400 hover:text-white text-sm transition-colors">Guides</Link>
              </div>
            </div>

            <div>
              <h4 className="text-white font-semibold mb-3">Company</h4>
              <div className="space-y-2">
                <a href="mailto:contact@semantis.ai" className="block text-slate-400 hover:text-white text-sm transition-colors">Contact</a>
                <Link to="/privacy" className="block text-slate-400 hover:text-white text-sm transition-colors">Privacy</Link>
                <Link to="/terms" className="block text-slate-400 hover:text-white text-sm transition-colors">Terms</Link>
              </div>
            </div>
          </div>

          <div className="pt-8 border-t border-slate-700/50 text-center">
            <p className="text-slate-400 text-sm">
              © 2025 Semantis AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
