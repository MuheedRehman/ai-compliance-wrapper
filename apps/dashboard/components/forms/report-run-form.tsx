'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { AlertCircle, CheckCircle2, Loader2, FileText } from 'lucide-react';

interface ReportRunFormProps {
  onSuccess: (report: any) => void;
}

export default function ReportRunForm({ onSuccess }: ReportRunFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systems, setSystems] = useState<any[]>([]);
  
  const [formData, setFormData] = useState({
    report_type: 'assessment_summary',
    title: '',
    ai_system_id: '',
  });

  useEffect(() => {
    api.listSystems().then(setSystems).catch(console.error);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.createReport(formData);
      onSuccess(res);
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-[13px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">
            Report Type
          </label>
          <select
            value={formData.report_type}
            onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
            className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
            required
          >
            <option value="assessment_summary">Assessment Summary</option>
            <option value="compliance_readiness_summary">Compliance Readiness</option>
            <option value="incident_summary">Incident Summary</option>
            <option value="test_session_summary">Test Session Summary</option>
          </select>
        </div>

        <div>
          <label className="block text-[13px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">
            AI System (Optional)
          </label>
          <select
            value={formData.ai_system_id}
            onChange={(e) => setFormData({ ...formData, ai_system_id: e.target.value })}
            className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
          >
            <option value="">All Systems / Generic</option>
            {systems.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[13px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">
            Custom Title (Optional)
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="e.g. Q3 Governance Review"
            className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Generating Report...
          </>
        ) : (
          <>
            <FileText className="h-5 w-5" />
            Generate Compliance Report
          </>
        )}
      </button>
    </form>
  );
}
