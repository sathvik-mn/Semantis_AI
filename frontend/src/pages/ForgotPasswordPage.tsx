import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, AlertCircle, ArrowLeft } from 'lucide-react';
import { Prism } from '../components/Prism';
import { useAuth } from '../contexts/AuthContext';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { resetPassword } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email) { setError('Please enter your email'); return; }

    setLoading(true);
    try {
      await resetPassword(email);
      setSent(true);
    } catch (err: any) {
      setError(err.message || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-5 relative overflow-hidden">
      <Prism />
      <Link
        to="/signin"
        className="fixed top-6 left-6 z-50 flex items-center justify-center w-11 h-11 rounded-xl
                   bg-white/[0.08] border border-white/[0.12] text-white/80 no-underline
                   backdrop-blur-[10px] hover:bg-white/[0.12] transition-all"
      >
        <ArrowLeft size={20} />
      </Link>

      <div className="max-w-[440px] w-full relative z-10">
        <div className="bg-white/[0.04] border border-white/[0.08] rounded-3xl p-12 backdrop-blur-[40px] shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          {sent ? (
            <div className="text-center">
              <div className="text-5xl mb-4">&#9993;</div>
              <h1 className="text-3xl font-bold text-white mb-2">Check your email</h1>
              <p className="text-white/60 text-sm mb-6">
                We sent a password reset link to <strong className="text-white">{email}</strong>.
              </p>
              <Link to="/signin" className="text-blue-500 font-semibold text-base hover:underline">
                Back to Sign In
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Reset Password</h1>
                <p className="text-sm text-white/60 leading-relaxed">
                  Enter your email and we'll send you a reset link.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <div className="flex flex-col gap-2.5">
                  <label className="flex items-center gap-2 text-sm font-semibold text-white/90">
                    <Mail size={16} /> Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full px-4 py-3.5 text-[15px] bg-black/40 border border-white/[0.15]
                               rounded-xl text-white outline-none focus:border-blue-500 transition-all"
                    required
                    autoFocus
                  />
                </div>

                {error && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/30
                                  rounded-xl text-red-300 text-sm">
                    <AlertCircle size={16} /> {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 text-base font-semibold bg-gradient-to-br from-blue-500 to-blue-600
                             text-white border-none rounded-xl cursor-pointer shadow-[0_4px_16px_rgba(59,130,246,0.4)]
                             hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all mt-2"
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </button>
              </form>

              <div className="mt-8 text-center text-sm text-white/60">
                <Link to="/signin" className="text-blue-500 font-semibold no-underline hover:underline">
                  Back to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
