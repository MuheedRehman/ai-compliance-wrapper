'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import EmptyState from '@/components/empty-state';
import ErrorState from '@/components/error-state';
import Card from '@/components/card';
import { Layers, Plus } from 'lucide-react';

export default function FeaturesPage() {
  const [features, setFeatures] = useState<any[]>([]);
  const [systems, setSystems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    feature_id: '',
    name: '',
    owner_email: '',
    ai_system_id: '',
  });

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([api.listFeatures(), api.listSystems().catch(() => [])])
      .then(([featureData, systemData]) => {
        setFeatures(featureData.features || []);
        setSystems(systemData || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createFeature({
        feature_id: formData.feature_id.trim(),
        name: formData.name.trim(),
        owner_email: formData.owner_email.trim() || undefined,
        ai_system_id: formData.ai_system_id || undefined,
        approved_models: ['gpt-4.1-nano'],
      });
      setFormData({ feature_id: '', name: '', owner_email: '', ai_system_id: '' });
      setShowCreate(false);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to create feature');
    } finally {
      setSubmitting(false);
    }
  }

  const highRiskCount = features.filter(f => f.risk_level_current?.toLowerCase() === 'high').length;
  const compliantCount = features.filter(f => f.compliance_status?.toLowerCase() === 'compliant').length;

  return (
    <PageShell 
      title="AI Features" 
      subtitle="Operational inventory of AI-enabled features across your organization."
      breadcrumbs={[{ label: 'Features' }]}
      actions={
        <button
          onClick={() => setShowCreate((current) => !current)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          {showCreate ? 'CANCEL' : 'CREATE FEATURE'}
        </button>
      }
    >
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : features.length === 0 ? (
        <div className="space-y-6">
          {showCreate && (
            <Card title="Create AI Feature">
              <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1fr_1fr_auto] gap-3">
                <input required value={formData.feature_id} onChange={(event) => setFormData({ ...formData, feature_id: event.target.value })} placeholder="feature_id" className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
                <input required value={formData.name} onChange={(event) => setFormData({ ...formData, name: event.target.value })} placeholder="Feature name" className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
                <input type="email" value={formData.owner_email} onChange={(event) => setFormData({ ...formData, owner_email: event.target.value })} placeholder="owner@company.com" className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
                <select value={formData.ai_system_id} onChange={(event) => setFormData({ ...formData, ai_system_id: event.target.value })} className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500">
                  <option value="">No linked system</option>
                  {systems.map((system) => <option key={system.id} value={system.id}>{system.name}</option>)}
                </select>
                <button disabled={submitting} className="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white disabled:opacity-50">{submitting ? 'Creating...' : 'Create'}</button>
              </form>
            </Card>
          )}
          <EmptyState
            title="No features mapped"
            message="Catalog your AI features to begin automated governance monitoring."
            icon={Layers}
          />
        </div>
      ) : (
        <div className="space-y-6">
          {showCreate && (
            <Card title="Create AI Feature">
              <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1fr_1fr_1fr_1fr_auto] gap-3">
                <input required value={formData.feature_id} onChange={(event) => setFormData({ ...formData, feature_id: event.target.value })} placeholder="feature_id" className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
                <input required value={formData.name} onChange={(event) => setFormData({ ...formData, name: event.target.value })} placeholder="Feature name" className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
                <input type="email" value={formData.owner_email} onChange={(event) => setFormData({ ...formData, owner_email: event.target.value })} placeholder="owner@company.com" className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500" />
                <select value={formData.ai_system_id} onChange={(event) => setFormData({ ...formData, ai_system_id: event.target.value })} className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500">
                  <option value="">No linked system</option>
                  {systems.map((system) => <option key={system.id} value={system.id}>{system.name}</option>)}
                </select>
                <button disabled={submitting} className="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white disabled:opacity-50">{submitting ? 'Creating...' : 'Create'}</button>
              </form>
            </Card>
          )}

          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card title="Total Features" variant="stat">
              <span className="text-3xl font-bold">{features.length}</span>
            </Card>
            <Card title="High Risk" variant="stat">
              <span className="text-3xl font-bold text-red-500">{highRiskCount}</span>
            </Card>
            <Card title="Compliant" variant="stat">
              <span className="text-3xl font-bold text-emerald-500">{compliantCount}</span>
            </Card>
          </div>

          <Card className="!p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Feature Specification</th>
                    <th>Associated System</th>
                    <th>Risk Profile</th>
                    <th>Compliance</th>
                    <th>Ownership</th>
                  </tr>
                </thead>
                <tbody>
                  {features.map((f: any) => (
                    <tr key={f.id}>
                      <td>
                        <div className="flex flex-col">
                          <Link href={`/features/${f.feature_id}`} className="text-sm font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                            {f.name}
                          </Link>
                          <span className="text-[10px] text-zinc-600 font-mono mt-0.5">{f.feature_id}</span>
                        </div>
                      </td>
                      <td>
                        {f.ai_system_id ? (
                          <Link href={`/systems/${f.ai_system_id}`} className="inline-flex items-center text-[10px] font-bold text-zinc-400 hover:text-zinc-200 transition-colors bg-zinc-900 px-2 py-1 rounded">
                            {f.ai_system_id.slice(0, 8).toUpperCase()}…
                          </Link>
                        ) : (
                          <span className="text-zinc-700">—</span>
                        )}
                      </td>
                      <td><StatusBadge value={f.risk_level_current} /></td>
                      <td><StatusBadge value={f.compliance_status} /></td>
                      <td className="text-[10px] text-zinc-500 font-medium italic">
                        {f.owner_email || 'Unassigned'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </PageShell>
  );
}
