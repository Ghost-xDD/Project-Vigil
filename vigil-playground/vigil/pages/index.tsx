import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { ShieldCheck } from 'lucide-react';

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
        <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-violet-600/20 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-72 w-72 rounded-full bg-purple-500/10 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-6xl px-6 py-16 md:py-24">
        <div className="mb-12 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur">
            <div className="h-2 w-2 rounded-full bg-violet-400" />
            <span className="text-xs text-white/70">Project Vigil</span>
          </div>
        </div>

        <div className="flex items-center justify-center">
          <div className="w-full max-w-md">
            <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur p-8 md:p-10 shadow-xl shadow-violet-500/10">
              <div className="flex items-center gap-3 mb-6">
                <div className="h-10 w-10 rounded-xl bg-violet-600/20 border border-violet-500/30 inline-flex items-center justify-center">
                  <ShieldCheck className="w-6 h-6 text-violet-400" />
                </div>
                <div>
                  <div className="text-lg font-semibold">Welcome back</div>
                  <div className="text-sm text-white/60">
                    Sign in to continue
                  </div>
                </div>
              </div>

              <button
                onClick={login}
                disabled={!ready}
                className="w-full px-6 py-4 rounded-xl bg-linear-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 border border-violet-500/30 shadow-lg shadow-violet-500/30 font-semibold text-base disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {ready ? 'Continue with Privy' : 'Loading...'}
              </button>

              <div className="mt-4 text-xs text-white/40 text-center">
                Powered by Privy
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
