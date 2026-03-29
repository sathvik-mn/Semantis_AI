import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-5">
      <div className="text-center max-w-md">
        <div className="text-[120px] font-bold leading-none text-gradient mb-4">
          404
        </div>
        <h1 className="text-2xl font-bold text-white mb-3">Page not found</h1>
        <p className="text-white/60 mb-8 leading-relaxed">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => window.history.back()}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/[0.08] border border-white/[0.12]
                       text-white font-medium cursor-pointer hover:bg-white/[0.12] transition-all"
          >
            <ArrowLeft size={18} /> Go Back
          </button>
          <Link
            to="/"
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white
                       text-[#0a0a0b] font-medium no-underline
                       hover:bg-[#e5e5e5] transition-all"
          >
            <Home size={18} /> Home
          </Link>
        </div>
      </div>
    </div>
  );
}
