'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import EmptyState from '@/components/empty-state';
import ErrorState from '@/components/error-state';
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  FileSearch,
  ListChecks,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
} from 'lucide-react';

const STATUS_OPTIONS = ['not_started', 'in_progress', 'blocked', 'completed', 'signed_off'];

export default function ControlsPage() {
  const searchParams = useSearchParams();
  const highlightedControlId = searchParams.get('control_id') || '';
  const [systems, setSystems] = useState<any[]>([]);
  const [selectedSystemId, setSelectedSystemId] = useState(searchParams.get('ai_system_id') || '');
  const [controls, setControls] = useState<any[]>([]);
  const [evidenceItems, setEvidenceItems] = useState<any[]>([]);
  const [scorecard, setScorecard] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, { owner_email: string; status: string }>>({});
  const [attachmentDrafts, setAttachmentDrafts] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const evidenceParams = selectedSystemId ? { ai_system_id: selectedSystemId } : undefined;
      const [systemData, controlData, scoreData, evidenceData] = await Promise.all([
        api.listSystems().catch(() => []),
        api.listControls(selectedSystemId || undefined),
        api.getScorecard(selectedSystemId || undefined),
        api.listEvidenceItems(evidenceParams),
      ]);
      setSystems(systemData || []);
      setControls(controlData || []);
      setScorecard(scoreData);
      setEvidenceItems(evidenceData || []);
      setDrafts(Object.fromEntries((controlData || []).map((control: any) => [
        control.id,
        {
          owner_email: control.owner_email || '',
          status: control.status || 'not_started',
        },
      ])));
      setAttachmentDrafts(Object.fromEntries((controlData || []).map((control: any) => [control.id, ''])));
    } catch (err: any) {
      setError(err.body?.error?.message || err.body?.detail || err.message || 'Failed to load controls');
    } finally {
      setLoading(false);
    }
  }, [selectedSystemId]);

  useEffect(() => {
    load();
  }, [load]);

  const overdueCount = scorecard?.overdue_controls || 0;
  const readyCount = scorecard?.completed_controls || 0;
  const totalCount = scorecard?.total_controls || controls.length;
  const readinessScore = scorecard?.readiness_score || 0;
  const evidenceLinkCount = controls.reduce((sum, control) => sum + (control.evidence_item_count || 0), 0);

  const selectedSystemName = useMemo(() => {
    if (!selectedSystemId) return 'Tenant-wide controls';
    return systems.find((system) => system.id === selectedSystemId)?.name || selectedSystemId;
  }, [selectedSystemId, systems]);

  async function seedBaseline() {
    setSavingId('seed');
    setError(null);
    try {
      await api.seedBaselineControls(selectedSystemId || undefined);
      await load();
    } catch (err: any) {
      setError(err.body?.error?.message || err.body?.detail || err.message || 'Failed to seed baseline controls');
    } finally {
      setSavingId(null);
    }
  }

  async function saveControl(control: any) {
    const draft = drafts[control.id];
    if (!draft) return;
    setSavingId(control.id);
    setError(null);
    try {
      await api.updateControl(control.id, {
        owner_email: draft.owner_email || null,
        status: draft.status,
      });
      await load();
    } catch (err: any) {
      setError(err.body?.error?.message || err.body?.detail || err.message || 'Failed to update control');
    } finally {
      setSavingId(null);
    }
  }

  function updateDraft(id: string, patch: Partial<{ owner_email: string; status: string }>) {
    setDrafts((current) => ({
      ...current,
      [id]: {
        owner_email: current[id]?.owner_email || '',
        status: current[id]?.status || 'not_started',
        ...patch,
      },
    }));
  }

  function createEvidenceHref(control: any) {
    const params = new URLSearchParams({
      create: '1',
      control_id: control.id,
      evidence_type: control.evidence_domain || 'policy',
      source: 'Control register',
    });
    const systemId = control.ai_system_id || selectedSystemId;
    if (systemId) {
      params.set('ai_system_id', systemId);
    }
    return `/evidence?${params.toString()}`;
  }

  function eligibleEvidenceForControl(control: any) {
    return evidenceItems.filter((item) => {
      if (item.control_id && item.control_id !== control.id) return false;
      if (control.ai_system_id && item.ai_system_id && item.ai_system_id !== control.ai_system_id) return false;
      return true;
    });
  }

  async function attachEvidence(control: any) {
    const itemId = attachmentDrafts[control.id];
    if (!itemId) return;
    setSavingId(`attach-${control.id}`);
    setError(null);
    try {
      await api.attachEvidenceToControl(control.id, itemId);
      await load();
    } catch (err: any) {
      setError(err.body?.error?.message || err.body?.detail || err.message || 'Failed to attach evidence to control');
    } finally {
      setSavingId(null);
    }
  }

  if (loading) {
    return (
      <PageShell title="Compliance Controls" subtitle="Control ownership, readiness, and evidence requirements across EU AI Act obligations.">
        <Loading />
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Compliance Controls"
      subtitle="Control ownership, readiness, and evidence requirements across EU AI Act obligations."
      breadcrumbs={[{ label: 'Controls' }]}
      actions={
        <button
          onClick={seedBaseline}
          disabled={savingId === 'seed'}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-[11px] font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all shadow-lg shadow-indigo-600/20"
        >
          {savingId === 'seed' ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
          Seed Baseline
        </button>
      }
    >
      <div className="space-y-6">
        {error && <ErrorState message={error} onRetry={load} />}

        <div className="grid grid-cols-1 lg:grid-cols-6 gap-4">
          <Card title="Readiness Score" variant="stat" className="lg:col-span-2">
            <div className="space-y-3">
              <div className="flex items-end gap-3">
                <span className={`text-4xl font-bold tabular-nums ${readinessScore >= 80 ? 'text-emerald-400' : readinessScore >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                  {readinessScore}%
                </span>
                <span className="text-xs text-zinc-500 mb-1">{selectedSystemName}</span>
              </div>
              <div className="h-2 w-full rounded-full bg-zinc-900 overflow-hidden">
                <div
                  className={`h-full ${readinessScore >= 80 ? 'bg-emerald-500' : readinessScore >= 40 ? 'bg-amber-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(100, Math.max(0, readinessScore))}%` }}
                />
              </div>
            </div>
          </Card>

          <Card title="Controls" variant="stat">
            <div className="flex items-end gap-2">
              <ListChecks className="h-5 w-5 text-indigo-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums">{totalCount}</span>
            </div>
          </Card>

          <Card title="Evidence Links" variant="stat">
            <div className="flex items-end gap-2">
              <FileSearch className="h-5 w-5 text-sky-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums text-sky-300">{evidenceLinkCount}</span>
            </div>
          </Card>

          <Card title="Completed" variant="stat">
            <div className="flex items-end gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums text-emerald-400">{readyCount}</span>
            </div>
          </Card>

          <Card title="Overdue" variant="stat">
            <div className="flex items-end gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums text-red-400">{overdueCount}</span>
            </div>
          </Card>
        </div>

        <Card className="bg-zinc-950 px-6 py-4">
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-bold text-zinc-500 uppercase tracking-widest md:border-r border-border md:pr-5">
              <BarChart3 className="h-3.5 w-3.5 text-zinc-600" />
              Scope
            </div>
            <select
              value={selectedSystemId}
              onChange={(event) => setSelectedSystemId(event.target.value)}
              className="min-w-[260px] bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            >
              <option value="">Tenant-wide controls</option>
              {systems.map((system) => (
                <option key={system.id} value={system.id}>{system.name}</option>
              ))}
            </select>
            <p className="text-xs text-zinc-500">
              Seed tenant-wide controls for organization-level duties, or select a system for system-specific ownership.
            </p>
          </div>
        </Card>

        {controls.length === 0 ? (
          <EmptyState
            title="No controls in this scope"
            message="Seed the EU AI Act baseline to create the first operational control set."
            icon={ShieldCheck}
            action={
              <button
                onClick={seedBaseline}
                disabled={savingId === 'seed'}
                className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-white text-[11px] font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all"
              >
                <Plus className="h-3.5 w-3.5" />
                Seed Controls
              </button>
            }
          />
        ) : (
          <Card className="!p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Control</th>
                    <th>Article</th>
                    <th>Evidence Domain</th>
                    <th>Evidence</th>
                    <th>Owner</th>
                    <th>Status</th>
                    <th>Due</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {controls.map((control) => {
                    const draft = drafts[control.id] || { owner_email: control.owner_email || '', status: control.status };
                    const eligibleEvidence = eligibleEvidenceForControl(control);
                    const attachmentKey = `attach-${control.id}`;
                    return (
                      <tr key={control.id} className={highlightedControlId === control.id ? 'bg-indigo-950/20' : undefined}>
                        <td className="min-w-[280px]">
                          <div className="space-y-1">
                            <p className="text-sm font-bold text-zinc-200">{control.title}</p>
                            <p className="text-[10px] font-mono text-zinc-600">{control.control_key}</p>
                          </div>
                        </td>
                        <td>
                          <span className="text-[10px] font-bold text-indigo-300 uppercase tracking-wider bg-indigo-500/10 border border-indigo-500/20 rounded px-2 py-1">
                            {control.article}
                          </span>
                        </td>
                        <td className="text-[10px] font-mono text-zinc-500">{control.evidence_domain}</td>
                        <td className="min-w-[280px]">
                          <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2 text-[10px] text-zinc-500">
                              <span className="inline-flex items-center gap-1 font-bold uppercase tracking-widest text-sky-300">
                                <FileSearch className="h-3 w-3" />
                                {control.evidence_item_count || 0} linked
                              </span>
                              {(control.needs_review_evidence_count || 0) > 0 && (
                                <span className="rounded bg-amber-500/10 px-2 py-0.5 font-bold text-amber-300">
                                  {control.needs_review_evidence_count} review
                                </span>
                              )}
                              {control.latest_evidence_at && (
                                <span>Latest {new Date(control.latest_evidence_at).toLocaleDateString()}</span>
                              )}
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <Link
                                href={createEvidenceHref(control)}
                                className="rounded-md bg-zinc-900 px-2 py-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800"
                              >
                                New Evidence
                              </Link>
                              <select
                                aria-label={`Attach evidence to ${control.title}`}
                                value={attachmentDrafts[control.id] || ''}
                                onChange={(event) => setAttachmentDrafts((current) => ({ ...current, [control.id]: event.target.value }))}
                                className="max-w-[150px] bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                              >
                                <option value="">Attach existing</option>
                                {eligibleEvidence.map((item) => (
                                  <option key={item.id} value={item.id}>{item.title}</option>
                                ))}
                              </select>
                              <button
                                onClick={() => attachEvidence(control)}
                                disabled={!attachmentDrafts[control.id] || savingId === attachmentKey}
                                className="rounded-md bg-zinc-800 px-2 py-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-200 hover:bg-zinc-700 disabled:opacity-50"
                              >
                                {savingId === attachmentKey ? 'Linking' : 'Attach'}
                              </button>
                            </div>
                          </div>
                        </td>
                        <td>
                          <input
                            value={draft.owner_email}
                            onChange={(event) => updateDraft(control.id, { owner_email: event.target.value })}
                            placeholder="owner@company.com"
                            className="w-[190px] bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-xs text-zinc-200 placeholder:text-zinc-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                          />
                        </td>
                        <td>
                          <select
                            aria-label={`Control status for ${control.title}`}
                            value={draft.status}
                            onChange={(event) => updateDraft(control.id, { status: event.target.value })}
                            className="bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                          >
                            {STATUS_OPTIONS.map((status) => (
                              <option key={status} value={status}>{status.replace(/_/g, ' ')}</option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <div className="flex items-center gap-1 text-[10px] text-zinc-500 whitespace-nowrap">
                            <Clock className="h-3 w-3 text-zinc-600" />
                            {control.due_at ? new Date(control.due_at).toLocaleDateString() : 'No due date'}
                          </div>
                        </td>
                        <td className="text-right">
                          <button
                            onClick={() => saveControl(control)}
                            disabled={savingId === control.id}
                            className="inline-flex items-center gap-1.5 rounded-md bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-200"
                          >
                            {savingId === control.id ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                            Save
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {controls.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(scorecard?.controls_by_status || {}).map(([status, count]) => (
              <Card key={status} title={status.replace(/_/g, ' ')} variant="stat">
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold tabular-nums">{count as number}</span>
                  <StatusBadge value={status} />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
