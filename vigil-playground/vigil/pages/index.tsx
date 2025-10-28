import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { Activity, Brain, Zap, TrendingUp } from 'lucide-react';

export default function Home() {
  const { ready, authenticated, login } = usePrivy();
  const router = useRouter();

  useEffect(() => {
    if (ready && authenticated) {
      router.push('/dashboard');
    }
  }, [ready, authenticated, router]);

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_0%,rgba(88,28,135,0.12),rgba(17,17,23,0.0))]" />
      </div>

      <div className="flex items-center justify-center min-h-screen px-6">
        <div className="max-w-md text-center">
          <Activity className="w-16 h-16 text-violet-500 mx-auto mb-6 animate-pulse" />

          <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
            Project Vigil
          </h1>

          <p className="text-lg text-white/70 mb-8">
            ML-powered intelligent routing for Solana RPC requests
          </p>

          <div className="grid grid-cols-3 gap-4 mb-8 text-sm">
            <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <Brain className="w-5 h-5 text-violet-400 mx-auto mb-2" />
              <div className="text-white/80">Predictive</div>
            </div>
            <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <Zap className="w-5 h-5 text-violet-400 mx-auto mb-2" />
              <div className="text-white/80">Optimized</div>
            </div>
            <div className="p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <TrendingUp className="w-5 h-5 text-violet-400 mx-auto mb-2" />
              <div className="text-white/80">Intelligent</div>
            </div>
          </div>

          <button
            onClick={login}
            disabled={!ready}
            className="w-full px-8 py-4 rounded-xl bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 border border-violet-500/30 shadow-lg shadow-violet-500/30 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {ready ? 'Sign In to Continue' : 'Loading...'}
          </button>

          <p className="text-xs text-white/40 mt-4">
            Secure authentication powered by Privy
          </p>
        </div>
      </div>
    </div>
  );
}
