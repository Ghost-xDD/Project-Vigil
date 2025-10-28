import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { Activity } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { ready, authenticated, login } = usePrivy();
  const router = useRouter();

  useEffect(() => {
    if (ready && !authenticated && router.pathname !== '/') {
      router.push('/');
    }
  }, [ready, authenticated, router]);

  if (!ready) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-8 h-8 text-violet-500 animate-pulse mx-auto mb-4" />
          <p className="text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  if (!authenticated && router.pathname !== '/') {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-violet-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Authentication Required</h1>
          <p className="text-white/60 mb-6">Please log in to access Vigil</p>
          <button
            onClick={login}
            className="px-6 py-3 rounded-lg bg-violet-600 hover:bg-violet-500 border border-violet-500/30"
          >
            Log In
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
