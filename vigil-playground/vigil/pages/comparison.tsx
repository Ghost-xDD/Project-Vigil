import Link from 'next/link';
import { TrendingDown, Brain, Activity } from 'lucide-react';

export default function Comparison() {
  const metrics = {
    withML: {
      avgLatency: 94,
      failures: 0,
      p95: 125,
      success: 100,
      cost: 840,
      routingQuality: 94.2,
    },
    withoutML: {
      avgLatency: 156,
      failures: 3,
      p95: 280,
      success: 97,
      cost: 1200,
      routingQuality: 65.0,
    },
  };

  const improvement = {
    latency: (
      ((metrics.withoutML.avgLatency - metrics.withML.avgLatency) /
        metrics.withoutML.avgLatency) *
      100
    ).toFixed(0),
    cost: (
      ((metrics.withoutML.cost - metrics.withML.cost) /
        metrics.withoutML.cost) *
      100
    ).toFixed(0),
    failures: metrics.withoutML.failures - metrics.withML.failures,
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_0%,rgba(88,28,135,0.12),rgba(17,17,23,0.0))]" />
      </div>

      {/* Header */}
      <header className="fixed top-0 inset-x-0 z-50 bg-white/5 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6 text-violet-500" />
              <h1 className="text-xl font-semibold">Comparison</h1>
            </div>
            <nav className="hidden md:flex items-center gap-1 text-xs">
              <Link
                href="/dashboard"
                className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
              >
                Dashboard
              </Link>
              <Link
                href="/chaos"
                className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
              >
                Chaos
              </Link>
              <Link
                href="/comparison"
                className="px-2.5 py-1 rounded-md bg-violet-600/20 border border-violet-500/30 text-violet-200"
              >
                Comparison
              </Link>
              <Link
                href="/playground"
                className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
              >
                Playground
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-6 max-w-5xl mx-auto">
        {/* Title */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-2">Performance Comparison</h1>
          <p className="text-sm text-white/60">
            ML-powered vs traditional routing
          </p>
        </div>

        {/* Side-by-side Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Without ML */}
          <div className="p-6 rounded-xl bg-white/5 border border-white/10">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <TrendingDown className="w-4 h-4 text-white/60" />
              </div>
              <div>
                <h2 className="font-semibold">Traditional RPC</h2>
                <p className="text-xs text-white/50">Round-robin routing</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-white/10">
                <span className="text-xs text-white/60">Avg Latency</span>
                <span className="text-xl font-mono text-white/80">
                  {metrics.withoutML.avgLatency}ms
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-white/10">
                <span className="text-xs text-white/60">P95 Latency</span>
                <span className="text-xl font-mono text-white/80">
                  {metrics.withoutML.p95}ms
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-white/10">
                <span className="text-xs text-white/60">Failures</span>
                <span className="text-xl font-mono text-white/80">
                  {metrics.withoutML.failures}
                </span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-xs text-white/60">Success Rate</span>
                <span className="text-xl font-mono text-white/80">
                  {metrics.withoutML.success}%
                </span>
              </div>
            </div>
          </div>

          {/* With ML */}
          <div className="p-6 rounded-xl bg-violet-500/5 border border-violet-500/20">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center">
                <Brain className="w-4 h-4 text-violet-400" />
              </div>
              <div>
                <h2 className="font-semibold text-violet-200">
                  Vigil ML Routing
                </h2>
                <p className="text-xs text-violet-300/60">Gradient Boosting</p>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-violet-500/10">
                <span className="text-xs text-white/60">Avg Latency</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-mono text-emerald-400">
                    {metrics.withML.avgLatency}ms
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">
                    ↓{improvement.latency}%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-violet-500/10">
                <span className="text-xs text-white/60">P95 Latency</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-mono text-emerald-400">
                    {metrics.withML.p95}ms
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">
                    ↓55%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-violet-500/10">
                <span className="text-xs text-white/60">Failures</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-mono text-emerald-400">
                    {metrics.withML.failures}
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">
                    ✓
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-xs text-white/60">Success Rate</span>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-mono text-emerald-400">
                    {metrics.withML.success}%
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">
                    ↑3%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Impact Grid */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
            <div className="text-3xl font-bold text-emerald-400 mb-1">
              {improvement.latency}%
            </div>
            <div className="text-xs text-white/60">Latency Reduction</div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
            <div className="text-3xl font-bold text-emerald-400 mb-1">100%</div>
            <div className="text-xs text-white/60">Zero Failures</div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-center">
            <div className="text-3xl font-bold text-emerald-400 mb-1">
              ${metrics.withoutML.cost - metrics.withML.cost}
            </div>
            <div className="text-xs text-white/60">Monthly Savings</div>
          </div>
        </div>

        {/* CTA */}
        <div className="p-6 rounded-xl bg-white/5 border border-white/10 text-center">
          <p className="text-sm text-white/60 mb-4">
            Watch ML routing in real-time
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-medium text-sm transition-all"
            >
              <Activity className="w-4 h-4" />
              Dashboard
            </Link>
            <Link
              href="/chaos"
              className="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-white font-medium text-sm transition-all"
            >
              <Activity className="w-4 h-4" />
              Chaos Test
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
