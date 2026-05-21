'use client';

import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Bot,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  FilePlus2,
  FileSearch,
  FileText,
  Plus,
  RefreshCw,
  Trash2,
  ListChecks,
  Scale,
  Save,
  ShieldCheck,
  UserPlus,
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

function followUpHref(systemId: string, task: any) {
  const details = task.findings_json || {};
  const targetType = details.target_type;
  if (targetType === 'control') {
    const controlId = details.control_id || details.created_placeholder_id;
    return `/controls?${new URLSearchParams({ ai_system_id: systemId, ...(controlId ? { control_id: controlId } : {}) }).toString()}`;
  }
  if (targetType === 'evidence') {
    const evidenceId = details.evidence_item_id || details.created_placeholder_id;
    return `/evidence?${new URLSearchParams({ ai_system_id: systemId, ...(evidenceId ? { evidence_item_id: evidenceId } : {}) }).toString()}`;
  }
  return `/reviews?${new URLSearchParams({ ai_system_id: systemId }).toString()}`;
}

function WorkspaceAction({
  icon,
  label,
  value,
  href,
  onClick,
  busy,
  disabled,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  href?: string;
  onClick?: () => void;
  busy?: boolean;
  disabled?: boolean;
}) {
  const content = (
    <>
      <div className="flex items-center gap-3 min-w-0">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-900 text-indigo-300 ring-1 ring-zinc-800">
          {icon}
        </span>
        <span className="min-w-0">
          <span className="block text-xs font-bold text-zinc-100">{label}</span>
          <span className="mt-1 block text-[10px] font-mono uppercase tracking-widest text-zinc-600">{value}</span>
        </span>
      </div>
      {busy ? <RefreshCw className="h-4 w-4 shrink-0 animate-spin text-zinc-500" /> : <ArrowRight className="h-4 w-4 shrink-0 text-zinc-600" />}
    </>
  );
  const className = "flex min-h-[74px] items-center justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3 text-left transition-colors hover:border-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-50";
  if (href && !disabled && !onClick) {
    return <Link href={href} className={className}>{content}</Link>;
  }
  return (
    <button type="button" onClick={onClick} disabled={disabled || busy} className={className}>
      {content}
    </button>
  );
}

type FollowUpDraft = {
  title: string;
  target_type: string;
  owner_email: string;
  due_at: string;
  severity: string;
};

const EMPTY_FOLLOW_UP: FollowUpDraft = {
  title: '',
  target_type: 'control',
  owner_email: '',
  due_at: '',
  severity: 'medium',
};

export default function SystemDetailPage() {
  const params = useParams();
  const router = useRouter();
  const systemId = params.id as string;

  const [workspace, setWorkspace] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [recordingReview, setRecordingReview] = useState(false);
  const [closingTaskId, setClosingTaskId] = useState<string | null>(null);
  const [runningAction, setRunningAction] = useState<string | null>(null);
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
  const [followUpActions, setFollowUpActions] = useState<FollowUpDraft[]>([{ ...EMPTY_FOLLOW_UP }]);

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
  const followUpTasks = workspace?.follow_up_tasks || [];
  const drillDownActions = workspace?.drill_down_actions || {};
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
        actions: followUpActions
          .filter((action) => action.title.trim())
          .map((action) => ({
            title: action.title.trim(),
            target_type: action.target_type,
            owner_email: action.owner_email.trim() || null,
            due_at: fromDateInput(action.due_at),
            severity: action.severity,
            create_placeholder: action.target_type !== 'general',
          })),
      });
      setReviewForm({
        reviewer_email: '',
        review_type: 'lifecycle_review',
        status: 'completed',
        next_review_at: '',
        notes: '',
      });
      setFollowUpActions([{ ...EMPTY_FOLLOW_UP }]);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to record review');
    } finally {
      setRecordingReview(false);
    }
  }

  function updateFollowUp(index: number, patch: Partial<FollowUpDraft>) {
    setFollowUpActions((current) => current.map((action, actionIndex) => (
      actionIndex === index ? { ...action, ...patch } : action
    )));
  }

  function addFollowUp() {
    setFollowUpActions((current) => [...current, { ...EMPTY_FOLLOW_UP }].slice(0, 5));
  }

  function removeFollowUp(index: number) {
    setFollowUpActions((current) => {
      const next = current.filter((_, actionIndex) => actionIndex !== index);
      return next.length ? next : [{ ...EMPTY_FOLLOW_UP }];
    });
  }

  async function handleCloseFollowUp(taskId: string) {
    setClosingTaskId(taskId);
    setError(null);
    try {
      await api.closeReviewTask(taskId, 'Closed from AI system workspace');
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to close follow-up task');
    } finally {
      setClosingTaskId(null);
    }
  }

  async function handleSeedControls() {
    if (!system) return;
    setRunningAction('controls');
    setError(null);
    try {
      await api.seedBaselineControls(system.id);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to seed controls');
    } finally {
      setRunningAction(null);
    }
  }

  async function handleGenerateReport() {
    if (!system) return;
    setRunningAction('reports');
    setError(null);
    try {
      const report = await api.createReport({
        report_type: 'compliance_readiness_summary',
        ai_system_id: system.id,
        title: `${system.name} Compliance Readiness`,
        source_refs: [{ type: 'ai_system_workspace', ai_system_id: system.id }],
      });
      router.push(`/reports/${report.id}`);
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to generate report');
    } finally {
      setRunningAction(null);
    }
  }

  async function handleStartFria() {
    if (!system) return;
    const existingFria = workspace?.fria_records?.[0];
    if (existingFria?.id) {
      router.push(`/fria/${existingFria.id}`);
      return;
    }
    setRunningAction('fria');
    setError(null);
    try {
      const fria = await api.createFria({
        ai_system_id: system.id,
        status: 'draft',
        assessment_json: {
          source: 'ai_system_workspace',
          system_name: system.name,
          intended_purpose: system.description || system.name,
        },
      });
      router.push(`/fria/${fria.id}`);
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to start FRIA');
    } finally {
      setRunningAction(null);
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

        <Card title="Workspace Actions">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            <WorkspaceAction
              icon={<ListChecks className="h-4 w-4" />}
              label={(drillDownActions.controls?.count || 0) === 0 ? 'Seed Controls' : 'Open Controls'}
              value={`${drillDownActions.controls?.open_count || 0} open`}
              onClick={(drillDownActions.controls?.count || 0) === 0 ? handleSeedControls : undefined}
              href={(drillDownActions.controls?.count || 0) === 0 ? undefined : drillDownActions.controls?.href || `/controls?ai_system_id=${system.id}`}
              busy={runningAction === 'controls'}
            />
            <WorkspaceAction
              icon={<FilePlus2 className="h-4 w-4" />}
              label={(drillDownActions.evidence?.count || 0) === 0 ? 'Add Evidence' : 'Open Evidence'}
              value={`${drillDownActions.evidence?.count || 0} items`}
              href={(drillDownActions.evidence?.count || 0) === 0 ? drillDownActions.evidence?.create_href : drillDownActions.evidence?.href}
            />
            <WorkspaceAction
              icon={<FileText className="h-4 w-4" />}
              label="Generate Report"
              value={`${drillDownActions.reports?.count || 0} reports`}
              onClick={handleGenerateReport}
              busy={runningAction === 'reports'}
            />
            <WorkspaceAction
              icon={<ShieldCheck className="h-4 w-4" />}
              label={drillDownActions.fria?.record_id ? 'Open FRIA' : 'Start FRIA'}
              value={`${drillDownActions.fria?.count || 0} records`}
              onClick={handleStartFria}
              busy={runningAction === 'fria'}
            />
            <WorkspaceAction
              icon={<UserPlus className="h-4 w-4" />}
              label={(drillDownActions.oversight?.count || 0) === 0 ? 'Assign Oversight' : 'Open Oversight'}
              value={`${drillDownActions.oversight?.count || 0} roles`}
              href={(drillDownActions.oversight?.count || 0) === 0 ? drillDownActions.oversight?.create_href : drillDownActions.oversight?.href}
            />
            <WorkspaceAction
              icon={<AlertTriangle className="h-4 w-4" />}
              label={(drillDownActions.incidents?.open_count || 0) === 0 ? 'Report Incident' : 'Open Incidents'}
              value={`${drillDownActions.incidents?.open_count || 0} open`}
              href={(drillDownActions.incidents?.open_count || 0) === 0 ? drillDownActions.incidents?.create_href : drillDownActions.incidents?.href}
            />
          </div>
        </Card>

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
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Follow-up plan</span>
                    <button
                      type="button"
                      onClick={addFollowUp}
                      disabled={followUpActions.length >= 5}
                      className="flex items-center gap-1 rounded-lg bg-zinc-900 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800 disabled:opacity-50"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add
                    </button>
                  </div>
                  {followUpActions.map((action, index) => (
                    <div key={index} className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Action {index + 1}</span>
                        {followUpActions.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeFollowUp(index)}
                            className="rounded-lg bg-zinc-900 p-1.5 text-zinc-500 ring-1 ring-zinc-800 hover:text-red-300"
                            aria-label={`Remove action ${index + 1}`}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                      <label className="space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Action</span>
                        <input
                          value={action.title}
                          onChange={(event) => updateFollowUp(index, { title: event.target.value })}
                          placeholder="Attach evidence or resolve control gap"
                          className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                        />
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        <label className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Target</span>
                          <select
                            value={action.target_type}
                            onChange={(event) => updateFollowUp(index, { target_type: event.target.value })}
                            className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                          >
                            <option value="control">Control</option>
                            <option value="evidence">Evidence</option>
                            <option value="general">General</option>
                          </select>
                        </label>
                        <label className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Severity</span>
                          <select
                            value={action.severity}
                            onChange={(event) => updateFollowUp(index, { severity: event.target.value })}
                            className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                          >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                          </select>
                        </label>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <label className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Owner</span>
                          <input
                            type="email"
                            value={action.owner_email}
                            onChange={(event) => updateFollowUp(index, { owner_email: event.target.value })}
                            placeholder="owner@example.com"
                            className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                          />
                        </label>
                        <label className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Due</span>
                          <input
                            type="date"
                            value={action.due_at}
                            onChange={(event) => updateFollowUp(index, { due_at: event.target.value })}
                            className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                          />
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
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
                <span className="text-xs text-zinc-500">Open follow-ups</span>
                <span className="text-xs font-mono text-zinc-300">{metrics.open_follow_up_task_count || 0}</span>
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
                        {(item.artifacts?.length || 0) > 0 && (
                          <p className="mt-1 text-[10px] font-bold uppercase tracking-widest text-indigo-400">
                            {item.artifacts.length} uploaded file{item.artifacts.length === 1 ? '' : 's'}
                          </p>
                        )}
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

        <Card title={`Review Follow-Ups (${followUpTasks.length})`} subtitle="Open review actions linked back to controls, evidence, or the wider workspace.">
          {followUpTasks.length === 0 ? (
            <EmptyPanel label="No review follow-up tasks" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {followUpTasks.slice(0, 8).map((task: any) => {
                const details = task.findings_json || {};
                return (
                  <div key={task.review_task_id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold text-zinc-200">{details.title || task.trigger_reason}</p>
                        <p className="mt-1 text-[10px] font-mono text-zinc-600">{details.target_type || 'general'} / {task.review_task_id.slice(0, 8)}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <StatusBadge value={task.status} />
                        <StatusBadge value={task.severity || 'medium'} />
                      </div>
                    </div>
                    {details.description && (
                      <p className="mt-3 text-xs leading-5 text-zinc-400">{details.description}</p>
                    )}
                    <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-bold uppercase tracking-widest text-zinc-600">
                      {details.created_placeholder_type && (
                        <span className="rounded bg-zinc-900 px-2 py-1 ring-1 ring-zinc-800">
                          Created {details.created_placeholder_type}
                        </span>
                      )}
                      {details.owner_email && (
                        <span className="rounded bg-zinc-900 px-2 py-1 ring-1 ring-zinc-800">
                          {details.owner_email}
                        </span>
                      )}
                      {details.due_at && (
                        <span className="rounded bg-zinc-900 px-2 py-1 ring-1 ring-zinc-800">
                          Due {displayDate(details.due_at)}
                        </span>
                      )}
                    </div>
                    <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                      <Link href={followUpHref(system.id, task)} className="text-[10px] font-bold uppercase tracking-widest text-indigo-400 hover:text-indigo-300">
                        Open Target
                      </Link>
                      {task.status === 'open' && (
                        <button
                          onClick={() => handleCloseFollowUp(task.review_task_id)}
                          disabled={closingTaskId === task.review_task_id}
                          className="flex items-center gap-1 rounded-lg bg-zinc-900 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800 disabled:opacity-50"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          {closingTaskId === task.review_task_id ? 'Closing' : 'Close'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
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
