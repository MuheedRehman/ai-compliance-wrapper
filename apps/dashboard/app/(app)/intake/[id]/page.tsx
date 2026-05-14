'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import ErrorState from '@/components/error-state';
import { 
  ArrowLeft, 
  ShieldCheck, 
  AlertTriangle, 
  BookOpen, 
  Scale,
  Gavel,
  ListChecks,
  RefreshCw
} from 'lucide-react';

export default function IntakeDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [intake, setIntake] = useState<any>(null);
  const [obligationExplanation, setObligationExplanation] = useState<any>(null);
  const [systems, setSystems] = useState<any[]>([]);
  const [selectedSystemId, setSelectedSystemId] = useState('');
  const [createdControls, setCreatedControls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [materializing, setMaterializing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    try {
      const [data, systemData] = await Promise.all([
        api.getIntake(id),
        api.listSystems().catch(() => []),
      ]);
      setIntake(data);
      setSystems(systemData || []);
      api.explainIntakeObligations(id)
        .then(setObligationExplanation)
        .catch(() => setObligationExplanation(null));
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to load intake record');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  if (loading) return <PageShell title="Loading assessment..."><Loading /></PageShell>;
  if (error) return <PageShell title="Error"><ErrorState message={error} onRetry={loadDetail} /></PageShell>;

  async function createControlPlan() {
    setMaterializing(true);
    setError(null);
    try {
      const controls = await api.materializeIntakeControlPlan(id, selectedSystemId || undefined);
      setCreatedControls(controls);
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to create control plan');
    } finally {
      setMaterializing(false);
    }
  }

  return (
    <PageShell
      title={intake.title}
      subtitle={`Classification Result · Generated ${new Date(intake.created_at).toLocaleDateString()}`}
      breadcrumbs={[
        { label: 'Intake', href: '/intake' },
        { label: intake.id }
      ]}
      actions={
        <Link 
          href="/intake"
          className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-zinc-500 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to List
        </Link>
      }
    >
      <div className="space-y-8 animate-fade-in">
        {/* Classification Summary Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card title="Actor Role" variant="stat">
            <div className="flex items-center gap-2 mt-1">
              <StatusBadge value={intake.actor_role} />
            </div>
          </Card>
          <Card title="System Risk" variant="stat">
            <div className="mt-1">
              <span className={`text-sm font-bold px-2 py-0.5 rounded border ${
                intake.system_classification.includes('High') ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' :
                intake.system_classification.includes('Prohibited') ? 'bg-red-500/10 border-red-500/30 text-red-500' :
                'bg-zinc-800 border-zinc-700 text-zinc-300'
              }`}>
                {intake.system_classification}
              </span>
            </div>
          </Card>
          <Card title="Obligation Path" variant="stat">
            <div className="flex items-center gap-2 mt-1">
              <Scale className="h-4 w-4 text-indigo-400" />
              <span className="text-sm font-bold text-zinc-200 font-mono">{intake.obligation_path}</span>
            </div>
          </Card>
          <Card title="Assessment Status" variant="stat">
            <div className="flex items-center gap-2 mt-1">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Persisted</span>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Classification Result */}
          <div className="lg:col-span-2 space-y-6">
            <Card title="Classification Rationale" subtitle="The legal logic behind this system's categorization.">
              <div className="space-y-4">
                <div className="flex gap-4 p-4 rounded-xl bg-secondary/30 border border-border">
                  <div className="p-2 rounded-lg bg-indigo-500/10 shrink-0 h-fit">
                    <Gavel className="h-5 w-5 text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-sm text-zinc-300 leading-relaxed font-medium">
                      {intake.rationale}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-[11px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                    <BookOpen className="h-3 w-3" /> Targeted Regulatory Guidance
                  </h4>
                  <div className="p-4 rounded-xl border border-border space-y-3">
                    <p className="text-xs text-zinc-400 leading-relaxed">
                      Based on the determined path <code className="text-indigo-400 font-bold">{intake.obligation_path}</code>, 
                      this system must adhere to specific documentation, transparency, and risk management requirements 
                      stipulated in the EU AI Act.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
                      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
                        <span className="text-[10px] font-bold text-zinc-600 uppercase block mb-1">Key Obligation</span>
                        <span className="text-xs text-zinc-300 font-medium">Conformity Assessment</span>
                      </div>
                      <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
                        <span className="text-[10px] font-bold text-zinc-600 uppercase block mb-1">Reporting Cycle</span>
                        <span className="text-xs text-zinc-300 font-medium">Annual Audit Required</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {obligationExplanation && (
              <Card title="Applicable EU AI Act Dimensions" subtitle="Structured obligation engine output for this intake.">
                <div className="space-y-3">
                  {(obligationExplanation.applicable_dimensions || []).map((dimension: any) => (
                    <div key={dimension.dimension_id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-xs font-bold text-zinc-200">{dimension.pillar}</p>
                          <p className="mt-1 text-[10px] font-mono text-indigo-300">{dimension.article}</p>
                        </div>
                        <StatusBadge value={dimension.status} />
                      </div>
                      <p className="mt-3 text-xs leading-relaxed text-zinc-400">{dimension.explanation}</p>
                      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Controls</p>
                          <p className="mt-1 text-xs text-zinc-300">{(dimension.required_controls || []).map((control: any) => control.title).join(', ') || 'Manual review'}</p>
                        </div>
                        <div className="rounded border border-zinc-800 bg-zinc-900/40 p-3">
                          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Evidence</p>
                          <p className="mt-1 text-xs text-zinc-300">{(dimension.required_evidence || []).map((item: any) => item.type).join(', ') || dimension.evidence_domain}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            <Card title="Obligation Control Plan" subtitle="Generate controls directly from this intake's obligation graph.">
              <div className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {(intake.obligation_graph_json || []).map((item: any) => (
                    <div key={item.key} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-300">{item.article}</span>
                        <StatusBadge value={item.status} />
                      </div>
                      <p className="mt-2 text-xs font-medium leading-relaxed text-zinc-300">{item.summary}</p>
                      <p className="mt-2 text-[10px] font-mono text-zinc-600">{item.evidence_domain}</p>
                    </div>
                  ))}
                </div>

                <div className="flex flex-col gap-3 rounded-lg border border-zinc-800 bg-zinc-950 p-4 md:flex-row md:items-end">
                  <div className="flex-1">
                    <label className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                      Scope control plan
                    </label>
                    <select
                      value={selectedSystemId}
                      onChange={(event) => setSelectedSystemId(event.target.value)}
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 outline-none focus:ring-2 focus:ring-indigo-500/30"
                    >
                      <option value="">Tenant-wide controls</option>
                      {systems.map((system) => (
                        <option key={system.id} value={system.id}>{system.name}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={createControlPlan}
                    disabled={materializing}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-[11px] font-bold uppercase tracking-widest text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 disabled:opacity-50"
                  >
                    {materializing ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ListChecks className="h-3.5 w-3.5" />}
                    Create Control Plan
                  </button>
                </div>

                {createdControls.length > 0 && (
                  <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-bold text-emerald-300">
                        {createdControls.length} controls are ready for ownership and tracking.
                      </p>
                      <Link
                        href={`/controls${selectedSystemId ? `?ai_system_id=${selectedSystemId}` : ''}`}
                        className="text-[10px] font-bold uppercase tracking-widest text-emerald-300 hover:text-emerald-200"
                      >
                        Open Controls
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </Card>

            <Card title="Intake Audit Trail" subtitle="Original inputs provided during assessment.">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.entries(intake.answers_json).map(([key, value]) => (
                  <div key={key} className="p-3 rounded-lg border border-border bg-zinc-950/40 flex justify-between items-center">
                    <span className="text-[11px] text-zinc-500 font-medium">{key.replace(/_/g, ' ')}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${value ? 'bg-emerald-500/10 text-emerald-500' : 'bg-zinc-800 text-zinc-600'}`}>
                      {value ? 'YES' : 'NO'}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Sidebar Actions/Context */}
          <div className="space-y-6">
            <Card title="Next Steps">
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="h-6 w-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-400 shrink-0">1</div>
                  <p className="text-xs text-zinc-400 leading-relaxed">Link this intake to an AI System in the Registry.</p>
                </div>
                <div className="flex gap-3">
                  <div className="h-6 w-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-400 shrink-0">2</div>
                  <p className="text-xs text-zinc-400 leading-relaxed">Create an obligation control plan from this classification.</p>
                </div>
                <div className="flex gap-3 opacity-40">
                  <div className="h-6 w-6 rounded-full bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-zinc-400 shrink-0">3</div>
                  <p className="text-xs text-zinc-400 leading-relaxed italic">Initialize FRIA workflow if high-risk deployer obligations apply.</p>
                </div>
              </div>
            </Card>

            <Card title="Metadata">
              <div className="space-y-3">
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-zinc-500">Intake ID</span>
                  <span className="font-mono text-zinc-300">{intake.id}</span>
                </div>
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-zinc-500">Compliance Version</span>
                  <span className="text-zinc-300">EU AI Act v1.0 (Stable)</span>
                </div>
                <div className="flex justify-between items-center text-[11px]">
                  <span className="text-zinc-500">Methodology</span>
                  <span className="text-zinc-300">Deterministic Branching</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
