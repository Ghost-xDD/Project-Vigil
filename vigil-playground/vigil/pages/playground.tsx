import { useMemo, useState } from 'react';
import Link from 'next/link';
import { Activity, Send, Terminal, Zap } from 'lucide-react';

export default function Playground() {
  const [endpoint, setEndpoint] = useState<string>(
    process.env.NEXT_PUBLIC_ROUTER_URL || 'http://localhost:8080'
  );
  const [method, setMethod] = useState<string>('getHealth');
  const [customMethod, setCustomMethod] = useState<string>('getHealth');
  const [account, setAccount] = useState<string>('');
  const [params, setParams] = useState<string>('[]');
  const [result, setResult] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [statusCode, setStatusCode] = useState<number | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');

  const send = async () => {
    setLoading(true);
    setResult('');
    setErrorMsg('');
    try {
      const chosenMethod = method === 'custom' ? customMethod : method;
      let builtParams: unknown[] = [];
      try {
        if (method === 'getBalance') {
          builtParams = account ? [account, { commitment: 'finalized' }] : [];
        } else if (
          method === 'getHealth' ||
          method === 'getSlot' ||
          method === 'getBlockHeight'
        ) {
          builtParams = [];
        } else {
          builtParams = JSON.parse(params || '[]');
        }
      } catch {
        setErrorMsg('Params JSON is invalid');
        setLoading(false);
        return;
      }

      const body = {
        jsonrpc: '2.0',
        id: 1,
        method: chosenMethod,
        params: method === 'custom' ? JSON.parse(params || '[]') : builtParams,
      };
      const started = performance.now();
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const ended = performance.now();
      setStatusCode(res.status);
      setDurationMs(Math.max(0, ended - started));
      const text = await res.text();
      setResult(text);
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const presetOptions = useMemo(
    () => [
      { key: 'getHealth', label: 'getHealth' },
      { key: 'getSlot', label: 'getSlot' },
      { key: 'getBlockHeight', label: 'getBlockHeight' },
      { key: 'getBalance', label: 'getBalance' },
      { key: 'custom', label: 'Custom' },
    ],
    []
  );

  const requestPreview = useMemo(() => {
    const chosenMethod = method === 'custom' ? customMethod : method;
    let builtParams: unknown[] | string = [];
    try {
      if (method === 'getBalance') {
        builtParams = account ? [account, { commitment: 'finalized' }] : [];
      } else if (
        method === 'getHealth' ||
        method === 'getSlot' ||
        method === 'getBlockHeight'
      ) {
        builtParams = [];
      } else {
        builtParams = JSON.parse(params || '[]');
      }
    } catch {
      builtParams = 'Invalid JSON';
    }
    const body = {
      jsonrpc: '2.0',
      id: 1,
      method: chosenMethod,
      params: builtParams,
    };
    try {
      return JSON.stringify(body, null, 2);
    } catch {
      return String(body);
    }
  }, [method, customMethod, params, account]);

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
              <h1 className="text-xl font-semibold">Playground</h1>
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
                className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 hover:bg-white/10"
              >
                Comparison
              </Link>
              <Link
                href="/playground"
                className="px-2.5 py-1 rounded-md bg-violet-600/20 border border-violet-500/30 text-violet-200"
              >
                Playground
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="pt-24 pb-12 px-6 max-w-5xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Request Panel */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-violet-950/40 to-black/60 border-2 border-violet-500/30 backdrop-blur-xl">
            <div className="flex items-center gap-2 mb-4">
              <Terminal className="w-5 h-5 text-violet-400" />
              <h2 className="text-lg font-semibold">Solana JSON-RPC</h2>
            </div>
            <div className="space-y-3 text-sm">
              <label className="block">
                <div className="text-white/70 mb-1">RPC Endpoint</div>
                <input
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-violet-500"
                  placeholder="http://localhost:8080"
                />
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="block">
                  <div className="text-white/70 mb-1">Method</div>
                  <select
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-violet-500"
                  >
                    {presetOptions.map((opt) => (
                      <option key={opt.key} value={opt.key}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
                {method === 'custom' ? (
                  <label className="block">
                    <div className="text-white/70 mb-1">Custom Method</div>
                    <input
                      value={customMethod}
                      onChange={(e) => setCustomMethod(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-violet-500"
                      placeholder="method name"
                    />
                  </label>
                ) : (
                  <label className="block">
                    <div className="text-white/70 mb-1">
                      Account (optional for getBalance)
                    </div>
                    <input
                      value={account}
                      onChange={(e) => setAccount(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-violet-500"
                      placeholder="Enter base58 public key"
                    />
                  </label>
                )}
              </div>

              <label className="block">
                <div className="text-white/70 mb-1">Params (JSON)</div>
                <textarea
                  value={params}
                  onChange={(e) => setParams(e.target.value)}
                  className="w-full h-28 bg-white/5 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-1 focus:ring-violet-500 font-mono text-xs"
                  placeholder="[] or [args]"
                />
                <div className="text-[11px] text-white/40 mt-1">
                  Used when Method is Custom.
                </div>
              </label>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <div className="text-white/70 mb-1">Request Preview</div>
                  <pre className="h-36 overflow-auto bg-black/60 border border-white/10 rounded-md p-3 text-xs whitespace-pre-wrap break-all">
                    {requestPreview}
                  </pre>
                </div>
                <div>
                  <div className="text-white/70 mb-1">Status</div>
                  <div className="p-3 rounded-md bg-white/5 border border-white/10 text-xs flex items-center justify-between gap-2">
                    <span className="text-white/60">HTTP</span>
                    <span
                      className={`font-mono ${
                        statusCode && statusCode >= 200 && statusCode < 300
                          ? 'text-emerald-400'
                          : 'text-white/80'
                      }`}
                    >
                      {statusCode ?? '—'}
                    </span>
                    <span className="text-white/60">Time</span>
                    <span className="font-mono text-white/80">
                      {durationMs ? `${durationMs.toFixed(0)}ms` : '—'}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={send}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-500 hover:to-violet-400 border border-violet-500/30 shadow-lg shadow-violet-500/30"
                disabled={loading}
              >
                <Send className={`w-4 h-4 ${loading ? 'animate-pulse' : ''}`} />
                Send Request
              </button>
              <p className="text-xs text-white/50">
                Tip: Use the router endpoint to observe Vigil routing in action.
              </p>
              {errorMsg && (
                <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/20 rounded-md p-2">
                  {errorMsg}
                </div>
              )}
            </div>
          </div>

          {/* Response Panel */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-semibold">Response</h2>
            </div>
            <pre className="h-[420px] overflow-auto bg-black/60 border border-white/10 rounded-md p-4 text-xs whitespace-pre-wrap break-all">
              {result
                ? (() => {
                    try {
                      return JSON.stringify(JSON.parse(result), null, 2);
                    } catch {
                      return result;
                    }
                  })()
                : 'Response will appear here'}
            </pre>
          </div>
        </div>
      </main>
    </div>
  );
}
