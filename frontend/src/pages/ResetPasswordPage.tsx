import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, AlertCircle, Check, X } from 'lucide-react';
import { Prism } from '../components/Prism';
import { useAuth } from '../contexts/AuthContext';

export function ResetPasswordPage() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const { updatePassword } = useAuth();
  const navigate = useNavigate();

  const checks = {
    length: password.length >= 8,
    hasLetter: /[a-zA-Z]/.test(password),
    hasNumber: /[0-9]/.test(password),
  };
  const isValid = Object.values(checks).every(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!isValid) { setError('Please meet all password requirements'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match'); return; }

    setLoading(true);
    try {
      await updatePassword(password);
      setDone(true);
      setTimeout(() => navigate('/signin'), 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-5 relative overflow-hidden">
      <Prism />
      <div className="max-w-[440px] w-full relative z-10">
        <div className="bg-white/[0.04] border border-white/[0.08] rounded-3xl p-12 backdrop-blur-[40px] shadow-[0_8px_32px_rgba(0,0,0,0.4)]">
          {done ? (
            <div className="text-center">
              <div className="text-5xl mb-4">&#10003;</div>
              <h1 className="text-3xl font-bold text-white mb-2">Password Updated</h1>
              <p className="text-white/60 text-sm">Redirecting to sign in...</p>
            </div>
          ) : (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">New Password</h1>
                <p className="text-sm text-white/60">Choose a new password for your account.</p>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <div className="flex flex-col gap-2.5">
                  <label className="flex items-center gap-2 text-sm font-semibold text-white/90">
                    <Lock size={16} /> New Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter new password"
                    className="w-full px-4 py-3.5 text-[15px] bg-black/40 border border-white/[0.15]
                               rounded-xl text-white outline-none focus:border-blue-500 transition-all"
                    required
                    autoFocus
                  />
                  {password && (
                    <div className="mt-2 p-3 bg-black/30 border border-white/10 rounded-lg flex flex-col gap-1.5">
                      {[
                        { ok: checks.length, label: 'At least 8 characters' },
                        { ok: checks.hasLetter, label: 'Contains a letter' },
                        { ok: checks.hasNumber, label: 'Contains a number' },
                      ].map((c) => (
                        <div key={c.label} className="flex items-center gap-2">
                          {c.ok ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-red-500" />}
                          <span className={`text-[13px] ${c.ok ? 'text-emerald-500' : 'text-red-500'}`}>{c.label}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2.5">
                  <label className="flex items-center gap-2 text-sm font-semibold text-white/90">
                    <Lock size={16} /> Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    className="w-full px-4 py-3.5 text-[15px] bg-black/40 border border-white/[0.15]
                               rounded-xl text-white outline-none focus:border-blue-500 transition-all"
                    required
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
                  {loading ? 'Updating...' : 'Update Password'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
