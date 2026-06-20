'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import {
  ShieldCheck, ChevronLeft, Trash2, CheckCircle2, Clock, XCircle,
  ChevronRight, ChevronLeft as ChevronPrev, Download, Send, Eye,
  AlertCircle, Save,
} from 'lucide-react';

// ---- Section definitions ----
const SECTIONS = [
  {
    key: 'intended_purpose',
    title: 'Intended Purpose',
    description: 'Describe the AI system and the context in which it is deployed.',
    fields: [
      { key: 'system_description', label: 'System Description', placeholder: 'Describe what the AI system does and its primary function…', rows: 4 },
      { key: 'deployment_context', label: 'Deployment Context', placeholder: 'Where and how is the system deployed (sector, environment)?', rows: 3 },
      { key: 'intended_users', label: 'Intended Users', placeholder: 'Who operates or interacts with the system?', rows: 2 },
      { key: 'geographic_scope', label: 'Geographic Scope', placeholder: 'Which regions, countries, or jurisdictions are affected?', rows: 2 },
    ],
  },
  {
    key: 'affected_persons',
    title: 'Affected Persons',
    description: "Identify who is affected by the AI system's outputs or decisions.",
    fields: [
      { key: 'population_description', label: 'Population Description', placeholder: "Describe the persons who are subject to the AI system's decisions or outputs…", rows: 4 },
      { key: 'vulnerable_groups', label: 'Vulnerable Groups', placeholder: 'Are there vulnerable individuals (minors, elderly, marginalised groups)?', rows: 3 },
      { key: 'estimated_scale', label: 'Estimated Scale', placeholder: 'How many people are affected per year or deployment period?', rows: 2 },
      { key: 'interaction_type', label: 'Interaction Type', placeholder: 'Direct (output shown to person), indirect (used by operator), automated decision-making?', rows: 2 },
    ],
  },
  {
    key: 'fundamental_rights_risks',
    title: 'Fundamental Rights Risks',
    description: 'Identify which fundamental rights are at risk and assess the severity and likelihood.',
    fields: [
      { key: 'rights_at_risk', label: 'Rights at Risk', placeholder: 'List the fundamental rights potentially affected (e.g. right to non-discrimination, right to explanation, right to privacy)…', rows: 4 },
      { key: 'risk_descriptions', label: 'Risk Descriptions', placeholder: 'Describe how each identified risk could materialise in practice…', rows: 4 },
      { key: 'severity_assessment', label: 'Severity Assessment', placeholder: 'Rate the severity of the identified risks (Low / Medium / High / Critical) and explain the rating…', rows: 3 },
      { key: 'likelihood_assessment', label: 'Likelihood Assessment', placeholder: 'Rate the likelihood of each risk materialising and explain based on evidence or comparable cases…', rows: 3 },
    ],
  },
  {
    key: 'mitigation_measures',
    title: 'Mitigation Measures',
    description: 'Document the technical, organisational, and human measures that reduce identified risks.',
    fields: [
      { key: 'technical_measures', label: 'Technical Measures', placeholder: 'Describe technical controls: bias audits, explainability tools, input validation, output filtering…', rows: 4 },
      { key: 'organizational_measures', label: 'Organisational Measures', placeholder: 'Describe organisational controls: policies, training, third-party audits, governance structures…', rows: 4 },
      { key: 'human_oversight_measures', label: 'Human Oversight Measures', placeholder: 'How do humans intervene, override, or review system outputs?', rows: 3 },
      { key: 'monitoring_approach', label: 'Monitoring Approach', placeholder: 'How will ongoing effectiveness of mitigations be monitored and reported?', rows: 3 },
    ],
  },
  {
    key: 'human_oversight',
    title: 'Human Oversight',
    description: 'Define oversight roles, procedures, and escalation paths as required by the EU AI Act.',
    fields: [
      { key: 'oversight_roles', label: 'Oversight Roles', placeholder: 'Who holds accountability for oversight (job titles, departments)?', rows: 3 },
      { key: 'oversight_procedures', label: 'Oversight Procedures', placeholder: 'Describe the procedures for periodic review and monitoring of the system…', rows: 4 },
      { key: 'override_capability', label: 'Override Capability', placeholder: "Can responsible persons halt, override, or reverse the system's outputs? Describe how.", rows: 3 },
      { key: 'escalation_path', label: 'Escalation Path', placeholder: 'Define the escalation path when a human oversight concern or incident is raised…', rows: 3 },
    ],
  },
  {
    key: 'residual_risk',
    title: 'Residual Risk',
    description: 'Document remaining risks after mitigations and obtain DPO sign-off.',
    fields: [
      { key: 'remaining_risks', label: 'Remaining Risks', placeholder: 'What risks remain after applying all mitigation measures?', rows: 4 },
      { key: 'risk_acceptance_rationale', label: 'Risk Acceptance Rationale', placeholder: 'Explain why the residual risks are acceptable and who approved this determination…', rows: 4 },
      { key: 'review_schedule', label: 'Review Schedule', placeholder: 'When will the FRIA be reviewed and updated (e.g. annually, on significant change)?', rows: 2 },
      { key: 'dpo_consulted', label: 'DPO Consultation', placeholder: 'Was the Data Protection Officer consulted? Provide date and outcome…', rows: 2 },
    ],
  },
] as const;

type SectionKey = typeof SECTIONS[number]['key'];

// ---- Small helpers ----
function isSectionComplete(data: Record<string, any>): boolean {
  return Object.values(data).some(v => typeof v === 'string' && v.trim().length > 0);
}

function CompletionBar({ percent }: { percent: number }) {
  const color = percent === 100 ? 'bg-emerald-500' : percent >= 50 ? 'bg-indigo-500' : 'bg-zinc-600';
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${percent}%` }} />
      </div>
      <span className="text-xs font-bold text-zinc-400 tabular-nums">{percent}%</span>
    </div>
  );
}

// ---- Submit modal ----
function SubmitModal({ onConfirm, onClose }: { onConfirm: (email: string) => void; onClose: () => void }) {
  const [email, setEmail] = useState('');
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 w-full max-w-md space-y-4">
        <h3 className="text-lg font-bold text-white">Submit FRIA for Review</h3>
        <p className="text-sm text-zinc-400">Enter your email to submit this assessment for approval. The status will change to <strong>In Review</strong>.</p>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="your@email.com"
          className="w-full bg-zinc-800 border border-zinc-700 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <div className="flex gap-2">
          <button
            onClick={() => email && onConfirm(email)}
            disabled={!email}
            className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors disabled:opacity-50"
          >
            Submit for Review
          </button>
          <button onClick={onClose} className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-white text-sm font-bold transition-colors">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ---- Review modal (approve / reject) ----
function ReviewModal({ onConfirm, onClose }: { onConfirm: (d: { reviewer_email: string; outcome: string; notes: string }) => void; onClose: () => void }) {
  const [email, setEmail] = useState('');
  const [outcome, setOutcome] = useState<'approved' | 'rejected'>('approved');
  const [notes, setNotes] = useState('');
  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 w-full max-w-md space-y-4">
        <h3 className="text-lg font-bold text-white">Review FRIA</h3>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="reviewer@email.com"
          className="w-full bg-zinc-800 border border-zinc-700 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <div className="flex gap-2">
          {(['approved', 'rejected'] as const).map(o => (
            <button
              key={o}
              onClick={() => setOutcome(o)}
              className={`flex-1 py-2 rounded-lg text-sm font-bold border transition-colors ${outcome === o
                ? o === 'approved' ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-red-600 border-red-600 text-white'
                : 'bg-transparent border-zinc-700 text-zinc-400 hover:border-zinc-500'
              }`}
            >
              {o === 'approved' ? '✓ Approve' : '✗ Reject'}
            </button>
          ))}
        </div>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Review notes (optional)…"
          rows={3}
          className="w-full bg-zinc-800 border border-zinc-700 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
        />
        <div className="flex gap-2">
          <button
            onClick={() => email && onConfirm({ reviewer_email: email, outcome, notes })}
            disabled={!email}
            className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors disabled:opacity-50"
          >
            Submit Review
          </button>
          <button onClick={onClose} className="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-white text-sm font-bold transition-colors">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

// ---- Main page ----
export default function FriaDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [fria, setFria] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(0);
  const [sectionData, setSectionData] = useState<Record<SectionKey, Record<string, string>>>({} as any);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [showSubmit, setShowSubmit] = useState(false);
  const [showReview, setShowReview] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    api.getFria(id as string)
      .then(data => {
        setFria(data);
        setSectionData(data.sections_json || {} as any);
      })
      .catch(() => router.push('/fria'))
      .finally(() => setLoading(false));
  }, [id, router]);

  const handleFieldChange = (sectionKey: SectionKey, fieldKey: string, value: string) => {
    setSectionData(prev => ({
      ...prev,
      [sectionKey]: { ...(prev[sectionKey] || {}), [fieldKey]: value },
    }));
  };

  const handleSaveSection = useCallback(async () => {
    const key = SECTIONS[activeSection].key as SectionKey;
    setSaving(true);
    setSaveMsg(null);
    try {
      const updated = await api.updateFriaSections(id as string, { [key]: sectionData[key] || {} });
      setFria(updated);
      setSaveMsg('Saved');
      setTimeout(() => setSaveMsg(null), 2000);
    } catch {
      setSaveMsg('Save failed');
    } finally {
      setSaving(false);
    }
  }, [id, activeSection, sectionData]);

  const handleSubmit = async (email: string) => {
    setShowSubmit(false);
    setActionError(null);
    try {
      const updated = await api.submitFria(id as string, { submitted_by: email });
      setFria(updated);
    } catch (err: any) {
      setActionError(err?.message || 'Submit failed.');
    }
  };

  const handleReview = async (data: { reviewer_email: string; outcome: string; notes: string }) => {
    setShowReview(false);
    setActionError(null);
    try {
      const updated = await api.reviewFria(id as string, data);
      setFria(updated);
    } catch (err: any) {
      setActionError(err?.message || 'Review failed.');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Delete this FRIA permanently?')) return;
    try {
      await api.deleteFria(id as string);
      router.push('/fria');
    } catch {
      setActionError('Delete failed.');
    }
  };

  const handleExport = () => {
    window.open(`/api/fria/${id}/export`, '_blank');
  };

  if (loading) return <PageShell title="FRIA Builder" subtitle="Loading…"><Loading /></PageShell>;
  if (!fria) return null;

  const isEditable = fria.status === 'draft' || fria.status === 'rejected';
  const isInReview = fria.status === 'in_review';
  const isApproved = fria.status === 'approved';
  const approval = fria.approval_json || {};

  const section = SECTIONS[activeSection];
  const currentData: Record<string, string> = (sectionData as any)[section.key] || {};

  return (
    <>
      {showSubmit && <SubmitModal onConfirm={handleSubmit} onClose={() => setShowSubmit(false)} />}
      {showReview && <ReviewModal onConfirm={handleReview} onClose={() => setShowReview(false)} />}

      <PageShell
        title={`FRIA: ${fria.id}`}
        subtitle={`Fundamental Rights Impact Assessment — Article 27 EU AI Act`}
      >
        <div className="space-y-6 animate-fade-in">
          {/* Back + status bar */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-xs font-bold text-zinc-500 hover:text-zinc-300 transition-colors uppercase tracking-wider"
            >
              <ChevronLeft className="h-3 w-3" /> Back to List
            </button>
            <div className="flex items-center gap-2">
              <StatusBadge value={fria.status} />
            </div>
          </div>

          {actionError && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {actionError}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Left: section nav + wizard */}
            <div className="lg:col-span-3 space-y-4">
              {/* Progress */}
              <Card>
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Overall Completion</span>
                    <span className="text-xs text-zinc-400">{fria.completion_percent}% complete</span>
                  </div>
                  <CompletionBar percent={fria.completion_percent} />

                  {/* Section tabs */}
                  <div className="flex flex-wrap gap-1.5 mt-4">
                    {SECTIONS.map((s, i) => {
                      const done = isSectionComplete((sectionData as any)[s.key] || {});
                      return (
                        <button
                          key={s.key}
                          onClick={() => setActiveSection(i)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                            activeSection === i
                              ? 'bg-indigo-600 border-indigo-600 text-white'
                              : done
                              ? 'bg-zinc-900 border-emerald-700/50 text-emerald-400'
                              : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:text-zinc-300 hover:border-zinc-700'
                          }`}
                        >
                          {done && activeSection !== i && <CheckCircle2 className="h-3 w-3" />}
                          <span>{i + 1}. {s.title}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </Card>

              {/* Active section form */}
              <Card title={`${activeSection + 1}. ${section.title}`}>
                <p className="text-xs text-zinc-500 mb-5 leading-relaxed">{section.description}</p>
                <div className="space-y-5">
                  {section.fields.map(field => (
                    <div key={field.key}>
                      <label className="block text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1.5">{field.label}</label>
                      <textarea
                        value={currentData[field.key] || ''}
                        onChange={e => handleFieldChange(section.key as SectionKey, field.key, e.target.value)}
                        placeholder={field.placeholder}
                        rows={field.rows}
                        disabled={!isEditable}
                        className="w-full bg-zinc-900 border border-zinc-700 text-white text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none placeholder-zinc-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                    </div>
                  ))}
                </div>

                {/* Section nav + save */}
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800/60">
                  <button
                    onClick={() => setActiveSection(i => Math.max(0, i - 1))}
                    disabled={activeSection === 0}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white text-xs font-bold transition-colors disabled:opacity-30"
                  >
                    <ChevronPrev className="h-3.5 w-3.5" /> Previous
                  </button>

                  <div className="flex items-center gap-2">
                    {saveMsg && (
                      <span className={`text-xs font-bold ${saveMsg === 'Saved' ? 'text-emerald-400' : 'text-red-400'}`}>{saveMsg}</span>
                    )}
                    {isEditable && (
                      <button
                        onClick={handleSaveSection}
                        disabled={saving}
                        className="flex items-center gap-1.5 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                      >
                        <Save className="h-3.5 w-3.5" />
                        {saving ? 'Saving…' : 'Save Section'}
                      </button>
                    )}
                  </div>

                  <button
                    onClick={() => setActiveSection(i => Math.min(SECTIONS.length - 1, i + 1))}
                    disabled={activeSection === SECTIONS.length - 1}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white text-xs font-bold transition-colors disabled:opacity-30"
                  >
                    Next <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </Card>
            </div>

            {/* Right: metadata + actions */}
            <div className="space-y-4">
              <Card title="Assessment Info">
                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">FRIA ID</p>
                    <p className="text-xs text-zinc-300 font-mono mt-0.5">{fria.id}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">AI System</p>
                    <p className="text-xs text-zinc-300 font-mono mt-0.5">{fria.ai_system_id}</p>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">Legal Basis</p>
                    {(fria.legal_basis_json || []).map((ref: any, i: number) => (
                      <p key={i} className="text-xs text-indigo-400 mt-0.5">{ref.article} — {ref.title}</p>
                    ))}
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">Created</p>
                    <p className="text-xs text-zinc-400 mt-0.5">{new Date(fria.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </Card>

              {/* Approval info */}
              {(isInReview || isApproved || fria.status === 'rejected') && approval.submitted_by && (
                <Card title="Approval Record">
                  <div className="space-y-3 text-xs">
                    <div>
                      <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">Submitted by</p>
                      <p className="text-zinc-300 mt-0.5">{approval.submitted_by}</p>
                    </div>
                    {approval.reviewed_by && (
                      <>
                        <div>
                          <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">Reviewed by</p>
                          <p className="text-zinc-300 mt-0.5">{approval.reviewed_by}</p>
                        </div>
                        <div>
                          <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">Outcome</p>
                          <p className={`font-bold mt-0.5 ${approval.outcome === 'approved' ? 'text-emerald-400' : 'text-red-400'}`}>
                            {approval.outcome === 'approved' ? '✓ Approved' : '✗ Rejected'}
                          </p>
                        </div>
                        {approval.notes && (
                          <div>
                            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider">Notes</p>
                            <p className="text-zinc-400 mt-0.5 leading-relaxed">{approval.notes}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </Card>
              )}

              {/* Actions */}
              <Card title="Actions">
                <div className="space-y-2">
                  {/* Submit */}
                  {isEditable && fria.completion_percent > 0 && (
                    <button
                      onClick={() => setShowSubmit(true)}
                      className="w-full flex items-center justify-center gap-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-bold transition-colors"
                    >
                      <Send className="h-4 w-4" />
                      Submit for Review
                    </button>
                  )}

                  {/* Review (admin) */}
                  {isInReview && (
                    <button
                      onClick={() => setShowReview(true)}
                      className="w-full flex items-center justify-center gap-2 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-bold transition-colors"
                    >
                      <Eye className="h-4 w-4" />
                      Approve / Reject
                    </button>
                  )}

                  {/* Export */}
                  <button
                    onClick={handleExport}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-bold transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    Export Markdown
                  </button>

                  {/* Delete */}
                  {!isApproved && (
                    <button
                      onClick={handleDelete}
                      className="w-full flex items-center justify-center gap-2 py-2 bg-transparent text-zinc-500 hover:text-red-400 hover:bg-red-400/5 rounded-lg text-sm font-bold transition-all"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete FRIA
                    </button>
                  )}
                </div>
              </Card>

              {/* Status guide */}
              <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/60 space-y-2">
                <p className="text-xs font-bold text-white">Workflow</p>
                {[
                  { icon: <Clock className="h-3 w-3 text-zinc-400" />, label: 'Draft', note: 'Fill all 6 sections' },
                  { icon: <Eye className="h-3 w-3 text-amber-400" />, label: 'In Review', note: 'Awaiting approval' },
                  { icon: <CheckCircle2 className="h-3 w-3 text-emerald-400" />, label: 'Approved', note: 'FRIA complete' },
                  { icon: <XCircle className="h-3 w-3 text-red-400" />, label: 'Rejected', note: 'Revise and resubmit' },
                ].map(step => (
                  <div key={step.label} className="flex items-center gap-2">
                    {step.icon}
                    <span className="text-xs font-bold text-zinc-300">{step.label}</span>
                    <span className="text-[10px] text-zinc-600">— {step.note}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </PageShell>
    </>
  );
}
