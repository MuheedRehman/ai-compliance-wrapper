'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import Loading from '@/components/loading';
import { ShieldCheck, Plus, UserPlus, Mail, Trash2, AlertCircle, Info } from 'lucide-react';

export default function OversightPage() {
  const searchParams = useSearchParams();
  const systemFilter = searchParams.get('ai_system_id') || '';
  const [assignments, setAssignments] = useState<any[]>([]);
  const [systems, setSystems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(searchParams.get('create') === '1');
  
  // Form State
  const [formData, setFormData] = useState({
    ai_system_id: systemFilter,
    reviewer_email: '',
    role: 'technical_oversight'
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.listOversight(),
      api.listSystems()
    ]).then(([ovs, sys]) => {
      setAssignments(ovs);
      setSystems(sys);
    }).catch(err => {
      if (err instanceof ApiError && err.status === 403) {
        setError("Human Oversight management is not enabled for your current plan.");
      } else {
        setError("Failed to load oversight assignments.");
      }
    }).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const newOvs = await api.createOversight(formData);
      setAssignments([...assignments, newOvs]);
      setShowAdd(false);
      setFormData({ ai_system_id: systemFilter, reviewer_email: '', role: 'technical_oversight' });
    } catch (err) {
      alert("Failed to create assignment.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this assignment?")) return;
    try {
      await api.deleteOversight(id);
      setAssignments(assignments.filter(a => a.id !== id));
    } catch (err) {
      alert("Failed to delete.");
    }
  };

  if (loading) return <PageShell title="Human Oversight" subtitle="Manage Article 14 oversight roles for AI systems."><Loading /></PageShell>;

  if (error) {
    return (
      <PageShell title="Human Oversight" subtitle="Manage Article 14 oversight roles for AI systems.">
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
  const visibleAssignments = systemFilter ? assignments.filter((assignment) => assignment.ai_system_id === systemFilter) : assignments;

  return (
    <PageShell 
      title="Human Oversight" 
      subtitle="Manage Article 14 oversight roles for AI systems."
      actions={
        <button 
          onClick={() => setShowAdd(!showAdd)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/20"
        >
          {showAdd ? 'Cancel' : <><Plus className="h-4 w-4" /> Add Oversight</>}
        </button>
      }
    >
      <div className="space-y-6">
        {showAdd && (
          <Card title="Assign Oversight Role" className="animate-in fade-in slide-in-from-top-2">
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">AI System</label>
                  <select 
                    required
                    value={formData.ai_system_id}
                    onChange={e => setFormData({...formData, ai_system_id: e.target.value})}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:border-indigo-500 outline-none transition-colors"
                  >
                    <option value="">Select a system...</option>
                    {systems.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Reviewer Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-4 w-4 text-zinc-600" />
                    <input 
                      type="email"
                      required
                      placeholder="reviewer@company.com"
                      value={formData.reviewer_email}
                      onChange={e => setFormData({...formData, reviewer_email: e.target.value})}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-9 pr-3 py-2 text-sm text-white focus:border-indigo-500 outline-none transition-colors placeholder:text-zinc-700"
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider">Role Type</label>
                  <select 
                    value={formData.role}
                    onChange={e => setFormData({...formData, role: e.target.value})}
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white focus:border-indigo-500 outline-none transition-colors"
                  >
                    <option value="technical_oversight">Technical Oversight</option>
                    <option value="legal_oversight">Legal Oversight</option>
                    <option value="ethical_oversight">Ethical Oversight</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end pt-2">
                <button 
                  disabled={submitting}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Create Assignment'}
                </button>
              </div>
            </form>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {visibleAssignments.length === 0 ? (
            <div className="col-span-full py-20 text-center bg-zinc-900/30 rounded-xl border border-zinc-800/60 border-dashed">
              <UserPlus className="h-10 w-10 text-zinc-700 mx-auto mb-4" />
              <h3 className="text-zinc-400 font-medium">No oversight roles assigned yet.</h3>
              <p className="text-zinc-600 text-sm mt-1">High-risk systems require human oversight under Article 14.</p>
            </div>
          ) : (
            visibleAssignments.map((ovs) => (
              <Card key={ovs.id} className="relative group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                      <ShieldCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white tracking-tight">{ovs.reviewer_email}</h4>
                      <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider mt-0.5">{ovs.role.replace('_', ' ')}</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDelete(ovs.id)}
                    className="p-1.5 rounded-md text-zinc-700 hover:text-red-400 hover:bg-red-400/10 transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
                <div className="mt-6 pt-4 border-t border-zinc-800/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    <span className="text-[10px] font-bold text-zinc-400">System: {systems.find(s => s.id === ovs.ai_system_id)?.name || ovs.ai_system_id}</span>
                  </div>
                  <span className="text-[10px] text-zinc-600 font-medium">{new Date(ovs.created_at).toLocaleDateString()}</span>
                </div>
              </Card>
            ))
          )}
        </div>

        <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-xl p-4 flex gap-4 items-start">
          <div className="p-2 rounded-lg bg-indigo-500/10">
            <Info className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="text-xs text-zinc-500 leading-relaxed">
            <p className="font-bold text-indigo-300/80 mb-1">Regulatory Context: Article 14</p>
            High-risk AI systems shall be designed and developed in such a way that they can be effectively overseen by natural persons during the period they are in use.
          </div>
        </div>
      </div>
    </PageShell>
  );
}
