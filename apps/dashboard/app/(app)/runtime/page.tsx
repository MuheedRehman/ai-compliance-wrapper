'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import { Send, Terminal, Sparkles, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

export default function RuntimePage() {
  const [prompt, setPrompt] = useState('Explain what the EU AI Act requires for high-risk AI systems.');
  const [featureId, setFeatureId] = useState('');
  const [model, setModel] = useState('');
  const [maxTokens, setMaxTokens] = useState(300);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const body: any = {
        messages: [{ role: 'user', content: prompt }],
        max_tokens: maxTokens,
      };
      if (featureId.trim()) body.feature_id = featureId.trim();
      if (model.trim()) body.model = model.trim();

      const data = await api.sendChat(body);
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageShell 
      title="Compliance Playground" 
      subtitle="Execute governed AI requests to validate policy enforcement and risk detection."
      breadcrumbs={[{ label: 'Playground' }]}
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Input Controls */}
        <div className="lg:col-span-5 space-y-6">
          <Card title="Request Specification">
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                  <Terminal className="h-3 w-3" />
                  Governance Context
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-tight">Feature Identity</span>
                    <input
                      value={featureId}
                      onChange={(e) => setFeatureId(e.target.value)}
                      className="w-full rounded-md bg-zinc-950 border border-border px-3 py-2 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all"
                      placeholder="e.g. F-123"
                    />
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-tight">Override Model</span>
                    <input
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="w-full rounded-md bg-zinc-950 border border-border px-3 py-2 text-xs text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition-all"
                      placeholder="Auto-select"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                  <Sparkles className="h-3 w-3" />
                  System Prompt
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={6}
                  className="w-full rounded-lg bg-zinc-950 border border-border px-4 py-3 text-sm text-zinc-200 placeholder-zinc-700 focus:outline-none focus:ring-1 focus:ring-indigo-500/30 resize-none font-medium leading-relaxed transition-all"
                  placeholder="Enter input for governed processing…"
                />
              </div>

              <div className="pt-2">
                <button
                  onClick={handleSubmit}
                  disabled={loading || !prompt.trim()}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-indigo-600 text-white text-xs font-bold uppercase tracking-widest hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-500/20 active:scale-[0.98]"
                >
                  {loading ? (
                    <Activity className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-3.5 w-3.5" />
                  )}
                  {loading ? 'PROCESSING THROUGH GATEWAY...' : 'EXECUTE GOVERNED REQUEST'}
                </button>
              </div>
            </div>
          </Card>
          
          <div className="px-4 py-3 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
            <p className="text-[10px] text-indigo-400/70 leading-relaxed font-medium">
              Note: Every request submitted via this playground is logged in the immutable Evidence Trail and subject to active policy enforcement.
            </p>
          </div>
        </div>

        {/* Output & Analysis */}
        <div className="lg:col-span-7 space-y-6">
          <Card title="Operational Analysis">
            {!result && !error && !loading && (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="h-12 w-12 rounded-full border border-zinc-800 flex items-center justify-center mb-4">
                  <Terminal className="h-6 w-6 text-zinc-700" />
                </div>
                <h4 className="text-sm font-semibold text-zinc-500">Awaiting Input Execution</h4>
                <p className="text-xs text-zinc-600 mt-1">Submit a request to trigger policy analysis.</p>
              </div>
            )}
            
            {loading && (
              <div className="flex flex-col items-center justify-center py-24 animate-pulse">
                <Activity className="h-10 w-10 text-indigo-500/40 mb-4" />
                <p className="text-xs font-bold text-zinc-600 uppercase tracking-widest">Intercepting Request...</p>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-red-900/20 bg-red-950/5 p-6 flex gap-4">
                <AlertTriangle className="h-5 w-5 text-red-500 shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-red-400 uppercase tracking-tight">Gateway Denial</h4>
                  <p className="text-xs text-red-400/70 mt-1 leading-relaxed font-medium">{error}</p>
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-8 animate-slide-up">
                {/* Decision Header */}
                <div className="flex items-center justify-between p-4 rounded-xl border border-border bg-zinc-950/40">
                  <div className="flex items-center gap-4">
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center ${result.compliance?.decision === 'allow' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                      <ShieldCheck className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Policy Outcome</p>
                      <h3 className="text-lg font-bold capitalize">{result.compliance?.decision || result.status}</h3>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1.5">
                    <StatusBadge value={result.compliance?.risk_level || 'UNKNOWN'} />
                    <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-tighter">RISK RATING</span>
                  </div>
                </div>

                {/* Model Output */}
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2 px-1">
                    <Sparkles className="h-3 w-3" />
                    Sanitized Model Response
                  </label>
                  <div className="rounded-xl bg-zinc-950 border border-border p-5 shadow-inner">
                    <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed font-medium italic">
                      {result.output || result.message || 'No response data available.'}
                    </p>
                  </div>
                </div>

                {/* Technical Audit */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1 p-3 rounded-lg bg-zinc-950/40 border border-border">
                    <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Request ID</span>
                    <p className="text-[10px] font-mono text-zinc-400 truncate">{result.request_id}</p>
                  </div>
                  <div className="space-y-1 p-3 rounded-lg bg-zinc-950/40 border border-border">
                    <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Audit Event</span>
                    <p className="text-[10px] font-mono text-zinc-400 truncate">{result.evidence?.event_id || 'N/A'}</p>
                  </div>
                </div>

                {/* Policy Violations */}
                {result.compliance?.rule_results?.length > 0 && (
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold text-red-500/70 uppercase tracking-widest flex items-center gap-2 px-1">
                      <AlertTriangle className="h-3 w-3" />
                      Policy Violations Detected
                    </label>
                    <div className="space-y-2">
                      {result.compliance.rule_results.map((rule: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-red-900/20 bg-red-950/5">
                          <span className="text-[10px] font-bold text-red-400/80 font-mono tracking-widest uppercase">{rule.rule_id}</span>
                          <StatusBadge value={rule.severity || rule.action} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </PageShell>
  );
}
