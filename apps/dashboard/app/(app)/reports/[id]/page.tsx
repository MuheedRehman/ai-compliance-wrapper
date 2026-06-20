'use client';

import { useCallback, useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { 
  ArrowLeft, 
  Download, 
  ShieldCheck, 
  AlertCircle, 
  FileText, 
  History,
  Link as LinkIcon,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Info
} from 'lucide-react';
import Link from 'next/link';

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadReport = useCallback(async () => {
    try {
      const data = await api.getReport(id);
      setReport(data);
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  async function saveArtifact(artifact: string) {
    try {
      const result = await api.downloadArtifact(id, artifact);
      const blob = new Blob([result.content as any], { type: result.contentType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = artifact;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.body?.detail || err.body?.error?.message || `Failed to download ${artifact}`);
    }
  }

  async function saveBundle() {
    try {
      const result = await api.downloadBundle(id);
      const blob = new Blob([result.content], { type: result.contentType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${id}-bundle.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.body?.detail || err.body?.error?.message || 'Failed to download bundle');
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-4">
        <div className="h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-zinc-500 font-medium">Assembling compliance findings...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-12 text-center">
        <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Report Error</h2>
        <p className="text-zinc-400 mb-8">{error || 'Report not found'}</p>
        <Link href="/reports" className="text-indigo-400 hover:text-indigo-300 font-bold flex items-center justify-center gap-2">
          <ArrowLeft className="h-4 w-4" /> Back to Reports
        </Link>
      </div>
    );
  }

  const data = report.report_json || {};
  const sources = Array.isArray(report.source_refs_json) ? report.source_refs_json : [];
  const findings = Array.isArray(data.findings) ? data.findings : [];
  const remediationActions = Array.isArray(data.remediation_actions) ? data.remediation_actions : [];
  const evidenceReferences = Array.isArray(data.evidence_references) ? data.evidence_references : [];
  const penaltyExposures = Array.isArray(data.penalty_exposures) ? data.penalty_exposures : [];
  const scannerAuditPack = data.scanner_audit_pack || null;
  const scannerSummary = scannerAuditPack?.summary || {};
  const scannerFoundTopics = Array.isArray(scannerAuditPack?.found_topics) ? scannerAuditPack.found_topics : [];
  const scannerMissingTopics = Array.isArray(scannerAuditPack?.missing_topics) ? scannerAuditPack.missing_topics : [];
  const scannerSources = Array.isArray(scannerAuditPack?.public_sources) ? scannerAuditPack.public_sources : [];
  const readinessSummary = data.readiness_summary || {};
  const readinessStatus = readinessSummary.status || report.status || 'unknown';
  const reportTypeLabel = String(report.report_type || 'report').replace(/_/g, ' ');
  const executiveSummary = data.executive_summary || 'This report was generated, but no executive summary was recorded.';
  const readinessRationale = readinessSummary.rationale || 'No generation rationale was recorded for this report.';
  const penaltyText = (penalty: any) => penalty?.maximum_text || penalty?.notes || '';

  return (
    <div className="max-w-[1000px] mx-auto space-y-8 pb-24">
      {/* Navigation & Actions */}
      <div className="flex items-center justify-between">
        <Link href="/reports" className="text-zinc-500 hover:text-white flex items-center gap-2 text-sm font-medium transition-colors">
          <ArrowLeft className="h-4 w-4" /> Back to Reports
        </Link>
        
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <button
            onClick={() => saveArtifact('report.json')}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-3 py-2 rounded-xl text-sm font-bold transition-all"
          >
            <Download className="h-4 w-4" /> JSON
          </button>
          <button
            onClick={() => saveArtifact('report.md')}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-3 py-2 rounded-xl text-sm font-bold transition-all"
          >
            <Download className="h-4 w-4" /> Markdown
          </button>
          <button
            onClick={() => saveArtifact('report.pdf')}
            className="flex items-center gap-2 bg-red-700 hover:bg-red-600 text-white px-3 py-2 rounded-xl text-sm font-bold transition-all"
          >
            <Download className="h-4 w-4" /> PDF
          </button>
          <button
            onClick={saveBundle}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-2 rounded-xl text-sm font-bold shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Download className="h-4 w-4" /> Bundle
          </button>
        </div>
      </div>

      {/* Header */}
      <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-8">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <span className="bg-indigo-500/10 text-indigo-400 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-md border border-indigo-500/20">
                {reportTypeLabel}
              </span>
              <span className="text-zinc-600 font-bold">•</span>
              <span className="text-zinc-500 text-[12px] font-medium uppercase tracking-wider">
                Generated {new Date(report.created_at).toLocaleString()}
              </span>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight mb-4">{report.title}</h1>
            <p className="text-zinc-400 text-[15px] leading-relaxed max-w-2xl italic">
              &ldquo;{executiveSummary}&rdquo;
            </p>
          </div>

          <div className={`shrink-0 p-6 rounded-2xl border flex flex-col items-center gap-2 min-w-[180px]
            ${readinessStatus === 'ready'
              ? 'bg-emerald-500/5 border-emerald-500/20' 
              : 'bg-amber-500/5 border-amber-500/20'}`}>
            <ShieldCheck className={`h-8 w-8 ${readinessStatus === 'ready' ? 'text-emerald-400' : 'text-amber-400'}`} />
            <div className="text-center">
              <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1">Status</div>
              <div className={`text-lg font-bold uppercase tracking-tight ${readinessStatus === 'ready' ? 'text-emerald-400' : 'text-amber-400'}`}>
                {readinessStatus.replace(/_/g, ' ')}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Findings */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Key Findings</h2>
              <div className="px-2 py-0.5 bg-zinc-800 rounded text-[10px] font-bold text-zinc-400">
                {findings.length}
              </div>
            </div>
            
            <div className="space-y-4">
              {findings.map((f: any, i: number) => (
                <div key={i} className="bg-zinc-900/20 border border-zinc-800/60 rounded-xl p-5">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-bold text-white text-[15px]">{f.title}</h3>
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border
                      ${f.severity === 'high' ? 'text-red-400 bg-red-400/10 border-red-400/20' : 
                        f.severity === 'medium' ? 'text-amber-400 bg-amber-400/10 border-amber-400/20' : 
                        'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'}`}>
                      {f.severity}
                    </span>
                  </div>
                  <p className="text-zinc-400 text-sm leading-relaxed">{f.description}</p>
                  {f.penalty_exposure && (
                    <div className="mt-3 rounded border border-red-500/20 bg-red-500/5 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-red-300">Possible Fine Exposure</p>
                      <p className="mt-1 text-xs text-zinc-400">{penaltyText(f.penalty_exposure)}</p>
                    </div>
                  )}
                </div>
              ))}
              {findings.length === 0 && (
                <div className="p-8 text-center bg-zinc-900/10 border border-dashed border-zinc-800 rounded-xl text-zinc-500 text-sm italic">
                  No issues identified in current scope.
                </div>
              )}
            </div>
          </section>

          {scannerAuditPack && (
            <section className="space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <h2 className="text-lg font-bold text-white tracking-tight">Scanner Audit Pack</h2>
                <div className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 rounded text-[10px] font-bold text-indigo-300">
                  {scannerSummary.average_public_evidence_coverage || 0}% coverage
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Scans</p>
                  <p className="mt-2 text-2xl font-bold text-white">{scannerSummary.scan_count || 0}</p>
                </div>
                <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Found Topics</p>
                  <p className="mt-2 text-2xl font-bold text-emerald-400">{scannerSummary.found_topic_count || 0}</p>
                </div>
                <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Missing Topics</p>
                  <p className="mt-2 text-2xl font-bold text-amber-400">{scannerSummary.missing_topic_count || 0}</p>
                </div>
                <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-600">Priority Gaps</p>
                  <p className="mt-2 text-2xl font-bold text-red-300">{scannerSummary.high_or_medium_gap_count || 0}</p>
                </div>
              </div>

              {scannerFoundTopics.length > 0 && (
                <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/20 p-5">
                  <h3 className="mb-4 text-sm font-bold text-white">Public Evidence Found</h3>
                  <div className="space-y-3">
                    {scannerFoundTopics.slice(0, 6).map((topic: any, i: number) => (
                      <div key={`${topic.scan_id}-${topic.topic}-${i}`} className="rounded-lg border border-zinc-800/60 bg-black/20 p-3">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="text-xs font-bold text-zinc-200">{topic.label}</p>
                            <p className="mt-1 text-[11px] font-mono uppercase text-zinc-600">{topic.article} | {topic.dimension_id}</p>
                          </div>
                          {topic.source_url && (
                            <a href={topic.source_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[10px] font-bold uppercase text-indigo-400 hover:text-indigo-300">
                              Source <ExternalLink className="h-3 w-3" />
                            </a>
                          )}
                        </div>
                        <p className="mt-2 text-xs leading-relaxed text-zinc-500">{topic.excerpt}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {scannerMissingTopics.length > 0 && (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
                  <h3 className="mb-3 text-sm font-bold text-amber-200">Missing Public Evidence Topics</h3>
                  <div className="flex flex-wrap gap-2">
                    {scannerMissingTopics.map((topic: string) => (
                      <span key={topic} className="rounded bg-black/20 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-amber-300 ring-1 ring-amber-500/20">
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {scannerSources.length > 0 && (
                <div className="rounded-xl border border-zinc-800/60 bg-zinc-900/20 p-5">
                  <h3 className="mb-4 text-sm font-bold text-white">Public Source Excerpts</h3>
                  <div className="space-y-3">
                    {scannerSources.slice(0, 5).map((source: any, i: number) => (
                      <a key={`${source.scan_id}-${source.url}-${i}`} href={source.url} target="_blank" rel="noreferrer" className="block rounded-lg border border-zinc-800/60 bg-black/20 p-3 hover:border-zinc-700">
                        <div className="flex items-center justify-between gap-3">
                          <p className="truncate text-xs font-bold text-zinc-200">{source.title || source.url}</p>
                          <ExternalLink className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
                        </div>
                        <p className="mt-1 truncate text-[11px] text-zinc-600">{source.url}</p>
                        <p className="mt-2 text-xs leading-relaxed text-zinc-500">{source.text_excerpt}</p>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Remediation */}
          <section className="space-y-4">
            <h2 className="text-lg font-bold text-white tracking-tight">Required Actions</h2>
            <div className="space-y-3">
              {remediationActions.map((a: any, i: number) => (
                <div key={i} className="flex gap-4 p-4 bg-zinc-900/40 border border-zinc-800/40 rounded-xl items-start">
                  <div className="mt-1 h-2 w-2 rounded-full bg-indigo-500 shrink-0 shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
                  <div>
                    <h4 className="text-white font-bold text-sm mb-1">{a.title}</h4>
                    <p className="text-zinc-400 text-[13px] leading-relaxed">{a.description}</p>
                    {a.penalty_exposure && (
                      <p className="mt-2 text-[11px] leading-relaxed text-red-300">
                        Possible fine exposure: {penaltyText(a.penalty_exposure)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {remediationActions.length === 0 && (
                <div className="flex items-center gap-3 p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
                  <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
                  <p className="text-emerald-400/70 text-sm font-medium">Compliance posture is currently stable.</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Sidebar Context */}
        <div className="space-y-8">
          <section className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6">
            <h3 className="text-[13px] font-bold text-red-300 uppercase tracking-widest mb-6 flex items-center gap-2">
              <AlertCircle className="h-3.5 w-3.5" /> Fine Exposure
            </h3>
            <div className="space-y-4">
              {penaltyExposures.map((penalty: any) => (
                <div key={penalty.band_id} className="rounded-xl border border-red-500/10 bg-black/20 p-3">
                  <div className="text-[10px] font-bold text-red-300 uppercase tracking-tight">{penalty.enforcement_article}</div>
                  <div className="mt-1 text-[13px] font-bold text-zinc-200">{penalty.title}</div>
                  <p className="mt-2 text-[12px] leading-relaxed text-zinc-500">{penaltyText(penalty)}</p>
                </div>
              ))}
              {penaltyExposures.length === 0 && (
                <div className="text-zinc-600 text-[12px] italic">No fine exposure band recorded.</div>
              )}
            </div>
          </section>

          {/* Source Linkage */}
          <section className="bg-zinc-900/60 border border-zinc-800/60 rounded-2xl p-6">
            <h3 className="text-[13px] font-bold text-zinc-500 uppercase tracking-widest mb-6 flex items-center gap-2">
              <LinkIcon className="h-3.5 w-3.5" /> Source Traceability
            </h3>
            <div className="space-y-4">
              {sources.map((src: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-black/20 rounded-xl border border-zinc-800/40">
                  <div>
                    <div className="text-[10px] font-bold text-zinc-600 uppercase tracking-tight">{src.type}</div>
                    <div className="text-[13px] font-medium text-zinc-300 truncate max-w-[120px]">{src.name || src.id}</div>
                  </div>
                  <ChevronRight className="h-3.5 w-3.5 text-zinc-700" />
                </div>
              ))}
              {sources.length === 0 && (
                <div className="text-zinc-600 text-[12px] italic">No formal source linkage.</div>
              )}
            </div>
          </section>

          {/* Evidence Trail */}
          <section className="bg-zinc-900/60 border border-zinc-800/60 rounded-2xl p-6">
            <h3 className="text-[13px] font-bold text-zinc-500 uppercase tracking-widest mb-6 flex items-center gap-2">
              <History className="h-3.5 w-3.5" /> Evidence Trail
            </h3>
            <div className="space-y-2">
              {evidenceReferences.slice(0, 5).map((e: any, i: number) => (
                <div key={i} className="text-[11px] font-mono text-zinc-500 hover:text-zinc-300 transition-colors cursor-default truncate">
                  <span className="text-zinc-700 mr-2">{i+1}.</span> {e.id}
                </div>
              ))}
              <div className="pt-4 flex items-center justify-between">
                <span className="text-[11px] font-bold text-zinc-600">{evidenceReferences.length} Total Logs</span>
                <Link href="/evidence" className="text-[11px] font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                  View Full <ExternalLink className="h-2.5 w-2.5" />
                </Link>
              </div>
            </div>
          </section>

          {/* Rationale */}
          <section className="p-6 bg-indigo-500/5 border border-indigo-500/10 rounded-2xl">
            <div className="flex items-center gap-2 mb-3">
              <Info className="h-4 w-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-white">Generation Rationale</h3>
            </div>
            <p className="text-[13px] text-zinc-400 leading-relaxed italic">
              {readinessRationale}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
