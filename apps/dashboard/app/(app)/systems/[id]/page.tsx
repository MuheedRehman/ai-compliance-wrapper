'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  Bot,
  CalendarClock,
  ClipboardCheck,
  FileSearch,
  FileText,
  ListChecks,
  Scale,
  Save,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { api } from '@/lib/api';
import Card from '@/components/card';
import ErrorState from '@/components/error-state';
import Loading from '@/components/loading';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';

function EmptyPanel({ label }: { label: string }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-800 bg-zinc-950/40 px-4 py-8 text-center text-xs font-bold uppercase tracking-widest text-zinc-600">
      {label}
    </div>
  );
}

function metricColor(value: number) {
  if (value >= 80) return 'text-emerald-400';
  if (value >= 40) return 'text-amber-400';
  return 'text-red-400';
}

function toDateInput(value?: string | null) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 10);
}

function fromDateInput(value: string) {
  return value ? new Date(`${value}T12:00:00.000Z`).toISOString() : null;
}

function displayDate(value?: string | null) {
  if (!value) return 'Not scheduled';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Not scheduled';
  return date.toLocaleDateString(undefined, { dateStyle: 'medium' });
}

export default function SystemDetailPage() {
  const params = useParams();
  const systemId = params.id as string;

  const [workspace, setWorkspace] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [recordingReview, setRecordingReview] = useState(false);
  const [profileForm, setProfileForm] = useState({
    owner_email: '',
    technical_owner_email: '',
    legal_owner_email: '',
    review_status: 'not_started',
    next_review_at: '',
    lifecycle_notes: '',
  });
  const [reviewForm, setReviewForm] = useState({
    reviewer_email: '',
    review_type: 'lifecycle_review',
    status: 'completed',
    next_review_at: '',
    notes: '',
  });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api.getSystemWorkspace(systemId)
      .then(setWorkspace)
      .catch((err) => setError(err.body?.detail || err.body?.error?.message || err.message || 'Failed to load AI system workspace'))
      .finally(() => setLoading(false));
  }, [systemId]);

  useEffect(() => { load(); }, [load]);

  const system = workspace?.system;
  const metrics = workspace?.metrics || {};
  const governance = workspace?.governance_summary || {};
  const scorecard = workspace?.readiness_scorecard || {};
  const classification = workspace?.latest_classification;
  const reviewEvents = workspace?.review_events || [];
  const readinessScore = scorecard.readiness_score || 0;

  useEffect(() => {
    if (!system) return;
    setProfileForm({
      owner_email: system.owner_email || '',
      technical_owner_email: system.technical_owner_email || '',
      legal_owner_email: system.legal_owner_email || '',
      review_status: system.review_status || 'not_started',
      next_review_at: toDateInput(system.next_review_at),
      lifecycle_notes: system.lifecycle_notes || '',
    });
  }, [system]);

  const openControls = useMemo(
    () => (workspace?.controls || []).filter((control: any) => !['completed', 'signed_off'].includes(control.status)),
    [workspace],
  );

  async function handleProfileSave(event: React.FormEvent) {
    event.preventDefault();
    if (!system) return;
    setSavingProfile(true);
    setError(null);
    try {
      await api.updateSystem(system.id, {
        owner_email: profileForm.owner_email.trim() || null,
        technical_owner_email: profileForm.technical_owner_email.trim() || null,
        legal_owner_email: profileForm.legal_owner_email.trim() || null,
        review_status: profileForm.review_status,
        next_review_at: fromDateInput(profileForm.next_review_at),
        lifecycle_notes: profileForm.lifecycle_notes.trim() || null,
      });
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to update lifecycle profile');
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleReviewSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!system) return;
    setRecordingReview(true);
    setError(null);
    try {
      await api.createSystemReview(system.id, {
        reviewer_email: reviewForm.reviewer_email.trim() || null,
        review_type: reviewForm.review_type,
        status: reviewForm.status,
        next_review_at: fromDateInput(reviewForm.next_review_at),
        notes: reviewForm.notes.trim() || null,
      });
      setReviewForm({
        reviewer_email: '',
        review_type: 'lifecycle_review',
        status: 'completed',
        next_review_at: '',
        notes: '',
      });
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to record review');
    } finally {
      setRecordingReview(false);
    }
  }

  if (loading) {
    return (
      <PageShell title="AI System Workspace" subtitle="Loading lifecycle record.">
        <Loading />
      </PageShell>
    );
  }

  if (error || !workspace || !system) {
    return (
      <PageShell title="AI System Workspace" subtitle="Lifecycle record unavailable.">
        <ErrorState message={error || 'AI system not found'} onRetry={load} />
      </PageShell>
    );
  }

  return (
    <PageShell
      title={system.name}
      subtitle={system.description || `System ID: ${system.id}`}
      breadcrumbs={[{ label: 'AI Systems', href: '/systems' }, { label: system.name }]}
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/systems" className="flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800">
            <ArrowLeft className="h-4 w-4" />
            BACK
          </Link>
          <Link href={`/controls?ai_system_id=${system.id}`} className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500">
            <ListChecks className="h-4 w-4" />
            CONTROLS
          </Link>
          <Link href={`/evidence?ai_system_id=${system.id}`} className="flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800">
            <FileSearch className="h-4 w-4" />
            EVIDENCE
          </Link>
        </div>
      }
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card title="Readiness" variant="stat">
            <div className="space-y-2">
              <span className={`text-4xl font-bold tabular-nums ${metricColor(readinessScore)}`}>{readinessScore}%</span>
              <div className="h-2 rounded-full bg-zinc-900 overflow-hidden">
                <div className="h-full bg-indigo-500" style={{ width: `${Math.min(100, Math.max(0, readinessScore))}%` }} />
              </div>
            </div>
          </Card>
          <Card title="Open Controls" variant="stat">
            <div className="flex items-end gap-2">
              <ListChecks className="h-5 w-5 text-amber-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums">{metrics.open_control_count || 0}</span>
            </div>
          </Card>
          <Card title="Evidence Vault" variant="stat">
            <div className="flex items-end gap-2">
              <FileSearch className="h-5 w-5 text-indigo-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums">{metrics.evidence_item_count || 0}</span>
            </div>
          </Card>
          <Card title="Open Incidents" variant="stat">
            <div className="flex items-end gap-2">
              <AlertTriangle className="h-5 w-5 text-red-400 mb-1" />
              <span className="text-3xl font-bold tabular-nums">{metrics.open_incident_count || 0}</span>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <Card title="Lifecycle Ownership" className="xl:col-span-2">
            <form onSubmit={handleProfileSave} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Business owner</span>
                  <input
                    type="email"
                    value={profileForm.owner_email}
                    onChange={(event) => setProfileForm({ ...profileForm, owner_email: event.target.value })}
                    placeholder="owner@example.com"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Technical owner</span>
                  <input
                    type="email"
                    value={profileForm.technical_owner_email}
                    onChange={(event) => setProfileForm({ ...profileForm, technical_owner_email: event.target.value })}
                    placeholder="tech@example.com"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Legal owner</span>
                  <input
                    type="email"
                    value={profileForm.legal_owner_email}
                    onChange={(event) => setProfileForm({ ...profileForm, legal_owner_email: event.target.value })}
                    placeholder="legal@example.com"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-[180px_180px_1fr] gap-3">
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Review status</span>
                  <select
                    value={profileForm.review_status}
                    onChange={(event) => setProfileForm({ ...profileForm, review_status: event.target.value })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  >
                    <option value="not_started">Not started</option>
                    <option value="scheduled">Scheduled</option>
                    <option value="in_review">In review</option>
                    <option value="completed">Completed</option>
                    <option value="overdue">Overdue</option>
                  </select>
                </label>
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Next review</span>
                  <input
                    type="date"
                    value={profileForm.next_review_at}
                    onChange={(event) => setProfileForm({ ...profileForm, next_review_at: event.target.value })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Lifecycle notes</span>
                  <input
                    value={profileForm.lifecycle_notes}
                    onChange={(event) => setProfileForm({ ...profileForm, lifecycle_notes: event.target.value })}
                    placeholder="Release, scope, or review notes"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-2">
                  <StatusBadge value={governance.review_deadline_status || 'unscheduled'} />
                  <span className="rounded-lg bg-zinc-950 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-zinc-500 ring-1 ring-zinc-800">
                    {metrics.assigned_owner_count || 0}/3 owners
                  </span>
                </div>
                <button
                  disabled={savingProfile}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  <Save className="h-4 w-4" />
                  {savingProfile ? 'SAVING...' : 'SAVE PROFILE'}
                </button>
              </div>
            </form>
          </Card>

          <Card title="Review Checkpoint">
            <form onSubmit={handleReviewSubmit} className="space-y-3">
              <div className="grid grid-cols-1 gap-3">
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Reviewer</span>
                  <input
                    type="email"
                    value={reviewForm.reviewer_email}
                    onChange={(event) => setReviewForm({ ...reviewForm, reviewer_email: event.target.value })}
                    placeholder="reviewer@example.com"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Type</span>
                    <select
                      value={reviewForm.review_type}
                      onChange={(event) => setReviewForm({ ...reviewForm, review_type: event.target.value })}
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                    >
                      <option value="lifecycle_review">Lifecycle</option>
                      <option value="classification_review">Classification</option>
                      <option value="control_review">Controls</option>
                      <option value="evidence_review">Evidence</option>
                      <option value="incident_review">Incidents</option>
                    </select>
                  </label>
                  <label className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Outcome</span>
                    <select
                      value={reviewForm.status}
                      onChange={(event) => setReviewForm({ ...reviewForm, status: event.target.value })}
                      className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                    >
                      <option value="completed">Completed</option>
                      <option value="needs_follow_up">Follow up</option>
                      <option value="scheduled">Scheduled</option>
                      <option value="in_review">In review</option>
                    </select>
                  </label>
                </div>
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Next review</span>
                  <input
                    type="date"
                    value={reviewForm.next_review_at}
                    onChange={(event) => setReviewForm({ ...reviewForm, next_review_at: event.target.value })}
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
                <label className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Notes</span>
                  <textarea
                    value={reviewForm.notes}
                    onChange={(event) => setReviewForm({ ...reviewForm, notes: event.target.value })}
                    rows={3}
                    placeholder="Review outcome"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                  />
                </label>
              </div>
              <button
                disabled={recordingReview}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-100 px-4 py-2 text-xs font-bold text-zinc-950 hover:bg-white disabled:opacity-50"
              >
                <ClipboardCheck className="h-4 w-4" />
                {recordingReview ? 'RECORDING...' : 'RECORD REVIEW'}
              </button>
            </form>
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <Card title="Lifecycle Snapshot" className="xl:col-span-1">
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Deployment</span>
                <StatusBadge value={system.deployment_status} />
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Registration</span>
                <StatusBadge value={system.registration_status} />
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Features</span>
                <span className="text-xs font-mono text-zinc-300">{metrics.feature_count || 0}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Website scans</span>
                <span className="text-xs font-mono text-zinc-300">{metrics.website_scan_count || 0}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Reports</span>
                <span className="text-xs font-mono text-zinc-300">{metrics.report_count || 0}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Next review</span>
                <span className="text-xs font-mono text-zinc-300">{displayDate(system.next_review_at)}</span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs text-zinc-500">Last reviewed</span>
                <span className="text-xs font-mono text-zinc-300">{displayDate(system.last_reviewed_at)}</span>
              </div>
            </div>
          </Card>

          <Card title="Current Classification" className="xl:col-span-2">
            {classification ? (
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Scale className="h-5 w-5 text-indigo-400 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-bold text-white">{classification.system_classification}</h3>
                    <p className="text-xs text-zinc-500 mt-1">{classification.rationale}</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Actor</p>
                    <p className="mt-1 text-xs font-bold text-zinc-200">{classification.actor_role}</p>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Path</p>
                    <p className="mt-1 text-xs font-bold text-zinc-200">{classification.obligation_path}</p>
                  </div>
                  <Link href={`/intake/${classification.intake_id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-indigo-500/40">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Intake</p>
                    <p className="mt-1 text-xs font-mono text-indigo-300">{classification.intake_id}</p>
                  </Link>
                </div>
              </div>
            ) : (
              <EmptyPanel label="No classification linked yet" />
            )}
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card title={`Controls (${workspace.controls.length})`} subtitle="System-specific EU AI Act control plan.">
            {workspace.controls.length === 0 ? (
              <EmptyPanel label="No controls materialized" />
            ) : (
              <div className="space-y-3">
                {workspace.controls.slice(0, 6).map((control: any) => (
                  <Link key={control.id} href={`/controls?ai_system_id=${system.id}`} className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{control.title}</p>
                        <p className="mt-1 text-[10px] font-mono text-zinc-600">{control.article} / {control.evidence_domain}</p>
                      </div>
                      <StatusBadge value={control.status} />
                    </div>
                  </Link>
                ))}
                {openControls.length > 6 && (
                  <Link href={`/controls?ai_system_id=${system.id}`} className="text-xs font-bold text-indigo-400 hover:text-indigo-300">
                    View all open controls
                  </Link>
                )}
              </div>
            )}
          </Card>

          <Card title={`Evidence Vault (${workspace.evidence_items?.length || 0})`} subtitle="Signed audit artifacts and recent traceability events.">
            {(workspace.evidence_items?.length || 0) === 0 && workspace.evidence_logs.length === 0 ? (
              <EmptyPanel label="No evidence items yet" />
            ) : (
              <div className="space-y-3">
                {(workspace.evidence_items || []).slice(0, 4).map((item: any) => (
                  <Link key={item.id} href={`/evidence?ai_system_id=${system.id}`} className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{item.title}</p>
                        <p className="mt-1 text-[10px] font-mono text-zinc-600">{item.evidence_type} / {item.evidence_hash.slice(0, 12)}</p>
                      </div>
                      <StatusBadge value={item.status} />
                    </div>
                  </Link>
                ))}
                {workspace.evidence_logs.slice(0, 6).map((event: any) => (
                  <Link key={event.event_id} href={`/evidence?ai_system_id=${system.id}`} className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{event.event_type}</p>
                        <p className="mt-1 text-[10px] font-mono text-zinc-600">{event.evidence_domain || 'runtime'} / {event.event_id.slice(0, 12)}</p>
                      </div>
                      <StatusBadge value={event.risk_level || 'unknown'} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <Card title={`Scans (${workspace.website_scans.length})`}>
            {workspace.website_scans.length === 0 ? (
              <EmptyPanel label="No website scans" />
            ) : (
              <div className="space-y-3">
                {workspace.website_scans.slice(0, 4).map((scan: any) => (
                  <Link key={scan.id} href={`/scanner/${scan.id}`} className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                    <p className="text-xs font-bold text-zinc-200">{scan.title || scan.normalized_url}</p>
                    <p className="mt-1 text-[10px] text-zinc-600">{scan.classification_json?.classification || 'Unclassified'}</p>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          <Card title={`Reports (${workspace.reports.length})`}>
            {workspace.reports.length === 0 ? (
              <EmptyPanel label="No reports generated" />
            ) : (
              <div className="space-y-3">
                {workspace.reports.slice(0, 4).map((report: any) => (
                  <Link key={report.id} href={`/reports/${report.id}`} className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-emerald-400 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{report.title}</p>
                        <p className="mt-1 text-[10px] text-zinc-600">{report.report_type}</p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          <Card title="Governance Records">
            <div className="grid grid-cols-2 gap-3">
              <Link href={`/fria?ai_system_id=${system.id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                <ShieldCheck className="h-4 w-4 text-emerald-400 mb-2" />
                <p className="text-2xl font-bold">{metrics.fria_count || 0}</p>
                <p className="text-[10px] uppercase tracking-widest text-zinc-600">FRIA</p>
              </Link>
              <Link href={`/oversight?ai_system_id=${system.id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                <Users className="h-4 w-4 text-indigo-400 mb-2" />
                <p className="text-2xl font-bold">{metrics.oversight_count || 0}</p>
                <p className="text-[10px] uppercase tracking-widest text-zinc-600">Oversight</p>
              </Link>
              <Link href={`/incidents?ai_system_id=${system.id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                <Activity className="h-4 w-4 text-red-400 mb-2" />
                <p className="text-2xl font-bold">{metrics.incident_count || 0}</p>
                <p className="text-[10px] uppercase tracking-widest text-zinc-600">Incidents</p>
              </Link>
              <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                <BarChart3 className="h-4 w-4 text-amber-400 mb-2" />
                <p className="text-2xl font-bold">{metrics.high_severity_incident_count || 0}</p>
                <p className="text-[10px] uppercase tracking-widest text-zinc-600">Severe</p>
              </div>
            </div>
          </Card>
        </div>

        <Card title={`Review History (${reviewEvents.length})`} subtitle="Lifecycle decisions, review outcomes, and next checkpoints.">
          {reviewEvents.length === 0 ? (
            <EmptyPanel label="No lifecycle reviews recorded" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {reviewEvents.slice(0, 6).map((event: any) => (
                <div key={event.id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <CalendarClock className="mt-0.5 h-4 w-4 text-indigo-400" />
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{event.review_type?.replaceAll('_', ' ') || 'review'}</p>
                        <p className="mt-1 text-[10px] text-zinc-500">{event.reviewer_email || 'Unassigned reviewer'} / {displayDate(event.created_at)}</p>
                      </div>
                    </div>
                    <StatusBadge value={event.status} />
                  </div>
                  {event.notes && (
                    <p className="mt-3 text-xs leading-5 text-zinc-400">{event.notes}</p>
                  )}
                  {event.next_review_at && (
                    <p className="mt-3 text-[10px] font-bold uppercase tracking-widest text-zinc-600">
                      Next: {displayDate(event.next_review_at)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title={`Associated Features (${workspace.features.length})`} subtitle="Runtime-governed feature surfaces linked to this AI system.">
          {workspace.features.length === 0 ? (
            <EmptyPanel label="No linked runtime features" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {workspace.features.map((feature: any) => (
                <Link key={feature.id} href={`/features/${feature.feature_id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <Bot className="h-4 w-4 text-indigo-400 mt-0.5" />
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{feature.name}</p>
                        <p className="mt-1 text-[10px] font-mono text-zinc-600">{feature.feature_id}</p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <StatusBadge value={feature.compliance_status || 'draft'} />
                      <StatusBadge value={feature.risk_level_current || 'unknown'} />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>
    </PageShell>
  );
}
