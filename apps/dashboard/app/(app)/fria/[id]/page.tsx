'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import { ShieldCheck, Calendar, ChevronLeft, Save, Trash2, Database } from 'lucide-react';

export default function FriaDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const [fria, setFria] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getFria(id as string)
      .then(setFria)
      .catch(() => router.push('/fria'))
      .finally(() => setLoading(false));
  }, [id, router]);

  const handleUpdate = async (status: string) => {
    setSaving(true);
    try {
      const updated = await api.updateFria(id as string, { ...fria, status });
      setFria(updated);
    } catch (err) {
      alert("Update failed.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this FRIA?")) return;
    try {
      await api.deleteFria(id as string);
      router.push('/fria');
    } catch (err) {
      alert("Delete failed.");
    }
  };

  if (loading) return <PageShell title="FRIA Detail" subtitle="Loading..."><Loading /></PageShell>;
  if (!fria) return null;

  return (
    <PageShell 
      title={`FRIA: ${fria.id}`} 
      subtitle={`Fundamental Rights Impact Assessment for ${fria.ai_system_id}`}
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
            <Card title="Assessment Data">
              <div className="bg-zinc-950/50 rounded-xl border border-zinc-800/60 p-4 font-mono text-xs text-zinc-400 overflow-auto max-h-[600px]">
                <pre>{JSON.stringify(fria.assessment_json, null, 2)}</pre>
              </div>
            </Card>
          </div>

          <div className="space-y-6">
            <Card title="Assessment Metadata">
              <div className="space-y-5">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Status</span>
                  <StatusBadge value={fria.status} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">System</span>
                  <span className="text-xs text-white font-medium flex items-center gap-2">
                    <Database className="h-3 w-3 text-indigo-400" />
                    {fria.ai_system_id}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Created</span>
                  <span className="text-xs text-zinc-400 font-medium flex items-center gap-2">
                    <Calendar className="h-3 w-3 text-zinc-600" />
                    {new Date(fria.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="mt-8 space-y-2">
                <button 
                  onClick={() => handleUpdate('completed')}
                  disabled={saving || fria.status === 'completed'}
                  className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Mark as Completed'}
                </button>
                <button 
                  onClick={handleDelete}
                  className="w-full py-2 bg-transparent text-zinc-500 rounded-lg text-sm font-bold hover:text-red-400 hover:bg-red-400/5 transition-all flex items-center justify-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Assessment
                </button>
              </div>
            </Card>

            <div className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/60 flex items-start gap-3">
              <ShieldCheck className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold text-white mb-1">Evidence Domain</p>
                <p className="text-[10px] text-zinc-500 leading-relaxed font-medium font-mono">governance_fria</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
