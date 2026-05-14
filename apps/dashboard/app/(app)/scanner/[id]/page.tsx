'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowLeft, CheckCircle2, ExternalLink, FileSearch, FileText, Layers, ListChecks, ShieldCheck } from 'lucide-react';
import { api } from '@/lib/api';
import Card from '@/components/card';
import ErrorState from '@/components/error-state';
import Loading from '@/components/loading';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';

export default function ScannerDetailPage({ params }: { params: { id: string } }) {
  const [scan, setScan] = useState<any>(null);
  const [conversionResult, setConversionResult] = useState<any>(null);
  const [generatedReport, setGeneratedReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    api.getWebsiteScan(params.id)
      .then(setScan)
      .catch((err) => setError(err.body?.detail || err.message || 'Failed to load website scan'))
      .finally(() => setLoading(false));
  }, [params.id]);

  useEffect(() => { load(); }, [load]);

  async function convert() {
    setConverting(true);
    setError(null);
    try {
      const result = await api.convertWebsiteScan(params.id);
      setScan(result.scan);
      setConversionResult(result);
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to convert scan');
    } finally {
      setConverting(false);
    }
  }

  async function generateReport() {
    setGeneratingReport(true);
    setError(null);
    try {
      const result = await api.generateWebsiteScanReport(params.id);
      setScan(result.scan);
      setConversionResult(result);
      setGeneratedReport(result.report);
    } catch (err: any) {
      setError(err.body?.error?.message || err.body?.detail || err.message || 'Failed to generate report');
    } finally {
      setGeneratingReport(false);
    }
  }

  if (loading) return <PageShell title="Website Scan" subtitle="Loading scanner result."><Loading /></PageShell>;
  if (error || !scan) return <PageShell title="Website Scan" subtitle="Scanner result unavailable."><ErrorState message={error || 'Scan not found'} onRetry={load} /></PageShell>;

  const classification = scan.classification_json || {};
  const highRisk = ['high', 'prohibited_review'].includes(classification.risk_level);
  const obligationDimensions = classification.obligation_dimensions || [];
  const annexMatches = classification.annex_iii_matches || [];

  return (
    <PageShell
      title={scan.title || 'Website Scan'}
      subtitle={scan.summary || scan.normalized_url}
      breadcrumbs={[{ label: 'Website Scanner', href: '/scanner' }, { label: scan.id }]}
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/scanner" className="flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-xs font-bold text-zinc-300 ring-1 ring-zinc-800 hover:bg-zinc-800">
            <ArrowLeft className="h-4 w-4" />
            BACK
          </Link>
          <button
            disabled={converting || scan.ai_system_id}
            onClick={convert}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            <Layers className="h-4 w-4" />
            {scan.ai_system_id ? 'WORKSPACE READY' : converting ? 'CONVERTING...' : 'CREATE WORKSPACE'}
          </button>
          <button
            disabled={generatingReport || scan.status !== 'completed'}
            onClick={generateReport}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            <FileText className="h-4 w-4" />
            {generatingReport ? 'GENERATING...' : 'GENERATE REPORT'}
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <Card title="Status" variant="stat">
            <StatusBadge value={scan.status} />
          </Card>
          <Card title="Risk Level" variant="stat">
            <span className={`text-2xl font-bold ${highRisk ? 'text-amber-400' : 'text-indigo-400'}`}>
              {classification.risk_level || 'unknown'}
            </span>
          </Card>
          <Card title="Confidence" variant="stat">
            <span className="text-3xl font-bold">{scan.confidence_score}%</span>
          </Card>
          <Card title="Sources" variant="stat">
            <span className="text-3xl font-bold">{scan.source_pages_json?.length || 0}</span>
          </Card>
        </div>

        <Card title="Preliminary Classification">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              {highRisk ? <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" /> : <ShieldCheck className="h-5 w-5 text-emerald-400 mt-0.5" />}
              <div>
                <h3 className="text-sm font-bold text-white">{classification.classification || 'Unknown'}</h3>
                <p className="text-sm text-zinc-400 mt-1">{classification.rationale}</p>
                <p className="text-[11px] text-zinc-500 mt-2 font-mono">Path: {classification.obligation_path || 'MANUAL_REVIEW'}</p>
              </div>
            </div>
            {scan.ai_system_id && scan.intake_id && (
              <div className="flex flex-wrap gap-3 pt-3 border-t border-zinc-800">
                <Link href={`/systems/${scan.ai_system_id}`} className="text-xs font-bold text-indigo-400 hover:text-indigo-300">
                  Open AI System
                </Link>
                <Link href={`/intake/${scan.intake_id}`} className="text-xs font-bold text-indigo-400 hover:text-indigo-300">
                  Open Intake
                </Link>
                <Link href={`/controls?ai_system_id=${scan.ai_system_id}`} className="text-xs font-bold text-indigo-400 hover:text-indigo-300">
                  Open Controls
                </Link>
                <Link href={`/evidence?ai_system_id=${scan.ai_system_id}`} className="text-xs font-bold text-indigo-400 hover:text-indigo-300">
                  Open Evidence
                </Link>
                {generatedReport && (
                  <Link href={`/reports/${generatedReport.id}`} className="text-xs font-bold text-emerald-400 hover:text-emerald-300">
                    Open Report
                  </Link>
                )}
              </div>
            )}
          </div>
        </Card>

        {annexMatches.length > 0 && (
          <Card title="Matched Annex III Categories">
            <div className="space-y-3">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                {annexMatches.map((match: any) => (
                  <div key={match.subcategory_id} className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] font-mono uppercase text-amber-300">{match.annex_ref} | {match.article}</p>
                        <h3 className="mt-1 text-sm font-bold text-white">{match.subcategory}</h3>
                        <p className="mt-1 text-xs font-medium text-zinc-400">{match.area}</p>
                      </div>
                      <span className="rounded bg-amber-500/10 px-2 py-1 text-[10px] font-mono uppercase text-amber-300 ring-1 ring-amber-500/20">
                        {match.confidence} {match.confidence_score}%
                      </span>
                    </div>
                    <p className="mt-3 text-xs leading-relaxed text-zinc-500">{match.summary}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(match.matched_terms || []).map((term: string) => (
                        <span key={term} className="rounded bg-zinc-950 px-2 py-1 text-[10px] font-mono uppercase text-zinc-400 ring-1 ring-zinc-800">
                          {term}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {obligationDimensions.length > 0 && (
          <Card title="Applicable EU AI Act Dimensions">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono uppercase text-zinc-500">
                <span>Canonical: {classification.canonical_classification || classification.classification || 'Unknown'}</span>
                <span>Role: {classification.canonical_actor_role || classification.actor_assumption || 'Unknown'}</span>
                <span>Mapping confidence: {classification.scanner_to_obligation_confidence || 0}%</span>
                {classification.manual_review_required && <span className="text-amber-300">Manual review required</span>}
              </div>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
                {obligationDimensions.map((dimension: any) => (
                  <div key={dimension.dimension_id} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-bold text-white">{dimension.pillar}</h3>
                        <p className="mt-1 text-xs leading-relaxed text-zinc-500">{dimension.summary}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className="rounded bg-zinc-900 px-2 py-1 text-[10px] font-mono uppercase text-zinc-400 ring-1 ring-zinc-800">
                          {dimension.article}
                        </span>
                        <span className="rounded bg-indigo-500/10 px-2 py-1 text-[10px] font-mono uppercase text-indigo-300 ring-1 ring-indigo-500/20">
                          {dimension.status}
                        </span>
                      </div>
                    </div>
                    <p className="mt-3 text-xs leading-relaxed text-zinc-400">{dimension.explanation}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(dimension.matched_public_signals || []).length > 0 ? (
                        dimension.matched_public_signals.map((signal: string) => (
                          <span key={signal} className="rounded bg-emerald-500/10 px-2 py-1 text-[10px] font-mono uppercase text-emerald-300 ring-1 ring-emerald-500/20">
                            {signal}
                          </span>
                        ))
                      ) : (
                        <span className="rounded bg-amber-500/10 px-2 py-1 text-[10px] font-mono uppercase text-amber-300 ring-1 ring-amber-500/20">
                          inferred from classification
                        </span>
                      )}
                    </div>
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 border-t border-zinc-900 pt-3">
                      <div>
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-600">Controls</p>
                        <p className="text-xs text-zinc-500">
                          {(dimension.required_controls || []).map((control: any) => control.title).join(', ') || 'No control template listed'}
                        </p>
                      </div>
                      <div>
                        <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-600">Evidence</p>
                        <p className="text-xs text-zinc-500">
                          {(dimension.required_evidence || []).map((item: any) => `${item.type}:${item.domain}`).join(', ') || 'No evidence requirement listed'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {scan.ai_system_id && (
          <Card title="Compliance Workspace Starter Pack">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Link href={`/systems/${scan.ai_system_id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-indigo-500/40">
                <div className="flex items-center gap-2 mb-2">
                  <Layers className="h-4 w-4 text-indigo-400" />
                  <span className="text-xs font-bold text-zinc-200">AI System</span>
                </div>
                <p className="text-[11px] font-mono text-zinc-500">{scan.ai_system_id}</p>
              </Link>
              <Link href={`/controls?ai_system_id=${scan.ai_system_id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-indigo-500/40">
                <div className="flex items-center gap-2 mb-2">
                  <ListChecks className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-bold text-zinc-200">Control Plan</span>
                </div>
                <p className="text-[11px] text-zinc-500">
                  {conversionResult?.controls?.length ? `${conversionResult.controls.length} controls materialized` : 'System-specific controls ready'}
                </p>
              </Link>
              <Link href={`/evidence?ai_system_id=${scan.ai_system_id}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-indigo-500/40">
                <div className="flex items-center gap-2 mb-2">
                  <FileSearch className="h-4 w-4 text-amber-400" />
                  <span className="text-xs font-bold text-zinc-200">Evidence Log</span>
                </div>
                <p className="text-[11px] font-mono text-zinc-500">
                  {conversionResult?.evidence_event_id ? conversionResult.evidence_event_id.slice(0, 12) : 'Scan conversion captured'}
                </p>
              </Link>
              {generatedReport && (
                <Link href={`/reports/${generatedReport.id}`} className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 hover:border-emerald-500/40">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-4 w-4 text-emerald-400" />
                    <span className="text-xs font-bold text-zinc-200">Compliance Report</span>
                  </div>
                  <p className="text-[11px] font-mono text-emerald-300">{generatedReport.id}</p>
                </Link>
              )}
            </div>
          </Card>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card title="Detected Signals">
            <div className="space-y-3">
              {(scan.detected_signals_json || []).map((signal: any, index: number) => (
                <div key={`${signal.category}-${index}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <span className="text-xs font-bold text-zinc-200">{signal.label}</span>
                    <span className="text-[10px] font-mono uppercase text-zinc-500">{signal.category}</span>
                  </div>
                  <p className="text-xs text-zinc-500 leading-relaxed">{signal.excerpt}</p>
                  <a href={signal.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300">
                    Evidence source <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              ))}
            </div>
          </Card>

          <Card title="Gap Findings">
            <div className="space-y-3">
              {(scan.gap_findings_json || []).map((gap: any, index: number) => (
                <div key={`${gap.title}-${index}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                  <div className="flex items-center gap-2 mb-2">
                    {gap.severity === 'low' ? <CheckCircle2 className="h-4 w-4 text-emerald-400" /> : <AlertTriangle className="h-4 w-4 text-amber-400" />}
                    <span className="text-xs font-bold text-zinc-200">{gap.title}</span>
                  </div>
                  <p className="text-xs text-zinc-500 leading-relaxed">{gap.detail}</p>
                  {gap.article && (
                    <p className="mt-2 text-[10px] font-mono uppercase text-zinc-600">
                      {gap.article} | {gap.dimension_id}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card title="Suggested Actions">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(scan.suggested_actions_json || []).map((action: any, index: number) => (
              <div key={`${action.title}-${index}`} className="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="h-4 w-4 text-indigo-400" />
                  <span className="text-xs font-bold text-zinc-200">{action.title}</span>
                </div>
                <p className="text-xs text-zinc-500 leading-relaxed">{action.detail}</p>
                {action.article && (
                  <p className="mt-2 text-[10px] font-mono uppercase text-zinc-600">
                    {action.article} | {action.dimension_id}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card title="Crawled Public Pages">
          <div className="space-y-3">
            {(scan.source_pages_json || []).map((page: any) => (
              <a key={page.url} href={page.url} target="_blank" rel="noreferrer" className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-zinc-700">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-bold text-zinc-200">{page.title || page.url}</span>
                  <ExternalLink className="h-3.5 w-3.5 text-zinc-500" />
                </div>
                <p className="text-[11px] text-zinc-500 mt-1">{page.url}</p>
                <p className="text-xs text-zinc-600 mt-2 leading-relaxed">{page.text_excerpt}</p>
              </a>
            ))}
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
