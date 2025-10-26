import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  Activity,
  Zap,
  TrendingUp,
  Brain,
  RefreshCcw,
  Clock,
} from 'lucide-react';
import Link from 'next/link';

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

export default function Dashboard() {
  const [metrics, setMetrics] = useState<NodeMetric[]>([]);
  const [prediction, setPrediction] = useState<RoutingRecommendation | null>(
    null
  );
  const [chartData, setChartData] = useState<
    Array<{ time: string; predicted: number; actual: number }>
  >([]);
  const [stats, setStats] = useState({
    total: 0,
    successRate: 99.97,
    avgLatency: 92,
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('—');
  const [range, setRange] = useState<'5m' | '15m' | '1h'>('15m');
  const [autoPoll, setAutoPoll] = useState<boolean>(true);
  const [pollMs, setPollMs] = useState<number>(2000);
  const [statsLine, setStatsLine] = useState({ mae: 0, mape: 0, acc: 0 });
  interface NodeLog {
    time: string;
    chosen: boolean;
    latency: number;
    success: boolean;
  }
  const [nodeLogs, setNodeLogs] = useState<Record<string, NodeLog[]>>({});

  useEffect(() => {
    // Fetch metrics every 2 seconds
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const dataCollectorUrl =
          process.env.NEXT_PUBLIC_DATA_COLLECTOR_URL || 'http://localhost:8000';
        const mlServiceUrl =
          process.env.NEXT_PUBLIC_ML_SERVICE_URL || 'http://localhost:8001';

        const metricsRes = await fetch(
          `${dataCollectorUrl}/api/v1/metrics/latest-metrics`
        );
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);

        // Get ML prediction
        const limit = range === '5m' ? 20 : range === '15m' ? 60 : 180;
        const historyRes = await fetch(
          `${dataCollectorUrl}/api/v1/metrics/history?limit=${limit}`
        );
        const historyData = await historyRes.json();

        const predictionRes = await fetch(`${mlServiceUrl}/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ metrics: historyData }),
        });
        const predictionData = await predictionRes.json();
        setPrediction(predictionData);

        // Update chart data (mock for now - would track actual vs predicted)
        setChartData((prev) => {
          const newData = [
            ...prev,
            {
              time: new Date().toLocaleTimeString(),
              predicted:
                predictionData.recommendation_details.predicted_latency_ms,
              actual:
                metricsData.find(
                  (m: NodeMetric) =>
                    m.node_name === predictionData.recommended_node
                )?.latency_ms || 0,
            },
          ].slice(-20);
          // compute simple metrics from newData
          if (newData.length >= 2) {
            const errors = newData.map((d) =>
              Math.abs((d.predicted || 0) - (d.actual || 0))
            );
            const mae = errors.reduce((a, b) => a + b, 0) / errors.length;
            const mape =
              (newData
                .map((d) =>
                  d.actual
                    ? Math.abs(
                        ((d.predicted || 0) - (d.actual || 0)) / d.actual
                      )
                    : 0
                )
                .reduce((a, b) => a + b, 0) /
                errors.length) *
              100;
            const withinThreshold = newData.filter(
              (d) => Math.abs((d.predicted || 0) - (d.actual || 0)) <= 15
            ).length;
            const acc = (withinThreshold / newData.length) * 100;
            setStatsLine({ mae, mape: isFinite(mape) ? mape : 0, acc });
          }
          return newData;
        });

        // update per-node logs
        if (predictionData && Array.isArray(predictionData.all_predictions)) {
          const timeStr = new Date().toLocaleTimeString();
          setNodeLogs((prev) => {
            const updated: Record<string, NodeLog[]> = { ...prev };
            predictionData.all_predictions.forEach((p: NodePrediction) => {
              const nodeId = p.node_id;
              const latest = metricsData.find(
                (m: NodeMetric) => m.node_name === nodeId
              );
              const latency = latest?.latency_ms ?? 0;
              const success = (latest?.is_healthy ?? 0) === 1;
              const chosen = predictionData.recommended_node === nodeId;
              const entry: NodeLog = {
                time: timeStr,
                chosen,
                latency,
                success,
              };
              const arr = updated[nodeId]
                ? [entry, ...updated[nodeId]].slice(0, 5)
                : [entry];
              updated[nodeId] = arr;
            });
            return updated;
          });
        }

        setStats((prev) => ({ ...prev, total: prev.total + 1 }));
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (error) {
        console.error('Error fetching data:', error);
        setError('Failed to fetch data. Check services.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    if (!autoPoll) return;
    const interval = setInterval(fetchData, pollMs);
    return () => clearInterval(interval);
  }, [range, autoPoll, pollMs]);

  return (
    <div className="min-h-screen bg-black text-white antialiased">
      {/* Background gradient */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_0%,rgba(88,28,135,0.12),rgba(17,17,23,0.0))]" />
      </div>

      {/* Header */}
      <header className="fixed top-0 inset-x-0 z-50 bg-white/5 backdrop-blur-xl border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6 text-violet-500" />
              <h1 className="text-xl font-semibold">Vigil Dashboard</h1>
            </div>
            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-1 px-2 py-1 rounded-lg bg-white/5 border border-white/10 text-xs">
                <Clock className="w-3.5 h-3.5 text-white/60" />
                <span className="text-white/60">Last updated:</span>
                <span className="text-white/80 font-medium">{lastUpdated}</span>
              </div>
              <div className="hidden md:flex items-center gap-1 text-xs ml-2">
                <button
                  onClick={() => setAutoPoll((v) => !v)}
                  className={`px-2.5 py-1 rounded-md border ${
                    autoPoll
                      ? 'bg-emerald-600 border-emerald-500'
                      : 'bg-white/5 border-white/10'
                  }`}
                  title="Toggle Auto Poll"
                >
                  {autoPoll ? 'Auto' : 'Manual'}
                </button>
                <select
                  value={pollMs}
                  onChange={(e) => setPollMs(parseInt(e.target.value, 10))}
                  className="bg-white/5 border border-white/10 rounded-md px-2 py-1"
                  title="Polling Interval"
                >
                  <option value={1000}>1s</option>
                  <option value={2000}>2s</option>
                  <option value={5000}>5s</option>
                </select>
              </div>
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
              <button
                onClick={() => {
                  // retrigger effect by toggling range to same value
                  setRange((r) => r);
                }}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
                title="Refresh"
              >
                <RefreshCcw
                  className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
                />
                Refresh
              </button>

              <nav className="hidden md:flex items-center gap-1 text-xs mr-2">
                <Link
                  href="/dashboard"
                  className="px-2.5 py-1 rounded-md bg-violet-600/20 border border-violet-500/30 text-violet-200"
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
                  className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
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
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-12 px-6 max-w-7xl mx-auto">
        {/* Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="text-sm text-white/60 mb-1">Total Requests</div>
            <div className="text-3xl font-bold">
              {stats.total.toLocaleString()}
            </div>
          </div>
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="text-sm text-white/60 mb-1">Success Rate</div>
            <div className="text-3xl font-bold text-emerald-400">
              {stats.successRate}%
            </div>
          </div>
          <div className="px-6 py-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="text-sm text-white/60 mb-1">Avg Latency</div>
            <div className="text-3xl font-bold text-violet-400">
              {stats.avgLatency}ms
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Routing Engine Panel */}
          <div className="p-8 rounded-2xl bg-gradient-to-br from-violet-950/40 to-black/60 border-2 border-violet-500/30 backdrop-blur-xl relative overflow-hidden group">
            <div className="absolute -inset-1 bg-gradient-to-br from-violet-600 to-violet-500 opacity-10 group-hover:opacity-20 transition blur-xl" />

            <div className="relative">
              <div className="flex items-center gap-3 mb-6">
                <Zap className="w-6 h-6 text-violet-400" />
                <h2 className="text-xl font-bold">ML Routing Decision</h2>
              </div>

              {prediction ? (
                <div className="space-y-4">
                  <div className="p-6 rounded-xl bg-violet-500/10 border border-violet-500/20">
                    <div className="text-sm text-white/60 mb-2">
                      Recommended Node
                    </div>
                    <div className="text-4xl font-bold text-violet-300 mb-4 animate-pulse">
                      {prediction.recommended_node}
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-white/60">Predicted Latency</div>
                        <div className="text-xl font-semibold text-emerald-400">
                          {prediction.recommendation_details.predicted_latency_ms.toFixed(
                            1
                          )}
                          ms
                        </div>
                      </div>
                      <div>
                        <div className="text-white/60">Failure Probability</div>
                        <div className="text-xl font-semibold text-amber-400">
                          {(
                            prediction.recommendation_details.failure_prob * 100
                          ).toFixed(2)}
                          %
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-white/50 p-4 rounded-lg bg-white/5">
                    {prediction.explanation}
                  </div>
                </div>
              ) : (
                <div className="animate-pulse space-y-4">
                  <div className="h-32 bg-white/5 rounded-xl" />
                  <div className="h-20 bg-white/5 rounded-xl" />
                </div>
              )}
            </div>
          </div>

          {/* Node Health Grid */}
          <div className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center gap-3 mb-6">
              <Activity className="w-6 h-6 text-emerald-400" />
              <h2 className="text-xl font-bold">Node Health</h2>
            </div>

            <div className="space-y-3">
              {metrics.map((node) => {
                const pred = prediction?.all_predictions.find(
                  (p) => p.node_id === node.node_name
                );
                const isRecommended =
                  prediction?.recommended_node === node.node_name;
                const healthColorClass =
                  node.is_healthy === 1 ? 'emerald' : 'red';
                const latencyClamped = Math.max(
                  0,
                  Math.min(500, node.latency_ms)
                );
                const barPercent = Math.round((latencyClamped / 500) * 100);

                return (
                  <div
                    key={node.node_name}
                    className={`p-4 rounded-xl border transition-all ${
                      isRecommended
                        ? 'bg-violet-500/10 border-violet-500/30 shadow-lg shadow-violet-500/20'
                        : 'bg-white/5 border-white/10'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            node.is_healthy === 1 ? 'animate-pulse' : ''
                          } ${
                            healthColorClass === 'emerald'
                              ? 'bg-emerald-500'
                              : 'bg-red-500'
                          }`}
                        />
                        <span className="font-semibold">{node.node_name}</span>
                        {isRecommended && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30">
                            Selected
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-sm font-mono ${
                          healthColorClass === 'emerald'
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {node.latency_ms.toFixed(0)}ms
                      </span>
                    </div>

                    {/* Latency progress bar (0-500ms) */}
                    <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          node.is_healthy === 1
                            ? 'bg-emerald-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${barPercent}%` }}
                      />
                    </div>

                    {pred && (
                      <div className="flex items-center justify-between text-xs text-white/60 mt-2">
                        <span>
                          Predicted: {pred.predicted_latency_ms.toFixed(0)}ms
                        </span>
                        <span>
                          Risk: {(pred.failure_prob * 100).toFixed(2)}%
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Prediction Accuracy Chart */}
          <div className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-bold">Prediction Accuracy</h2>
            </div>

            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
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
                  dot={{ fill: '#8b5cf6', r: 3 }}
                  name="Predicted"
                />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#10b981"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: '#10b981', r: 3 }}
                  name="Actual"
                />
              </LineChart>
            </ResponsiveContainer>

            <div className="mt-4 p-4 rounded-lg bg-white/5 text-sm">
              <div className="flex justify-between text-white/60">
                <span>MAE: {statsLine.mae.toFixed(1)}ms</span>
                <span>MAPE: {statsLine.mape.toFixed(1)}%</span>
                <span className="text-emerald-400">
                  Accuracy: {statsLine.acc.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Feature Importance Panel */}
          <div className="p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center gap-3 mb-6">
              <Brain className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-bold">
                What&apos;s Driving Decisions
              </h2>
            </div>

            <div className="space-y-3">
              {[
                {
                  name: 'error_rate_rolling_mean',
                  value: 8.2,
                  barClass: 'bg-red-500',
                },
                {
                  name: 'cpu_usage_rolling_mean',
                  value: 5.8,
                  barClass: 'bg-amber-500',
                },
                {
                  name: 'memory_pressure',
                  value: 4.1,
                  barClass: 'bg-emerald-500',
                },
                {
                  name: 'disk_io_volatility',
                  value: 3.2,
                  barClass: 'bg-blue-500',
                },
                {
                  name: 'latency_trend',
                  value: 2.9,
                  barClass: 'bg-violet-500',
                },
              ].map((feature) => (
                <div key={feature.name}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm text-white/70">
                      {feature.name}
                    </span>
                    <span className="text-xs text-white/50 font-mono">
                      {feature.value}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${feature.barClass}`}
                      style={{ width: `${feature.value * 10}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <div className="flex items-start gap-2">
                <Zap className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-violet-200">
                  {prediction
                    ? `Error rate spike detected → routing to ${prediction.recommended_node}`
                    : 'Analyzing network conditions...'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* All Nodes Comparison */}
        {prediction && (
          <div className="mt-6 p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <h3 className="text-lg font-bold mb-4">All Node Predictions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {prediction.all_predictions
                .sort((a, b) => a.cost_score - b.cost_score)
                .map((pred, idx) => (
                  <div
                    key={pred.node_id}
                    className={`p-4 rounded-xl border ${
                      idx === 0
                        ? 'bg-emerald-500/10 border-emerald-500/30'
                        : 'bg-white/5 border-white/10'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-3">
                      {idx === 0 && <span className="text-lg">🥇</span>}
                      {idx === 1 && <span className="text-lg">🥈</span>}
                      {idx === 2 && <span className="text-lg">🥉</span>}
                      <span className="text-sm font-semibold truncate">
                        {pred.node_id}
                      </span>
                    </div>
                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-white/60">Latency</span>
                        <span className="font-mono">
                          {pred.predicted_latency_ms.toFixed(0)}ms
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-white/60">Risk</span>
                        <span className="font-mono">
                          {(pred.failure_prob * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-white/60">Score</span>
                        <span className="font-mono text-violet-400">
                          {pred.cost_score.toFixed(4)}
                        </span>
                      </div>
                    </div>
                    {/* Per-node recent routing logs */}
                    <div className="mt-3 p-2 rounded-lg bg-white/5 border border-white/10 max-h-28 overflow-auto">
                      <ul className="space-y-1">
                        {(nodeLogs[pred.node_id] || []).map((log, i) => {
                          const dot = log.success
                            ? 'bg-emerald-500'
                            : 'bg-red-500';
                          return (
                            <li
                              key={i}
                              className="flex items-center justify-between gap-2 text-[11px]"
                            >
                              <div className="flex items-center gap-2">
                                <span
                                  className={`w-1.5 h-1.5 rounded-full ${dot}`}
                                />
                                <span className="text-white/60">
                                  {log.time}
                                </span>
                                {log.chosen && (
                                  <span className="px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-200 border border-violet-500/30">
                                    chosen
                                  </span>
                                )}
                                <span
                                  className={`px-1.5 py-0.5 rounded-full ${
                                    log.success
                                      ? 'bg-emerald-500/15 text-emerald-200 border border-emerald-500/30'
                                      : 'bg-red-500/15 text-red-200 border border-red-500/30'
                                  }`}
                                >
                                  {log.success ? 'ok' : 'fail'}
                                </span>
                              </div>
                              <span className="font-mono text-white/80">
                                {log.latency.toFixed(0)}ms
                              </span>
                            </li>
                          );
                        })}
                        {(!nodeLogs[pred.node_id] ||
                          nodeLogs[pred.node_id].length === 0) && (
                          <li className="text-white/40">No history yet</li>
                        )}
                      </ul>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
