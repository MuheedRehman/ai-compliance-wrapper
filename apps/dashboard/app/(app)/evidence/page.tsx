'use client';

import { FormEvent, ReactNode, useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { AlertOctagon, CalendarClock, Clock, Download, FileSearch, Hash, Link as LinkIcon, Plus, ShieldCheck, Upload } from 'lucide-react';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import EmptyState from '@/components/empty-state';
import ErrorState from '@/components/error-state';
import Card from '@/components/card';

const evidenceTypes = [
  'policy',
  'screenshot',
  'model_card',
  'dpia',
  'fria',
  'risk_assessment',
  'human_oversight',
  'log_extract',
  'incident_record',
  'vendor_doc',
  'test_result',
  'report',
  'other',
];

const statuses = ['draft', 'active', 'needs_review', 'expired', 'archived'];

const emptyForm = {
  title: '',
  evidence_type: 'policy',
  source: '',
  source_url: '',
  owner_email: '',
  ai_system_id: '',
  control_id: '',
  review_at: '',
  expires_at: '',
  description: '',
};

function toIsoDate(value: string) {
  return value ? new Date(`${value}T00:00:00.000Z`).toISOString() : undefined;
}

export default function EvidencePage() {
  const searchParams = useSearchParams();
  const systemFilter = searchParams.get('ai_system_id') || '';
  const createRequested = searchParams.get('create') === '1';
  const requestedEvidenceType = searchParams.get('evidence_type') || 'policy';
  const [logs, setLogs] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [systems, setSystems] = useState<any[]>([]);
  const [controls, setControls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadingItemId, setUploadingItemId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(createRequested);
  const [error, setError] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [form, setForm] = useState({
    ...emptyForm,
    ai_system_id: systemFilter,
    control_id: searchParams.get('control_id') || '',
    evidence_type: evidenceTypes.includes(requestedEvidenceType) ? requestedEvidenceType : 'policy',
    source: searchParams.get('source') || '',
  });

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const logParams: Record<string, string> = {};
    const itemParams: Record<string, string> = {};
    if (riskFilter) logParams.risk_level = riskFilter;
    if (decisionFilter) logParams.decision = decisionFilter;
    if (systemFilter) {
      logParams.ai_system_id = systemFilter;
      itemParams.ai_system_id = systemFilter;
    }
    if (statusFilter) itemParams.status = statusFilter;
    if (typeFilter) itemParams.evidence_type = typeFilter;

    Promise.all([
      api.listLogs(Object.keys(logParams).length ? logParams : undefined),
      api.listEvidenceItems(Object.keys(itemParams).length ? itemParams : undefined),
      api.getEvidenceSummary(systemFilter || undefined),
      api.listSystems(),
      api.listControls(systemFilter || undefined),
    ])
      .then(([logData, evidenceItems, evidenceSummary, systemData, controlData]) => {
        setLogs(logData.logs || []);
        setItems(evidenceItems || []);
        setSummary(evidenceSummary);
        setSystems(systemData || []);
        setControls(controlData || []);
      })
      .catch((err) => setError(err.body?.detail || err.message || 'Failed to load evidence vault'))
      .finally(() => setLoading(false));
  }, [riskFilter, decisionFilter, statusFilter, typeFilter, systemFilter]);

  useEffect(() => { load(); }, [load]);

  async function createEvidenceItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const item = await api.createEvidenceItem({
        title: form.title,
        evidence_type: form.evidence_type,
        source: form.source,
        source_url: form.source_url || undefined,
        owner_email: form.owner_email || undefined,
        ai_system_id: form.ai_system_id || systemFilter || undefined,
        control_id: form.control_id || undefined,
        review_at: toIsoDate(form.review_at),
        expires_at: toIsoDate(form.expires_at),
        description: form.description || undefined,
        metadata_json: form.description ? { notes: form.description } : {},
      });
      if (selectedFile) {
        await api.uploadEvidenceArtifact(item.id, selectedFile);
      }
      setSelectedFile(null);
      setForm({ ...emptyForm, ai_system_id: systemFilter });
      setShowCreate(false);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to create evidence item');
    } finally {
      setSubmitting(false);
    }
  }

  async function updateItemStatus(itemId: string, status: string) {
    const updated = await api.updateEvidenceItem(itemId, { status });
    setItems((current) => current.map((item) => item.id === itemId ? updated : item));
  }

  async function uploadArtifact(itemId: string, file?: File | null) {
    if (!file) return;
    setUploadingItemId(itemId);
    setError(null);
    try {
      await api.uploadEvidenceArtifact(itemId, file);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to upload evidence artifact');
    } finally {
      setUploadingItemId(null);
    }
  }

  const blockedCount = logs.filter((log) => log.decision?.toLowerCase() === 'block').length;
  const highRiskCount = logs.filter((log) => log.risk_level?.toLowerCase() === 'high').length;
  const dueCount = summary?.due_for_review_count || 0;
  const expiringCount = summary?.expiring_soon_count || 0;

  return (
    <PageShell
      title="Evidence Vault"
      subtitle="Audit artifacts, review dates, and immutable evidence events for AI governance."
      breadcrumbs={[{ label: 'Evidence' }]}
      actions={
        <button
          onClick={() => setShowCreate((current) => !current)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" />
          {showCreate ? 'CLOSE FORM' : 'NEW EVIDENCE ITEM'}
        </button>
      }
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card title="Vault Items" variant="stat">
            <span className="text-2xl font-bold">{summary?.total_items ?? items.length}</span>
          </Card>
          <Card title="Review Due" variant="stat">
            <span className="text-2xl font-bold text-amber-500">{dueCount}</span>
          </Card>
          <Card title="Expiring Soon" variant="stat">
            <span className="text-2xl font-bold text-red-500">{expiringCount}</span>
          </Card>
          <Card title="Evidence Events" variant="stat">
            <span className="text-2xl font-bold text-emerald-500">{logs.length}</span>
          </Card>
        </div>

        {showCreate && (
          <Card title="Register Evidence Item" subtitle="Create a signed audit artifact record linked to a system or control.">
            <form onSubmit={createEvidenceItem} className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
              <input required placeholder="Evidence title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <select value={form.evidence_type} onChange={(e) => setForm({ ...form, evidence_type: e.target.value })}>
                {evidenceTypes.map((type) => <option key={type} value={type}>{type}</option>)}
              </select>
              <input required placeholder="Source" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} />
              <input type="email" placeholder="owner@company.com" value={form.owner_email} onChange={(e) => setForm({ ...form, owner_email: e.target.value })} />
              <select value={form.ai_system_id || systemFilter} onChange={(e) => setForm({ ...form, ai_system_id: e.target.value, control_id: '' })}>
                <option value="">Unlinked AI system</option>
                {systems.map((system) => <option key={system.id} value={system.id}>{system.name}</option>)}
              </select>
              <select value={form.control_id} onChange={(e) => setForm({ ...form, control_id: e.target.value })}>
                <option value="">Unlinked control</option>
                {controls.map((control) => <option key={control.id} value={control.id}>{control.title}</option>)}
              </select>
              <input type="url" placeholder="https://source.example/document" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} />
              <input type="date" value={form.review_at} onChange={(e) => setForm({ ...form, review_at: e.target.value })} />
              <input type="date" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })} />
              <label className="flex min-h-10 cursor-pointer items-center gap-2 rounded-lg border border-dashed border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-400 hover:border-indigo-500/40">
                <Upload className="h-4 w-4 text-zinc-500" />
                <span className="truncate">{selectedFile ? selectedFile.name : 'Attach file artifact'}</span>
                <input type="file" className="hidden" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
              </label>
              <textarea className="md:col-span-2 xl:col-span-3 min-h-20" placeholder="Notes or evidence description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <div className="flex items-end gap-2">
                <button disabled={submitting} className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white disabled:opacity-50">
                  {submitting ? 'Saving...' : 'Save Evidence Item'}
                </button>
                <button type="button" onClick={() => setShowCreate(false)} className="rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800">
                  Cancel
                </button>
              </div>
            </form>
          </Card>
        )}

        <Card className="bg-zinc-950 px-6 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {systemFilter && (
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">AI System</label>
                <div className="text-[10px] font-mono text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 rounded px-3 py-2">
                  {systemFilter}
                </div>
              </div>
            )}
            <FilterGroup
              icon={<FileSearch className="h-3 w-3" />}
              label="Evidence Type"
              values={['', 'policy', 'fria', 'model_card', 'vendor_doc', 'test_result']}
              active={typeFilter}
              onChange={setTypeFilter}
              allLabel="All Types"
            />
            <FilterGroup
              icon={<CalendarClock className="h-3 w-3" />}
              label="Vault Status"
              values={['', 'active', 'needs_review', 'expired', 'archived']}
              active={statusFilter}
              onChange={setStatusFilter}
              allLabel="All Status"
            />
            <FilterGroup
              icon={<AlertOctagon className="h-3 w-3" />}
              label="Event Risk"
              values={['', 'high', 'medium', 'low']}
              active={riskFilter}
              onChange={setRiskFilter}
              allLabel="All Risks"
            />
            <FilterGroup
              icon={<ShieldCheck className="h-3 w-3" />}
              label="Policy Decision"
              values={['', 'allow', 'block', 'flag']}
              active={decisionFilter}
              onChange={setDecisionFilter}
              allLabel="All Decisions"
            />
          </div>
        </Card>

        {loading ? (
          <Loading />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : (
          <>
            <Card title={`Vault Items (${items.length})`} subtitle="Signed artifact records for audit readiness.">
              {items.length === 0 ? (
                <EmptyState
                  title="No vault items recorded"
                  message="Register policies, model cards, assessments, screenshots, vendor docs, and test results here."
                  icon={FileSearch}
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Artifact</th>
                        <th>Owner</th>
                        <th>Status</th>
                        <th>Review</th>
                        <th>File</th>
                        <th>Hash</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => (
                        <tr key={item.id}>
                          <td>
                            <div className="flex flex-col">
                              <span className="text-xs font-bold text-zinc-200">{item.title}</span>
                              <span className="text-[10px] text-zinc-500 font-mono">{item.evidence_type} / {item.id}</span>
                              {item.source_url && (
                                <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300">
                                  <LinkIcon className="h-3 w-3" />
                                  Source
                                </a>
                              )}
                            </div>
                          </td>
                          <td className="text-[10px] font-mono text-zinc-400">{item.owner_email || item.source}</td>
                          <td>
                            <select value={item.status} onChange={(e) => updateItemStatus(item.id, e.target.value)} className="min-w-32">
                              {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
                            </select>
                          </td>
                          <td className="text-[10px] text-zinc-500 font-bold uppercase whitespace-nowrap">
                            {item.review_at ? new Date(item.review_at).toLocaleDateString() : 'Not set'}
                          </td>
                          <td className="min-w-[220px]">
                            <div className="space-y-2">
                              {(item.artifacts || []).length > 0 ? (
                                <a
                                  href={api.getEvidenceArtifactUrl(item.id, item.artifacts[0].id)}
                                  className="inline-flex max-w-[220px] items-center gap-1 text-[10px] font-bold text-indigo-400 hover:text-indigo-300"
                                >
                                  <Download className="h-3 w-3 shrink-0" />
                                  <span className="truncate">{item.artifacts[0].file_name}</span>
                                </a>
                              ) : (
                                <span className="text-[10px] text-zinc-600">No file</span>
                              )}
                              <label className="flex cursor-pointer items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:text-zinc-300">
                                <Upload className="h-3 w-3" />
                                {uploadingItemId === item.id ? 'Uploading' : 'Upload'}
                                <input type="file" className="hidden" onChange={(e) => uploadArtifact(item.id, e.target.files?.[0])} />
                              </label>
                            </div>
                          </td>
                          <td className="text-[10px] text-zinc-500 font-mono">
                            <span className="inline-flex items-center gap-1">
                              <Hash className="h-3 w-3" />
                              {item.evidence_hash?.slice(0, 12)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            <Card title={`Immutable Event Logs (${logs.length})`} subtitle="Runtime and compliance events captured by the evidence chain.">
              {logs.length === 0 ? (
                <EmptyState
                  title="No evidence events recorded"
                  message="Logs populate as AI systems process governed requests and compliance workflows run."
                  icon={FileSearch}
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th>Event ID</th>
                        <th>Feature Identity</th>
                        <th>Compliance Action</th>
                        <th>Risk Level</th>
                        <th>Latency</th>
                        <th>Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.event_id} className="group">
                          <td>
                            <div className="flex flex-col">
                              <span className="text-[10px] font-bold text-zinc-300 tracking-wider">{log.event_type}</span>
                              <span className="text-[10px] text-zinc-600 font-mono mt-0.5">{log.event_id?.slice(0, 12)}...</span>
                            </div>
                          </td>
                          <td className="text-[10px] font-mono text-zinc-400">{log.feature_id || '-'}</td>
                          <td><StatusBadge value={log.decision} /></td>
                          <td><StatusBadge value={log.risk_level} /></td>
                          <td className="text-[10px] text-zinc-500 font-bold font-mono">
                            <span className="flex items-center gap-1">
                              <Clock className="h-2.5 w-2.5" />
                              {log.latency_ms != null ? `${log.latency_ms}ms` : '-'}
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
              )}
            </Card>
          </>
        )}
      </div>
    </PageShell>
  );
}

function FilterGroup({
  icon,
  label,
  values,
  active,
  onChange,
  allLabel,
}: {
  icon: ReactNode;
  label: string;
  values: string[];
  active: string;
  onChange: (value: string) => void;
  allLabel: string;
}) {
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5">
        {icon}
        {label}
      </label>
      <div className="flex flex-wrap gap-2">
        {values.map((value) => (
          <button
            key={value || allLabel}
            onClick={() => onChange(value)}
            className={`px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider transition-all ${
              active === value ? 'bg-zinc-100 text-black' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'
            }`}
          >
            {value || allLabel}
          </button>
        ))}
      </div>
    </div>
  );
}
