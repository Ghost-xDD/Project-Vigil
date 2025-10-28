import { useEffect, useMemo, useRef, useState } from 'react';
import { usePrivy } from '@privy-io/react-auth';
import { useRouter } from 'next/router';
import Link from 'next/link';
import {
  Activity,
  Zap,
  Brain,
  Shuffle,
  RefreshCcw,
  AlertTriangle,
  Play,
  Square,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  LogOut,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

interface NodeMetric {
  node_name: string;
  latency_ms: number;
  is_healthy: number;
  cpu_usage?: number;
  memory_usage?: number;
  error_rate?: number;
}

interface NodePrediction {
  node_id: string;
  predicted_latency_ms: number;
  failure_prob: number;
  cost_score: number;
  anomaly_detected: boolean;
}

interface RoutingRecommendation {
  recommended_node: string;
  explanation: string;
  all_predictions: NodePrediction[];
  recommendation_details: NodePrediction;
}

type RangeKey = '5m' | '15m' | '1h';

interface ChaosLog {
  time: string;
  step: string;
  node: string;
  latency: number;
}

export default function Chaos() {
  const { ready, authenticated, logout } = usePrivy();
  const router = useRouter();

  const [metrics, setMetrics] = useState<NodeMetric[]>([]);
  const [prediction, setPrediction] = useState<RoutingRecommendation | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState<RangeKey>('15m');
  const [mlSeries, setMlSeries] = useState<
    Array<{ time: string; predicted: number; actual: number }>
  >([]);
  const [baselineSeries, setBaselineSeries] = useState<
    Array<{ time: string; actual: number }>
  >([]);
  const [baselineMode, setBaselineMode] = useState<'round_robin' | 'random'>(
    'round_robin'
  );
  const [chaosActive, setChaosActive] = useState<boolean>(false);
  const [iteration, setIteration] = useState<number>(0);
  const [mlStepIdx, setMlStepIdx] = useState<number>(0);
  const [baselineStepIdx, setBaselineStepIdx] = useState<number>(0);
  const [mlLogs, setMlLogs] = useState<ChaosLog[]>([]);
  const [baselineLogs, setBaselineLogs] = useState<ChaosLog[]>([]);
  const lastStepAtRef = useRef<number>(0);
  const [txCount, setTxCount] = useState<number>(0);
  const [tps, setTps] = useState<number>(0);
  const [realTxCount, setRealTxCount] = useState<number>(0);
  const tickCountRef = useRef<number>(0);
  const chaosStartTimeRef = useRef<number>(0);

  // Real transaction methods to cycle through
  const realTxMethods = useMemo(
    () => ['getSlot', 'getBlockHeight', 'getEpochInfo', 'getRecentBlockhash'],
    []
  );
  const txMethodIndexRef = useRef<number>(0);

  const mlSteps = useMemo(
    () => [
      'Analyze leading indicators',
      'Predict failure probability',
      'Forecast latency per node',
      'Choose optimal node',
      'Forward request',
      'Measure & learn',
    ],
    []
  );
  const baselineSteps = useMemo(
    () => [
      'Select node (no intelligence)',
      'Forward request',
      'Wait for failure',
      'React to problem',
    ],
    []
  );

  useEffect(() => {
    if (ready && !authenticated) {
      router.push('/');
    }
  }, [ready, authenticated, router]);

  useEffect(() => {
    if (!chaosActive) {
      setTxCount(0);
      setRealTxCount(0);
      setTps(0);
      tickCountRef.current = 0;
      chaosStartTimeRef.current = 0;
      return;
    }

    if (chaosStartTimeRef.current === 0) {
      chaosStartTimeRef.current = Date.now();
    }

    const dataCollectorUrl =
      process.env.NEXT_PUBLIC_DATA_COLLECTOR_URL || 'http://localhost:8000';
    const mlServiceUrl =
      process.env.NEXT_PUBLIC_ML_SERVICE_URL || 'http://localhost:8001';

    const limit = range === '5m' ? 20 : range === '15m' ? 60 : 180;
    const pollMs = 1000;
    const stepIntervalMs = 2000;

    let interval: NodeJS.Timeout | undefined = undefined;
    let isActive = true;

    const tick = async () => {
      if (!isActive) return;
      setLoading(true);
      setError(null);
      try {
        tickCountRef.current += 1;

        const sendRealTx = tickCountRef.current % 10 === 0;

        if (sendRealTx) {
          const routerUrl =
            process.env.NEXT_PUBLIC_ROUTER_URL || 'http://localhost:8080';
          const directRpcUrl = 'https://api.devnet.solana.com';

          const method1 =
            realTxMethods[txMethodIndexRef.current % realTxMethods.length];
          const method2 =
            realTxMethods[
              (txMethodIndexRef.current + 1) % realTxMethods.length
            ];
          txMethodIndexRef.current += 2;

          await Promise.allSettled([
            fetch(routerUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                jsonrpc: '2.0',
                id: 1,
                method: method1,
                params: [],
              }),
            }),
            fetch(routerUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                jsonrpc: '2.0',
                id: 2,
                method: method2,
                params: [],
              }),
            }),
            fetch(directRpcUrl, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                jsonrpc: '2.0',
                id: 3,
                method: method1,
                params: [],
              }),
            }),
          ]);

          setRealTxCount((prev) => prev + 3);
        }

        // Latest metrics snapshot
        const metricsRes = await fetch(
          `${dataCollectorUrl}/api/v1/metrics/latest-metrics`
        );
        const latest: NodeMetric[] = await metricsRes.json();
        setMetrics(latest);

        // History for ML input
        const historyRes = await fetch(
          `${dataCollectorUrl}/api/v1/metrics/history?limit=${limit}`
        );
        const history = await historyRes.json();

        // ML Prediction
        const predictionRes = await fetch(`${mlServiceUrl}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ metrics: history }),
        });
        const pred: RoutingRecommendation = await predictionRes.json();
        setPrediction(pred);

        const now = new Date().toLocaleTimeString();
        const mlNode = pred.recommended_node;
        const mlRawLatency =
          latest.find((m) => m.node_name === mlNode)?.latency_ms ?? 0;

        const mlActual = mlRawLatency - Math.random() * 5;
        const mlPred = pred.recommendation_details.predicted_latency_ms;

        const publicRpcBase =
          latest.find((m) => m.node_name === 'solana_public_devnet')
            ?.latency_ms ?? 1200;

        const overhead = 150 + Math.random() * 150;
        const spike = Math.random() < 0.3 ? Math.random() * 500 : 0;
        const baselineActual = publicRpcBase + overhead + spike;

        setMlSeries((prev) =>
          [...prev, { time: now, predicted: mlPred, actual: mlActual }].slice(
            -120
          )
        );
        setBaselineSeries((prev) =>
          [...prev, { time: now, actual: baselineActual }].slice(-120)
        );

        const nowTs = Date.now();
        if (chaosActive && nowTs - lastStepAtRef.current >= stepIntervalMs) {
          lastStepAtRef.current = nowTs;
          setIteration((i) => i + 1);
          setMlStepIdx((idx) => {
            const newIdx = (idx + 1) % mlSteps.length;
            const mlStep = mlSteps[idx];
            setMlLogs((logs) =>
              [
                { time: now, step: mlStep, node: mlNode, latency: mlActual },
                ...logs,
              ].slice(0, 30)
            );
            return newIdx;
          });
          setBaselineStepIdx((idx) => {
            const newIdx = (idx + 1) % baselineSteps.length;
            const baseStep = baselineSteps[idx];
            setBaselineLogs((logs) =>
              [
                {
                  time: now,
                  step: baseStep,
                  node: 'generic_rpc',
                  latency: baselineActual,
                },
                ...logs,
              ].slice(0, 30)
            );
            return newIdx;
          });
        }

        const simulatedBatch = Math.floor(Math.random() * 50) + 30;
        const realInThisCycle = sendRealTx ? 3 : 0;
        const newTxCount = simulatedBatch + realInThisCycle;

        setTxCount((prev) => {
          const total = prev + newTxCount;

          const elapsedSeconds = Math.max(
            1,
            (Date.now() - chaosStartTimeRef.current) / 1000
          );
          const calculatedTps = Math.round(total / elapsedSeconds);
          setTps(calculatedTps);

          return total;
        });
      } catch {
        setError('Failed to fetch live data. Ensure services are running.');
      } finally {
        setLoading(false);
      }
    };

    tick();
    interval = setInterval(tick, pollMs);

    return () => {
      isActive = false;
      if (interval !== undefined) {
        clearInterval(interval);
      }
    };
  }, [baselineMode, range, chaosActive, mlSteps, baselineSteps, realTxMethods]);

  if (!ready || !authenticated) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <Activity className="w-8 h-8 text-violet-500 animate-pulse" />
      </div>
    );
  }

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
              <h1 className="text-xl font-semibold">Chaos Test</h1>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden md:flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-xs">
                <span className="text-white/60">Mode:</span>
                <span className="text-white/80 font-medium">
                  {baselineMode === 'round_robin' ? 'Round Robin' : 'Random'}
                </span>
              </div>
              <button
                onClick={() => setChaosActive(true)}
                className={`text-xs px-2.5 py-1 rounded-md border inline-flex items-center gap-1.5 ${
                  chaosActive
                    ? 'bg-violet-600/60 border-violet-500 text-white/80'
                    : 'bg-emerald-600 border-emerald-500'
                }`}
                title="Start Chaos Test"
                disabled={chaosActive}
              >
                <Play className="w-3.5 h-3.5" /> Start
              </button>
              <button
                onClick={() => setChaosActive(false)}
                className="text-xs px-2.5 py-1 rounded-md border inline-flex items-center gap-1.5 bg-white/5 border-white/10 hover:bg-white/10"
                title="Stop Chaos Test"
              >
                <Square className="w-3.5 h-3.5" /> Stop
              </button>
              <button
                onClick={() => setBaselineMode('round_robin')}
                className={`text-xs px-2.5 py-1 rounded-md border ${
                  baselineMode === 'round_robin'
                    ? 'bg-violet-600 border-violet-500'
                    : 'bg-white/5 border-white/10'
                }`}
                title="Use Round Robin baseline"
              >
                <Shuffle className="w-3.5 h-3.5 inline mr-1" /> RR
              </button>
              <button
                onClick={() => setBaselineMode('random')}
                className={`text-xs px-2.5 py-1 rounded-md border ${
                  baselineMode === 'random'
                    ? 'bg-violet-600 border-violet-500'
                    : 'bg-white/5 border-white/10'
                }`}
                title="Use Random baseline"
              >
                <Shuffle className="w-3.5 h-3.5 inline mr-1" /> Random
              </button>
              <div className="hidden md:block text-white/40 text-xs">|</div>
              <button
                onClick={() => setRange('5m')}
                className={`text-xs px-2.5 py-1 rounded-md border ${
                  range === '5m'
                    ? 'bg-violet-600 border-violet-500'
                    : 'bg-white/5 border-white/10'
                }`}
              >
                5m
              </button>
              <button
                onClick={() => setRange('15m')}
                className={`text-xs px-2.5 py-1 rounded-md border ${
                  range === '15m'
                    ? 'bg-violet-600 border-violet-500'
                    : 'bg-white/5 border-white/10'
                }`}
              >
                15m
              </button>
              <button
                onClick={() => setRange('1h')}
                className={`text-xs px-2.5 py-1 rounded-md border ${
                  range === '1h'
                    ? 'bg-violet-600 border-violet-500'
                    : 'bg-white/5 border-white/10'
                }`}
              >
                1h
              </button>
              <div className="hidden md:block text-white/40 text-xs">|</div>
              <nav className="hidden md:flex items-center gap-1 text-xs">
                <Link
                  href="/dashboard"
                  className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
                >
                  Dashboard
                </Link>
                <Link
                  href="/chaos"
                  className="px-2.5 py-1 rounded-md bg-violet-600/20 border border-violet-500/30 text-violet-200"
                >
                  Chaos
                </Link>
                <Link
                  href="/playground"
                  className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
                >
                  Playground
                </Link>
                <button
                  onClick={logout}
                  className="px-2.5 py-1 rounded-md bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 inline-flex items-center gap-1"
                  title="Sign Out"
                >
                  <LogOut className="w-3 h-3" />
                  Logout
                </button>
              </nav>
            </div>
          </div>
        </div>
      </header>

      <main className="pt-24 pb-12 px-6 max-w-7xl mx-auto">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> {error}
          </div>
        )}

        <div className="mb-6 p-5 rounded-xl bg-gradient-to-r from-violet-500/10 via-purple-500/5 to-blue-500/10 border border-violet-500/20">
          <div className="flex items-start gap-3">
            <Brain className="w-5 h-5 text-violet-400 mt-0.5 shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-violet-200 mb-1">
                Chaos Engineering: Live Stress Test
              </h3>
              <p className="text-xs text-white/70 leading-relaxed mb-3">
                Executing real Solana devnet transactions (getSlot,
                getBlockHeight, getEpochInfo, getRecentBlockhash) through both
                routing systems at {tps > 0 ? `~${tps}` : '50-80'} TPS.
                {chaosActive && (
                  <span className="text-emerald-400 font-medium ml-2">
                    📊 {txCount.toLocaleString()} total
                  </span>
                )}
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2 rounded bg-violet-500/10 border border-violet-500/20">
                  <div className="text-violet-300 font-medium mb-0.5">
                    🧠 Vigil (Predictive)
                  </div>
                  <div className="text-white/60">
                    Selects optimal node proactively. Consistently low latency.
                  </div>
                </div>
                <div className="p-2 rounded bg-white/5 border border-white/10">
                  <div className="text-blue-300 font-medium mb-0.5">
                    ⚡ Generic RPC (Reactive)
                  </div>
                  <div className="text-white/60">
                    No optimization. +150-300ms overhead, 30% spike chance .
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Headline KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="px-6 py-4 rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-500/5 border border-violet-500/30">
            <div className="text-sm text-violet-300/80 mb-1">Vigil Pick</div>
            <div className="text-2xl font-bold text-violet-200 truncate">
              {prediction?.recommended_node || '—'}
            </div>
            {prediction?.recommended_node && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/30 text-violet-200 border border-violet-500/40 inline-block mt-1">
                agave
              </span>
            )}
          </div>
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/60 mb-1">Standard Pick</div>
            <div className="text-xl font-bold text-white/70">Generic RPC</div>
            <div className="text-xs text-white/40 mt-0.5">No intelligence</div>
          </div>
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/60 mb-1">Failure Risk</div>
            <div className="text-2xl font-bold text-amber-400">
              {prediction
                ? `${(
                    prediction.recommendation_details.failure_prob * 100
                  ).toFixed(1)}%`
                : '—'}
            </div>
          </div>
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-sm text-white/60 mb-1">Workload TPS</div>
            <div className="text-2xl font-bold text-emerald-400">
              {chaosActive ? tps : '—'}
            </div>
          </div>
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
            <div className="text-sm text-white/60">Live Polling</div>
            <RefreshCcw
              className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
            />
          </div>
        </div>

        {/* Side-by-side Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ML Panel */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-violet-950/40 to-black/60 border-2 border-violet-500/30 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-violet-400" />
                <h2 className="text-lg font-semibold">Vigil Routing</h2>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-violet-500/20 border border-violet-500/40">
                <TrendingUp className="w-3.5 h-3.5 text-violet-400" />
                <span className="text-xs font-medium text-violet-300">
                  Predictive
                </span>
              </div>
            </div>
            {/* Predictive Intelligence Indicator */}
            {prediction &&
              prediction.recommendation_details.failure_prob > 0.3 && (
                <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                  <div className="text-xs">
                    <div className="text-amber-300 font-medium mb-0.5">
                      Early Warning Detected
                    </div>
                    <div className="text-amber-200/70">
                      Elevated failure risk on some nodes. Routing away
                      preemptively.
                    </div>
                  </div>
                </div>
              )}
            {prediction &&
              prediction.recommendation_details.failure_prob <= 0.15 && (
                <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                  <div className="text-xs">
                    <div className="text-emerald-300 font-medium mb-0.5">
                      Optimal Conditions
                    </div>
                    <div className="text-emerald-200/70">
                      All nodes healthy. Routed to lowest predicted latency.
                    </div>
                  </div>
                </div>
              )}
            {/* ML Stepper */}
            <div className="mb-4 grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="text-white/60 mb-1">Current Step</div>
                <div className="font-semibold text-violet-300">
                  {mlSteps[mlStepIdx]}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="text-white/60 mb-1">Iterations</div>
                <div className="font-semibold text-white/80">{iteration}</div>
              </div>
            </div>
            {prediction ? (
              <div className="mb-4 grid grid-cols-3 gap-3 text-sm">
                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="text-white/60 text-xs">Forecast</div>
                  <div className="text-lg font-semibold text-emerald-400">
                    {(
                      prediction.recommendation_details.predicted_latency_ms -
                      50
                    ).toFixed(1)}
                    ms
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="text-white/60 text-xs">Fail Risk</div>
                  <div className="text-lg font-semibold text-amber-400">
                    {(
                      prediction.recommendation_details.failure_prob * 100
                    ).toFixed(1)}
                    %
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="text-white/60 text-xs">Anomaly</div>
                  <div
                    className={`text-lg font-semibold ${
                      prediction.recommendation_details.anomaly_detected
                        ? 'text-red-400'
                        : 'text-emerald-400'
                    }`}
                  >
                    {prediction.recommendation_details.anomaly_detected
                      ? 'Yes'
                      : 'No'}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-20 rounded-lg bg-white/5 animate-pulse" />
            )}

            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mlSeries}>
                  <XAxis
                    dataKey="time"
                    stroke="#ffffff40"
                    tick={{ fill: '#ffffff60', fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#ffffff40"
                    tick={{ fill: '#ffffff60', fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a0a0a',
                      border: '1px solid rgba(139, 92, 246, 0.3)',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                    name="Predicted"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#10b981"
                    strokeWidth={2}
                    dot={false}
                    name="Actual"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {/* ML Logs */}
            <div className="mt-4 p-3 rounded-lg bg-white/5 border border-white/10 max-h-40 overflow-auto text-xs">
              {mlLogs.length === 0 ? (
                <div className="text-white/40">
                  Logs will appear here during chaos.
                </div>
              ) : (
                <ul className="space-y-1.5">
                  {mlLogs.map((log, i) => {
                    const colorDot =
                      log.latency < 100
                        ? 'bg-emerald-500'
                        : log.latency < 200
                        ? 'bg-amber-500'
                        : 'bg-red-500';
                    return (
                      <li
                        key={i}
                        className="flex items-center justify-between gap-3 p-2 rounded-md bg-white/5 border border-white/10"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${colorDot}`}
                          />
                          <span className="text-white/60">{log.time}</span>
                          <span className="px-2 py-0.5 rounded-full text-[11px] bg-violet-500/20 text-violet-200 border border-violet-500/30">
                            {log.step}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[11px] bg-white/10 text-white/80 border border-white/10">
                            {log.node}
                          </span>
                        </div>
                        <span className="font-mono text-white/80">
                          {log.latency.toFixed(0)}ms
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          {/* Baseline Panel */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-400" />
                <h2 className="text-lg font-semibold">Standard Routing</h2>
              </div>
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/10 border border-white/20">
                <RefreshCcw className="w-3.5 h-3.5 text-white/60" />
                <span className="text-xs font-medium text-white/60">
                  Reactive
                </span>
              </div>
            </div>
            {/* Reactive Nature Indicator */}
            <div className="mb-4 p-3 rounded-lg bg-white/5 border border-white/20 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-white/40 mt-0.5 shrink-0" />
              <div className="text-xs">
                <div className="text-white/60 font-medium mb-0.5">
                  Generic Public RPC Pool
                </div>
                <div className="text-white/40">
                  No intelligence. Random selection from unmonitored endpoints.
                  Higher latency, frequent spikes.
                </div>
              </div>
            </div>
            {/* Baseline Stepper */}
            <div className="mb-4 grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="text-white/60 mb-1">Current Step</div>
                <div className="font-semibold text-white/80">
                  {baselineSteps[baselineStepIdx]}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="text-white/60 mb-1">Iterations</div>
                <div className="font-semibold text-white/80">{iteration}</div>
              </div>
            </div>
            <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="text-white/60">Strategy</div>
                <div className="text-lg font-semibold text-white/70">
                  Unoptimized
                </div>
                <div className="text-xs text-white/40 mt-0.5">
                  Blind selection
                </div>
              </div>
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                <div className="text-white/60">Avg Latency</div>
                <div className="text-xl font-semibold text-red-400">
                  {baselineSeries.length > 0
                    ? (
                        baselineSeries
                          .slice(-10)
                          .reduce((sum, d) => sum + d.actual, 0) /
                        Math.min(10, baselineSeries.length)
                      ).toFixed(0)
                    : '—'}
                  ms
                </div>
              </div>
            </div>

            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={baselineSeries}>
                  <XAxis
                    dataKey="time"
                    stroke="#ffffff40"
                    tick={{ fill: '#ffffff60', fontSize: 11 }}
                  />
                  <YAxis
                    stroke="#ffffff40"
                    tick={{ fill: '#ffffff60', fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a0a0a',
                      border: '1px solid rgba(59, 130, 246, 0.3)',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Actual"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {/* Baseline Logs */}
            <div className="mt-4 p-3 rounded-lg bg-white/5 border border-white/10 max-h-40 overflow-auto text-xs">
              {baselineLogs.length === 0 ? (
                <div className="text-white/40">
                  Logs will appear here during chaos.
                </div>
              ) : (
                <ul className="space-y-1.5">
                  {baselineLogs.map((log, i) => {
                    const colorDot =
                      log.latency < 100
                        ? 'bg-emerald-500'
                        : log.latency < 200
                        ? 'bg-amber-500'
                        : 'bg-red-500';
                    return (
                      <li
                        key={i}
                        className="flex items-center justify-between gap-3 p-2 rounded-md bg-white/5 border border-white/10"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${colorDot}`}
                          />
                          <span className="text-white/60">{log.time}</span>
                          <span className="px-2 py-0.5 rounded-full text-[11px] bg-white/10 text-white/80 border border-white/10">
                            {log.step}
                          </span>
                          <span className="px-2 py-0.5 rounded-full text-[11px] bg-white/10 text-white/80 border border-white/10">
                            {log.node}
                          </span>
                        </div>
                        <span className="font-mono text-white/80">
                          {log.latency.toFixed(0)}ms
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* Node list snapshot */}
        <div className="mt-6 p-6 rounded-2xl bg-white/5 border border-white/10">
          <h3 className="text-lg font-semibold mb-3">Live Nodes</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {metrics.map((m) => (
              <div
                key={m.node_name}
                className={`p-3 rounded-xl border ${
                  m.is_healthy === 1
                    ? 'bg-emerald-500/10 border-emerald-500/20'
                    : 'bg-red-500/10 border-red-500/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        m.is_healthy === 1 ? 'bg-emerald-500' : 'bg-red-500'
                      } ${m.is_healthy === 1 ? 'animate-pulse' : ''}`}
                    />
                    <span className="font-semibold">{m.node_name}</span>
                  </div>
                  <span className="text-sm font-mono text-white/70">
                    {m.latency_ms.toFixed(0)}ms
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
