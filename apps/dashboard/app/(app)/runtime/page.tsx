'use client';

import { useState, useEffect } from 'react';
import { api, type DeveloperKey, type RuntimeUsage, type PolicyCheckResult } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import {
  Send,
  Terminal,
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  Activity,
  Key,
  BarChart2,
  Copy,
  Check,
  Trash2,
  Plus,
} from 'lucide-react';

type Tab = 'playground' | 'keys' | 'usage';

export default function RuntimePage() {
  const [tab, setTab] = useState<Tab>('playground');

  return (
    <PageShell
      title="Runtime Governance SDK"
      subtitle="Policy enforcement gateway, developer API keys, and runtime usage analytics."
      breadcrumbs={[{ label: 'Runtime SDK' }]}
    >
      <div className="flex gap-1 mb-6 border-b border-border pb-0">
        {([
          { id: 'playground', label: 'Playground', icon: Terminal },
          { id: 'keys', label: 'Developer Keys', icon: Key },
          { id: 'usage', label: 'Usage', icon: BarChart2 },
        ] as { id: Tab; label: string; icon: any }[]).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-[11px] font-bold uppercase tracking-widest border-b-2 transition-all -mb-px ${
              tab === id
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'playground' && <PlaygroundTab />}
      {tab === 'keys' && <DeveloperKeysTab />}
      {tab === 'usage' && <UsageTab />}
    </PageShell>
  );
}

// ---------------------------------------------------------------------------
// Playground tab
// ---------------------------------------------------------------------------

function PlaygroundTab() {
  const [prompt, setPrompt] = useState('Explain what the EU AI Act requires for high-risk AI systems.');
  const [featureId, setFeatureId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PolicyCheckResult | null>(null);
  const [chatResult, setChatResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'policy' | 'chat'>('policy');

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    setChatResult(null);
    setError(null);
    try {
      if (mode === 'policy') {
        const data = await api.policyCheck({
          prompt,
          feature_id: featureId.trim() || undefined,
        });
        setResult(data);
      } else {
        const body: any = { messages: [{ role: 'user', content: prompt }], max_tokens: 300 };
        if (featureId.trim()) body.feature_id = featureId.trim();
        const data = await api.sendChat(body);
        setChatResult(data);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const decisionColor = (d?: string) => {
    if (d === 'allow') return 'text-emerald-500 bg-emerald-500/10';
    if (d === 'block') return 'text-red-500 bg-red-500/10';
    return 'text-amber-500 bg-amber-500/10';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div className="lg:col-span-5 space-y-6">
        <Card title="Request Specification">
          <div className="space-y-6">
            <div className="flex gap-2">
              {(['policy', 'chat'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest transition-all ${
                    mode === m
                      ? 'bg-indigo-600 text-white'
                      : 'bg-zinc-900 text-zinc-500 hover:text-zinc-300 border border-border'
                  }`}
                >
                  {m === 'policy' ? 'Policy Check' : 'Full Chat'}
                </button>
              ))}
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                <Terminal className="h-3 w-3" />
                Governance Context
              </label>
              <div className="space-y-1">
                <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-tight">Feature ID (optional)</span>
                <input
                  value={featureId}
                  onChange={(e) => setFeatureId(e.target.value)}
                  className="w-full rounded-md bg-zinc-950 border border-border px-3 py-2 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all"
                  placeholder="e.g. F-123"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                <Sparkles className="h-3 w-3" />
                Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={6}
                className="w-full rounded-lg bg-zinc-950 border border-border px-4 py-3 text-sm text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 resize-none font-medium leading-relaxed transition-all"
                placeholder="Enter input for policy evaluation..."
              />
            </div>

            <button
              onClick={handleSubmit}
              disabled={loading || !prompt.trim()}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-indigo-600 text-white text-xs font-bold uppercase tracking-widest hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-500/20 active:scale-[0.98]"
            >
              {loading ? <Activity className="h-4 w-4 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
              {loading ? 'PROCESSING...' : 'EXECUTE GOVERNED REQUEST'}
            </button>
          </div>
        </Card>

        <div className="px-4 py-3 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
          <p className="text-[10px] text-indigo-400/70 leading-relaxed font-medium">
            Every request is logged to the immutable Evidence Trail and subject to active policy enforcement.
          </p>
        </div>
      </div>

      <div className="lg:col-span-7 space-y-6">
        <Card title="Policy Analysis">
          {!result && !chatResult && !error && !loading && (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="h-12 w-12 rounded-full border border-zinc-800 flex items-center justify-center mb-4">
                <Terminal className="h-6 w-6 text-zinc-700" />
              </div>
              <h4 className="text-sm font-semibold text-zinc-500">Awaiting Execution</h4>
              <p className="text-xs text-zinc-600 mt-1">Submit a request to trigger policy analysis.</p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center py-24 animate-pulse">
              <Activity className="h-10 w-10 text-indigo-500/40 mb-4" />
              <p className="text-xs font-bold text-zinc-600 uppercase tracking-widest">Evaluating Policy...</p>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-900/20 bg-red-950/5 p-6 flex gap-4">
              <AlertTriangle className="h-5 w-5 text-red-500 shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-red-400 uppercase tracking-tight">Error</h4>
                <p className="text-xs text-red-400/70 mt-1 leading-relaxed font-medium">{error}</p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 rounded-xl border border-border">
                <div className="flex items-center gap-4">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center ${decisionColor(result.decision)}`}>
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Policy Decision</p>
                    <h3 className="text-lg font-bold capitalize">{result.decision}</h3>
                  </div>
                </div>
                {result.risk_level && <StatusBadge value={result.risk_level} />}
              </div>

              <div className="p-4 rounded-xl bg-zinc-950/40 border border-border space-y-1">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Reason</span>
                <p className="text-sm text-zinc-300 leading-relaxed">{result.reason}</p>
              </div>

              {result.feature_name && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-zinc-950/40 border border-border">
                    <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Feature</span>
                    <p className="text-xs text-zinc-300 mt-0.5">{result.feature_name}</p>
                  </div>
                  {result.ai_system_id && (
                    <div className="p-3 rounded-lg bg-zinc-950/40 border border-border">
                      <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">AI System</span>
                      <p className="text-xs font-mono text-zinc-400 mt-0.5 truncate">{result.ai_system_id}</p>
                    </div>
                  )}
                </div>
              )}

              {result.policy_refs.length > 0 && (
                <div className="space-y-2">
                  <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Policy References</span>
                  <div className="flex flex-wrap gap-2">
                    {result.policy_refs.map((ref) => (
                      <span key={ref} className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-900 border border-border text-zinc-400">{ref}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-zinc-950/40 border border-border">
                  <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Check ID</span>
                  <p className="text-[10px] font-mono text-zinc-400 mt-0.5">{result.check_id}</p>
                </div>
                <div className="p-3 rounded-lg bg-zinc-950/40 border border-border">
                  <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Latency</span>
                  <p className="text-xs text-zinc-300 mt-0.5">{result.latency_ms} ms</p>
                </div>
              </div>
            </div>
          )}

          {chatResult && (
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 rounded-xl border border-border bg-zinc-950/40">
                <div className="flex items-center gap-4">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center ${decisionColor(chatResult.compliance?.decision)}`}>
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Policy Outcome</p>
                    <h3 className="text-lg font-bold capitalize">{chatResult.compliance?.decision || chatResult.status}</h3>
                  </div>
                </div>
                <StatusBadge value={chatResult.compliance?.risk_level || 'UNKNOWN'} />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2 px-1">
                  <Sparkles className="h-3 w-3" />
                  Model Response
                </label>
                <div className="rounded-xl bg-zinc-950 border border-border p-5 shadow-inner">
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed font-medium italic">
                    {chatResult.output || chatResult.message || 'No response data.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Developer Keys tab
// ---------------------------------------------------------------------------

function DeveloperKeysTab() {
  const [keys, setKeys] = useState<DeveloperKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await api.listDeveloperKeys();
      setKeys(data);
    } catch {
      // non-fatal
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const created = await api.createDeveloperKey({ name: newName.trim(), description: newDesc.trim() || undefined });
      setNewKey(created.raw_key ?? null);
      setShowForm(false);
      setNewName('');
      setNewDesc('');
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId: string) => {
    try {
      await api.revokeDeveloperKey(keyId);
      setKeys((prev) => prev.map((k) => k.key_id === keyId ? { ...k, revoked: true } : k));
    } catch {
      // non-fatal
    }
  };

  const copy = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {newKey && (
        <div className="p-4 rounded-xl border border-emerald-900/30 bg-emerald-950/10">
          <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2">
            Key created - copy it now, it will not be shown again.
          </p>
          <div className="flex items-center gap-3 bg-zinc-950 border border-border rounded-lg px-4 py-2">
            <code className="flex-1 text-xs text-emerald-400 font-mono truncate">{newKey}</code>
            <button onClick={copy} className="shrink-0 text-zinc-400 hover:text-white transition-colors">
              {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
            </button>
          </div>
          <button onClick={() => setNewKey(null)} className="mt-3 text-[10px] text-zinc-500 hover:text-zinc-300 font-bold uppercase tracking-widest">
            Dismiss
          </button>
        </div>
      )}

      <Card
        title="Developer API Keys"
        actions={
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-indigo-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-indigo-500 transition-all"
          >
            <Plus className="h-3 w-3" />
            New Key
          </button>
        }
      >
        {showForm && (
          <div className="mb-6 p-4 rounded-xl border border-border bg-zinc-950/40 space-y-3">
            <h4 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Create Developer Key</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-tight">Name *</span>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full rounded-md bg-zinc-900 border border-border px-3 py-2 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
                  placeholder="e.g. production-sdk"
                />
              </div>
              <div className="space-y-1">
                <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-tight">Description</span>
                <input
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full rounded-md bg-zinc-900 border border-border px-3 py-2 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
                  placeholder="Optional"
                />
              </div>
            </div>
            {error && <p className="text-[10px] text-red-400">{error}</p>}
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={creating || !newName.trim()}
                className="px-4 py-2 rounded-md bg-indigo-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-indigo-500 disabled:opacity-50 transition-all"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
              <button
                onClick={() => { setShowForm(false); setError(null); }}
                className="px-4 py-2 rounded-md bg-zinc-800 text-zinc-400 text-[10px] font-bold uppercase tracking-widest hover:bg-zinc-700 transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="py-12 flex justify-center">
            <Activity className="h-6 w-6 text-indigo-500/40 animate-spin" />
          </div>
        ) : keys.length === 0 ? (
          <div className="py-12 text-center">
            <Key className="h-8 w-8 text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">No developer keys yet.</p>
            <p className="text-xs text-zinc-600 mt-1">Create a key to use the Runtime Governance SDK from your application.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {keys.map((k) => (
              <div key={k.key_id} className={`flex items-start justify-between p-4 rounded-xl border ${k.revoked ? 'border-border opacity-50' : 'border-border bg-zinc-950/30'}`}>
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-zinc-200">{k.name}</span>
                    {k.revoked && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-red-950/30 text-red-400 border border-red-900/30">
                        Revoked
                      </span>
                    )}
                  </div>
                  {k.description && <p className="text-xs text-zinc-500">{k.description}</p>}
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-[10px] font-mono text-zinc-600">{k.key_id}</span>
                    {k.last_used_at ? (
                      <span className="text-[10px] text-zinc-600">
                        Last used {new Date(k.last_used_at).toLocaleDateString()}
                      </span>
                    ) : !k.revoked ? (
                      <span className="text-[10px] text-zinc-700">Never used</span>
                    ) : null}
                  </div>
                </div>
                {!k.revoked && (
                  <button
                    onClick={() => handleRevoke(k.key_id)}
                    className="shrink-0 ml-4 p-2 rounded-lg text-zinc-600 hover:text-red-400 hover:bg-red-950/20 transition-all"
                    title="Revoke key"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      <div className="p-4 bg-zinc-900/40 border border-border rounded-xl space-y-2">
        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">SDK Quick Start</p>
        <pre className="text-[11px] text-zinc-400 font-mono leading-relaxed overflow-x-auto">{`import requests

response = requests.post(
    "https://your-backend/v1/runtime/policy-check",
    headers={"x-api-key": "aigw_<your_key>"},
    json={"prompt": "...", "feature_id": "F-123"}
)
result = response.json()
# { "decision": "allow", "reason": "...", "check_id": "chk-..." }`}</pre>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Usage tab
// ---------------------------------------------------------------------------

function UsageTab() {
  const [usage, setUsage] = useState<RuntimeUsage | null>(null);
  const [days, setDays] = useState(7);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getRuntimeUsage(days)
      .then(setUsage)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return (
      <div className="py-24 flex justify-center">
        <Activity className="h-6 w-6 text-indigo-500/40 animate-spin" />
      </div>
    );
  }

  const maxBar = usage ? Math.max(...usage.daily.map((d) => d.total), 1) : 1;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <div className="flex gap-1">
          {([7, 30] as const).map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-widest transition-all ${
                days === d
                  ? 'bg-indigo-600 text-white'
                  : 'bg-zinc-900 text-zinc-500 hover:text-zinc-300 border border-border'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {!usage || usage.total_checks === 0 ? (
        <div className="py-24 text-center">
          <BarChart2 className="h-10 w-10 text-zinc-700 mx-auto mb-4" />
          <p className="text-sm text-zinc-500">No policy checks in the last {days} days.</p>
          <p className="text-xs text-zinc-600 mt-1">Use the Playground or SDK to generate activity.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Checks', value: usage.total_checks, color: 'text-zinc-200' },
              { label: 'Allowed', value: usage.allow_count, color: 'text-emerald-400' },
              { label: 'Blocked', value: usage.block_count, color: 'text-red-400' },
              { label: 'Under Review', value: usage.review_count, color: 'text-amber-400' },
            ].map(({ label, value, color }) => (
              <div key={label} className="p-4 rounded-xl border border-border bg-zinc-950/30">
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{label}</p>
                <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
              </div>
            ))}
          </div>

          <Card title="Daily Activity">
            <div className="space-y-2">
              {usage.daily.map((d) => (
                <div key={d.date} className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-zinc-500 w-20 shrink-0">{d.date}</span>
                  <div className="flex-1 h-5 rounded bg-zinc-900 overflow-hidden flex">
                    {d.allow > 0 && (
                      <div
                        className="h-full bg-emerald-600/70"
                        style={{ width: `${(d.allow / maxBar) * 100}%` }}
                        title={`Allow: ${d.allow}`}
                      />
                    )}
                    {d.block > 0 && (
                      <div
                        className="h-full bg-red-600/70"
                        style={{ width: `${(d.block / maxBar) * 100}%` }}
                        title={`Block: ${d.block}`}
                      />
                    )}
                    {d.review > 0 && (
                      <div
                        className="h-full bg-amber-500/70"
                        style={{ width: `${(d.review / maxBar) * 100}%` }}
                        title={`Review: ${d.review}`}
                      />
                    )}
                  </div>
                  <span className="text-[10px] text-zinc-500 w-8 text-right shrink-0">{d.total}</span>
                </div>
              ))}
            </div>
            <div className="flex gap-4 mt-4 pt-4 border-t border-border">
              {[
                { color: 'bg-emerald-600/70', label: 'Allow' },
                { color: 'bg-red-600/70', label: 'Block' },
                { color: 'bg-amber-500/70', label: 'Review' },
              ].map(({ color, label }) => (
                <div key={label} className="flex items-center gap-1.5">
                  <div className={`h-2.5 w-2.5 rounded-sm ${color}`} />
                  <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">{label}</span>
                </div>
              ))}
            </div>
          </Card>

          {usage.top_features.length > 0 && (
            <Card title="Top Features by Policy Checks">
              <div className="space-y-2">
                {usage.top_features.map((f) => (
                  <div key={f.feature_id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-950/40 border border-border">
                    <span className="text-xs font-mono text-zinc-300">{f.feature_id}</span>
                    <span className="text-xs font-bold text-zinc-400">{f.check_count} checks</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
