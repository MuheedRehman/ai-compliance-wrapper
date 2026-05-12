'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import { AlertCircle, Calendar, ChevronLeft, Save, Trash2, MessageSquare } from 'lucide-react';

export default function IncidentDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [incident, setIncident] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getIncident(id as string)
      .then(setIncident)
      .catch(() => router.push('/incidents'))
      .finally(() => setLoading(false));
  }, [id, router]);

  const handleUpdate = async (status: string) => {
    setSaving(true);
    try {
      const updated = await api.updateIncident(id as string, { ...incident, status });
      setIncident(updated);
    } catch (err) {
      alert("Update failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this incident record?")) return;
    try {
      await api.deleteIncident(id as string);
      router.push('/incidents');
    } catch (err) {
      alert("Delete failed.");
    }
  };

  if (loading) return <PageShell title="Incident Detail" subtitle="Loading..."><Loading /></PageShell>;
  if (!incident) return null;

  return (
    <PageShell 
      title={`Incident: ${incident.id}`} 
      subtitle={`Malfunction report for ${incident.ai_system_id}`}
    >
      <div className="space-y-6 animate-fade-in">
        <button 
          onClick={() => router.back()}
          className="flex items-center gap-2 text-xs font-bold text-zinc-500 hover:text-zinc-300 transition-colors uppercase tracking-wider mb-2"
        >
          <ChevronLeft className="h-3 w-3" /> Back to List
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card title="Incident Description">
              <div className="p-4 bg-zinc-900/40 rounded-xl border border-zinc-800/60 min-h-[200px]">
                <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">{incident.description}</p>
              </div>
            </Card>

            <div className="flex gap-4">
               <Card className="flex-1" title="Resolution Notes" subtitle="Internal audit tracking.">
                  <div className="flex flex-col items-center justify-center py-8 text-zinc-600 border border-zinc-800/60 border-dashed rounded-lg">
                    <MessageSquare className="h-5 w-5 mb-2" />
                    <span className="text-[10px] font-bold uppercase tracking-wider">No resolution notes yet</span>
                  </div>
               </Card>
            </div>
          </div>

          <div className="space-y-6">
            <Card title="Incident Status">
              <div className="space-y-5">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Severity</span>
                  <StatusBadge value={incident.severity} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Status</span>
                  <StatusBadge value={incident.status} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Reported</span>
                  <span className="text-xs text-zinc-400 font-medium flex items-center gap-2">
                    <Calendar className="h-3 w-3 text-zinc-600" />
                    {new Date(incident.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="mt-8 space-y-2">
                <button 
                  onClick={() => handleUpdate('investigating')}
                  disabled={saving || incident.status === 'investigating'}
                  className="w-full py-2 bg-zinc-800 text-white rounded-lg text-sm font-bold hover:bg-zinc-700 transition-colors disabled:opacity-50"
                >
                  Mark as Investigating
                </button>
                <button 
                  onClick={() => handleUpdate('resolved')}
                  disabled={saving || incident.status === 'resolved'}
                  className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Mark as Resolved'}
                </button>
                <div className="pt-2 border-t border-zinc-800/60 mt-4">
                  <button 
                    onClick={handleDelete}
                    className="w-full py-2 bg-transparent text-zinc-500 rounded-lg text-sm font-bold hover:text-red-400 hover:bg-red-400/5 transition-all flex items-center justify-center gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Archive Record
                  </button>
                </div>
              </div>
            </Card>

            <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/10 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold text-white mb-1">Evidence Domain</p>
                <p className="text-[10px] text-zinc-500 leading-relaxed font-medium font-mono">governance_incident</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
