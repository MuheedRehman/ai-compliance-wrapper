'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import EmptyState from '@/components/empty-state';
import ErrorState from '@/components/error-state';
import Card from '@/components/card';
import { FileSearch, Clock, ShieldCheck, AlertOctagon } from 'lucide-react';

export default function EvidencePage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const params: Record<string, string> = {};
    if (riskFilter) params.risk_level = riskFilter;
    if (decisionFilter) params.decision = decisionFilter;
    api.listLogs(Object.keys(params).length ? params : undefined)
      .then((data) => setLogs(data.logs || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [riskFilter, decisionFilter]);

  useEffect(() => { load(); }, [load]);

  const blockedCount = logs.filter(l => l.decision?.toLowerCase() === 'block').length;
  const highRiskCount = logs.filter(l => l.risk_level?.toLowerCase() === 'high').length;

  return (
    <PageShell 
      title="Evidence Logs" 
      subtitle="Immutable audit trail of all governed AI requests and compliance decisions."
      breadcrumbs={[{ label: 'Evidence' }]}
    >
      <div className="space-y-6">
        {/* KPI Summaries */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card title="Total Events" variant="stat">
            <span className="text-2xl font-bold">{logs.length}</span>
          </Card>
          <Card title="Blocked Requests" variant="stat">
            <span className="text-2xl font-bold text-red-500">{blockedCount}</span>
          </Card>
          <Card title="High Risk detected" variant="stat">
            <span className="text-2xl font-bold text-amber-500">{highRiskCount}</span>
          </Card>
          <Card title="Audit Coverage" variant="stat">
            <span className="text-2xl font-bold text-emerald-500">100%</span>
          </Card>
        </div>

        {/* Filters Card */}
        <Card className="bg-zinc-950 px-6 py-4">
          <div className="flex flex-col md:flex-row md:items-center gap-6">
            <div className="space-y-2 flex-1">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5">
                <AlertOctagon className="h-3 w-3" />
                Risk Classification
              </label>
              <div className="flex flex-wrap gap-2">
                {['', 'high', 'medium', 'low'].map((val) => (
                  <button
                    key={val}
                    onClick={() => setRiskFilter(val)}
                    className={`px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider transition-all
                      ${riskFilter === val ? 'bg-zinc-100 text-black' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'}`}
                  >
                    {val || 'All Risks'}
                  </button>
                ))}
              </div>
            </div>
            <div className="w-px h-10 bg-border hidden md:block" />
            <div className="space-y-2 flex-1">
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5">
                <ShieldCheck className="h-3 w-3" />
                Policy Decision
              </label>
              <div className="flex flex-wrap gap-2">
                {['', 'allow', 'block', 'flag'].map((val) => (
                  <button
                    key={val}
                    onClick={() => setDecisionFilter(val)}
                    className={`px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider transition-all
                      ${decisionFilter === val ? 'bg-zinc-100 text-black' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'}`}
                  >
                    {val || 'All Decisions'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {loading ? (
          <Loading />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : logs.length === 0 ? (
          <EmptyState 
            title="No evidence recorded" 
            message="Logs will populate as AI systems process governed requests."
            icon={FileSearch}
          />
        ) : (
          <Card className="!p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Event ID</th>
                    <th>Feature Identity</th>
                    <th>Compliance Action</th>
                    <th>Risk level</th>
                    <th>Latency</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log: any) => (
                    <tr key={log.event_id} className="group">
                      <td>
                        <div className="flex flex-col">
                          <span className="text-[10px] font-bold text-zinc-300 tracking-wider">
                            {log.event_type}
                          </span>
                          <span className="text-[10px] text-zinc-600 font-mono mt-0.5">{log.event_id?.slice(0, 12)}…</span>
                        </div>
                      </td>
                      <td className="text-[10px] font-mono text-zinc-400">{log.feature_id || '—'}</td>
                      <td><StatusBadge value={log.decision} /></td>
                      <td><StatusBadge value={log.risk_level} /></td>
                      <td className="text-[10px] text-zinc-500 font-bold font-mono">
                        <span className="flex items-center gap-1">
                          <Clock className="h-2.5 w-2.5" />
                          {log.latency_ms != null ? `${log.latency_ms}ms` : '—'}
                        </span>
                      </td>
                      <td className="text-[10px] text-zinc-500 font-bold uppercase whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </PageShell>
  );
}
