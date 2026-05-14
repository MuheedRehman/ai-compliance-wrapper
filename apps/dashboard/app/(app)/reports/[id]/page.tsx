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
      const blob = new Blob([result.content], { type: result.contentType });
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
  const readinessSummary = data.readiness_summary || {};
  const readinessStatus = readinessSummary.status || report.status || 'unknown';
  const reportTypeLabel = String(report.report_type || 'report').replace(/_/g, ' ');
  const executiveSummary = data.executive_summary || 'This report was generated, but no executive summary was recorded.';
  const readinessRationale = readinessSummary.rationale || 'No generation rationale was recorded for this report.';

  return (
    <div className="max-w-[1000px] mx-auto space-y-8 pb-24">
      {/* Navigation & Actions */}
      <div className="flex items-center justify-between">
        <Link href="/reports" className="text-zinc-500 hover:text-white flex items-center gap-2 text-sm font-medium transition-colors">
          <ArrowLeft className="h-4 w-4" /> Back to Reports
        </Link>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => saveArtifact('report.json')}
            className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-4 py-2 rounded-xl text-sm font-bold transition-all"
          >
            <Download className="h-4 w-4" /> JSON
          </button>
          <button
            onClick={() => saveArtifact('report.md')}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Download className="h-4 w-4" /> Markdown
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
                </div>
              ))}
              {findings.length === 0 && (
                <div className="p-8 text-center bg-zinc-900/10 border border-dashed border-zinc-800 rounded-xl text-zinc-500 text-sm italic">
                  No issues identified in current scope.
                </div>
              )}
            </div>
          </section>

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
