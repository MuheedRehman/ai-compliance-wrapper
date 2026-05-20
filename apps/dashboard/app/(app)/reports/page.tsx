'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { 
  FileSearch, 
  Plus, 
  Calendar, 
  ShieldCheck, 
  AlertCircle,
  ChevronRight,
  FileText,
  Loader2,
  ExternalLink
} from 'lucide-react';
import ReportRunForm from '@/components/forms/report-run-form';

export default function ReportsPage() {
  const searchParams = useSearchParams();
  const systemFilter = searchParams.get('ai_system_id') || '';
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(searchParams.get('create') === '1');

  useEffect(() => {
    loadReports();
  }, []);

  async function loadReports() {
    setLoading(true);
    try {
      const data = await api.listReports();
      setReports(data);
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
      case 'pending': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      default: return 'text-zinc-400 bg-zinc-500/10 border-zinc-500/20';
    }
  };

  const getReadinessLabel = (report: any) => {
    const status = report.report_json?.readiness_summary?.status;
    return status ? status.replace(/_/g, ' ').toUpperCase() : 'NOT SCORED';
  };
  const visibleReports = systemFilter ? reports.filter((report) => report.ai_system_id === systemFilter) : reports;

  return (
    <div className="max-w-[1200px] mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-indigo-600/10 rounded-lg">
              <FileSearch className="h-6 w-6 text-indigo-400" />
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Governance Reports</h1>
          </div>
          <p className="text-zinc-400 text-sm max-w-2xl">
            Generate and manage EU AI Act compliance assessments, readiness summaries, and incident audits.
          </p>
        </div>
        
        {!isCreating && (
          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-lg shadow-indigo-600/20"
          >
            <Plus className="h-4 w-4" />
            New Report
          </button>
        )}
      </div>

      {isCreating && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 backdrop-blur-sm animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">Generate Assessment Report</h2>
            <button 
              onClick={() => setIsCreating(false)}
              className="text-zinc-500 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
          <ReportRunForm onSuccess={(r) => {
            setReports([r, ...reports]);
            setIsCreating(false);
          }} initialSystemId={systemFilter} initialReportType={systemFilter ? 'compliance_readiness_summary' : 'assessment_summary'} />
        </div>
      )}

      {/* Main List */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <p className="text-zinc-500 font-medium">Assembling reports...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center bg-red-500/5 border border-red-500/10 rounded-2xl">
            <AlertCircle className="h-10 w-10 text-red-500 mx-auto mb-4" />
            <h3 className="text-white font-bold mb-2">Service Error</h3>
            <p className="text-zinc-400 text-sm">{error}</p>
          </div>
        ) : visibleReports.length === 0 ? (
          <div className="p-24 text-center bg-zinc-900/30 border border-dashed border-zinc-800 rounded-3xl">
            <div className="h-16 w-16 bg-zinc-800/50 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <FileSearch className="h-8 w-8 text-zinc-600" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">No Reports Yet</h3>
            <p className="text-zinc-500 text-sm max-w-md mx-auto mb-8">
              Generate your first compliance assessment to see readiness summaries and findings here.
            </p>
            {!isCreating && (
              <button
                onClick={() => setIsCreating(true)}
                className="inline-flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white px-6 py-2.5 rounded-xl font-bold transition-all"
              >
                Start Assessment
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {visibleReports.map((report) => (
              <Link 
                key={report.id}
                href={`/reports/${report.id}`}
                className="group bg-zinc-900/40 hover:bg-zinc-900/60 border border-zinc-800/60 hover:border-indigo-500/30 rounded-2xl p-5 transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${getStatusColor(report.status)}`}>
                    {report.status}
                  </div>
                  <div className="text-[11px] font-medium text-zinc-500 flex items-center gap-1.5">
                    <Calendar className="h-3 w-3" />
                    {new Date(report.created_at).toLocaleDateString()}
                  </div>
                </div>

                <h3 className="text-[15px] font-bold text-white group-hover:text-indigo-400 transition-colors mb-1 line-clamp-1">
                  {report.title}
                </h3>
                <p className="text-zinc-500 text-[11px] font-medium uppercase tracking-widest mb-4">
                  {report.report_type.replace('_', ' ')}
                </p>

                <div className="pt-4 border-t border-zinc-800/40 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[12px] font-medium text-zinc-400">
                    <ShieldCheck className="h-3.5 w-3.5 text-indigo-500/70" />
                    {getReadinessLabel(report)}
                  </div>
                  <ChevronRight className="h-4 w-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
