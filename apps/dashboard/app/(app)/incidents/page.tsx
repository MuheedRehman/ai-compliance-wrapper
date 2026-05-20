'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import { AlertCircle, Plus, ArrowRight, MessageSquare, History } from 'lucide-react';

export default function IncidentsPage() {
  const searchParams = useSearchParams();
  const systemFilter = searchParams.get('ai_system_id') || '';
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(searchParams.get('create') === '1');
  const [systems, setSystems] = useState<any[]>([]);
  
  // Form State
  const [formData, setFormData] = useState({
    ai_system_id: systemFilter,
    severity: 'medium',
    description: '',
    status: 'open'
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.listIncidents(),
      api.listSystems()
    ]).then(([inc, sys]) => {
      setIncidents(inc);
      setSystems(sys);
    }).catch(err => {
      if (err instanceof ApiError && err.status === 403) {
        setError("Incident management is not enabled for your current plan.");
      } else {
        setError("Failed to load incident records.");
      }
    }).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const newInc = await api.createIncident(formData);
      setIncidents([newInc, ...incidents]);
      setShowAdd(false);
      setFormData({ ai_system_id: systemFilter, severity: 'medium', description: '', status: 'open' });
    } catch (err) {
      alert("Failed to create incident.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <PageShell title="Incident Management" subtitle="Track and respond to AI-related incidents and malfunctions."><Loading /></PageShell>;

  if (error) {
    return (
      <PageShell title="Incident Management" subtitle="Track and respond to AI-related incidents and malfunctions.">
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-3 rounded-full bg-red-500/10 mb-4">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Access Restricted</h3>
            <p className="text-zinc-400 max-w-md">{error}</p>
          </div>
        </Card>
      </PageShell>
    );
  }
  const visibleIncidents = systemFilter ? incidents.filter((incident) => incident.ai_system_id === systemFilter) : incidents;

  return (
    <PageShell 
      title="Incident Management" 
      subtitle="Track and respond to AI-related incidents and malfunctions."
      actions={
        <button 
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-500 transition-all shadow-lg shadow-red-600/20"
        >
          {showAdd ? 'Cancel' : <><Plus className="h-4 w-4" /> Report Incident</>}
        </button>
      }
    >
      <div className="space-y-6">
        {showAdd && (
          <Card title="New Incident Report" className="border-red-500/20 animate-in fade-in slide-in-from-top-2">
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Affected AI System</label>
                  <select 
                    required
                    value={formData.ai_system_id}
                    onChange={e => setFormData({...formData, ai_system_id: e.target.value})}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:border-red-500 outline-none transition-colors"
                  >
                    <option value="">Select a system...</option>
                    {systems.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Severity Level</label>
                  <select 
                    value={formData.severity}
                    onChange={e => setFormData({...formData, severity: e.target.value})}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:border-red-500 outline-none transition-colors"
                  >
                    <option value="low">Low - Minor Malfunction</option>
                    <option value="medium">Medium - Operational Impact</option>
                    <option value="high">High - Serious Incident (Article 62)</option>
                  </select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Description of Incident</label>
                <textarea 
                  required
                  rows={4}
                  placeholder="Describe the malfunction, unexpected behavior, or serious incident..."
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:border-red-500 outline-none transition-colors placeholder:text-zinc-700 resize-none"
                />
              </div>
              <div className="flex justify-end pt-2">
                <button 
                  disabled={submitting}
                  className="px-6 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-500 transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Report'}
                </button>
              </div>
            </form>
          </Card>
        )}

        <div className="grid grid-cols-1 gap-4">
          {visibleIncidents.length === 0 ? (
            <Card>
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="p-4 rounded-full bg-zinc-900 mb-6">
                  <History className="h-8 w-8 text-zinc-600" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">No incidents recorded</h3>
                <p className="text-zinc-500 max-w-sm mx-auto leading-relaxed">
                  Incidents involving AI systems must be documented and, in some cases, reported to market surveillance authorities under Article 62.
                </p>
              </div>
            </Card>
          ) : (
            visibleIncidents.map((inc) => (
              <Link key={inc.id} href={`/incidents/${inc.id}`}>
                <Card className="hover:border-zinc-700 transition-all group border-l-4 border-l-red-500/30">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4 min-w-0">
                      <div className="p-2.5 rounded-lg bg-red-500/10 text-red-400 shrink-0 border border-red-500/20">
                        <AlertCircle className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-bold text-white tracking-tight truncate">{inc.id}</h4>
                          <StatusBadge value={inc.severity} />
                          <StatusBadge value={inc.status} />
                        </div>
                        <p className="text-sm text-zinc-400 line-clamp-1">{inc.description}</p>
                        <div className="flex items-center gap-3 mt-3">
                          <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">System: {systems.find(s => s.id === inc.ai_system_id)?.name || inc.ai_system_id}</span>
                          <span className="h-1 w-1 rounded-full bg-zinc-800" />
                          <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">{new Date(inc.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-zinc-700 group-hover:text-zinc-400 transition-colors shrink-0 mt-1" />
                  </div>
                </Card>
              </Link>
            ))
          )}
        </div>
      </div>
    </PageShell>
  );
}
