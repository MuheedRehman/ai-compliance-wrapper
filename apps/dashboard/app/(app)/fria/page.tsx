'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import { ShieldCheck, Plus, ArrowRight, ClipboardList, AlertCircle, X, CheckCircle2 } from 'lucide-react';

function CompletionBar({ percent }: { percent: number }) {
  const color = percent === 100 ? 'bg-emerald-500' : percent >= 50 ? 'bg-indigo-500' : 'bg-zinc-600';
  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${percent}%` }} />
      </div>
      <span className="text-[10px] font-bold text-zinc-500 tabular-nums w-8 text-right">{percent}%</span>
    </div>
  );
}

function CreateFriaPanel({ onCreated, onClose }: { onCreated: (fria: any) => void; onClose: () => void }) {
  const [systems, setSystems] = useState<any[]>([]);
  const [systemId, setSystemId] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listSystems().then(setSystems).catch(() => {});
  }, []);

  const handleCreate = async () => {
    if (!systemId) { setError('Select an AI system.'); return; }
    setSaving(true);
    setError(null);
    try {
      const fria = await api.createFria({ ai_system_id: systemId });
      onCreated(fria);
    } catch {
      setError('Failed to create FRIA. Check entitlement or try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card title="New FRIA Assessment">
      <div className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">AI System</label>
          <select
            value={systemId}
            onChange={e => setSystemId(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Select a system…</option>
            {systems.map(s => (
              <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
            ))}
          </select>
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
        <div className="flex gap-2">
          <button
            onClick={handleCreate}
            disabled={saving}
            className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors disabled:opacity-50"
          >
            {saving ? 'Creating…' : 'Create FRIA'}
          </button>
          <button onClick={onClose} className="px-3 py-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </Card>
  );
}

export default function FriaPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const systemFilter = searchParams.get('ai_system_id') || '';
  const [frias, setFrias] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    api.listFrias()
      .then(setFrias)
      .catch(err => {
        if (err instanceof ApiError && err.status === 403) {
          setError("You do not have entitlement for FRIA management. Please upgrade your plan.");
        } else {
          setError("Failed to load FRIA records.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleCreated = (fria: any) => {
    setShowCreate(false);
    router.push(`/fria/${fria.id}`);
  };

  if (loading) {
    return (
      <PageShell title="Fundamental Rights Impact Assessments" subtitle="Manage and review mandated FRIAs for high-risk AI systems.">
        <Loading />
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell title="Fundamental Rights Impact Assessments" subtitle="Manage and review mandated FRIAs for high-risk AI systems.">
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-3 rounded-full bg-red-500/10 mb-4">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Access Restricted</h3>
            <p className="text-zinc-400 max-w-md">{error}</p>
            <Link href="/billing" className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors">
              View Plans
            </Link>
          </div>
        </Card>
      </PageShell>
    );
  }

  const visibleFrias = systemFilter ? frias.filter(f => f.ai_system_id === systemFilter) : frias;

  return (
    <PageShell
      title="Fundamental Rights Impact Assessments"
      subtitle="Guided FRIA builder — complete all 6 sections and submit for approval."
      actions={
        <button
          onClick={() => setShowCreate(v => !v)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/20"
        >
          <Plus className="h-4 w-4" />
          New FRIA
        </button>
      }
    >
      <div className="space-y-4">
        {showCreate && (
          <CreateFriaPanel onCreated={handleCreated} onClose={() => setShowCreate(false)} />
        )}

        {/* Stats row */}
        {visibleFrias.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(['draft', 'in_review', 'approved', 'rejected'] as const).map(s => {
              const count = visibleFrias.filter(f => f.status === s).length;
              const colors: Record<string, string> = {
                draft: 'text-zinc-400', in_review: 'text-amber-400',
                approved: 'text-emerald-400', rejected: 'text-red-400',
              };
              return (
                <div key={s} className="p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/60 text-center">
                  <p className={`text-lg font-bold ${colors[s]}`}>{count}</p>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-600 mt-0.5">{s.replace('_', ' ')}</p>
                </div>
              );
            })}
          </div>
        )}

        {visibleFrias.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="p-4 rounded-full bg-zinc-900 mb-6">
                <ClipboardList className="h-8 w-8 text-zinc-600" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">No FRIAs yet</h3>
              <p className="text-zinc-500 max-w-sm mx-auto leading-relaxed">
                Fundamental Rights Impact Assessments are required for high-risk AI systems under Article 27 of the EU AI Act.
              </p>
              <button
                onClick={() => setShowCreate(true)}
                className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors"
              >
                Start First FRIA
              </button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {visibleFrias.map(fria => (
              <Link key={fria.id} href={`/fria/${fria.id}`}>
                <Card className="hover:border-zinc-700 transition-all group">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 min-w-0 flex-1">
                      <div className="p-2.5 rounded-lg bg-zinc-900 text-zinc-400 group-hover:text-indigo-400 transition-colors border border-zinc-800 shrink-0">
                        {fria.status === 'approved' ? (
                          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                        ) : (
                          <ShieldCheck className="h-5 w-5" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-bold text-white tracking-tight text-sm">{fria.id}</h4>
                          <StatusBadge value={fria.status} />
                        </div>
                        <p className="text-xs text-zinc-500 mt-0.5 font-medium truncate">System: {fria.ai_system_id}</p>
                        <CompletionBar percent={fria.completion_percent ?? 0} />
                      </div>
                    </div>
                    <div className="flex items-center gap-6 shrink-0 ml-4">
                      <div className="text-right hidden sm:block">
                        <p className="text-[10px] uppercase tracking-wider font-bold text-zinc-600">Updated</p>
                        <p className="text-xs text-zinc-400 font-medium">{new Date(fria.updated_at).toLocaleDateString()}</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-zinc-700 group-hover:text-zinc-400 transition-colors" />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
