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
import { Cpu, Plus } from 'lucide-react';

interface AiSystem {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  deployment_status: string;
  registration_status: string;
  created_at: string;
  updated_at: string;
}

export default function SystemsPage() {
  const [systems, setSystems] = useState<AiSystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });

  const load = () => {
    setLoading(true);
    setError(null);
    api.listSystems()
      .then((data) => setSystems(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createSystem({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
      });
      setFormData({ name: '', description: '' });
      setShowCreate(false);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to register system');
    } finally {
      setSubmitting(false);
    }
  }

  const breadcrumbs = [{ label: 'AI Systems' }];

  const deployedCount = systems.filter(s => s.deployment_status.toLowerCase() === 'deployed').length;
  const registeredCount = systems.filter(s => s.registration_status.toLowerCase() === 'registered').length;

  return (
    <PageShell 
      title="AI Systems" 
      subtitle="Comprehensive inventory of AI systems within your governance scope."
      breadcrumbs={breadcrumbs}
      actions={
        <button
          onClick={() => setShowCreate((current) => !current)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          {showCreate ? 'CANCEL' : 'REGISTER SYSTEM'}
        </button>
      }
    >
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : systems.length === 0 ? (
        <div className="space-y-6">
          {showCreate && (
            <Card title="Register AI System">
              <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3">
                <input
                  required
                  value={formData.name}
                  onChange={(event) => setFormData({ ...formData, name: event.target.value })}
                  placeholder="System name"
                  className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                />
                <input
                  value={formData.description}
                  onChange={(event) => setFormData({ ...formData, description: event.target.value })}
                  placeholder="Short description"
                  className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                />
                <button disabled={submitting} className="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white disabled:opacity-50">
                  {submitting ? 'Creating...' : 'Create System'}
                </button>
              </form>
            </Card>
          )}
          <EmptyState
            title="No AI systems identified"
            message="Begin by registering your first AI system to initiate the compliance workflow."
            icon={Cpu}
          />
        </div>
      ) : (
        <div className="space-y-6">
          {showCreate && (
            <Card title="Register AI System">
              <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-[1fr_1fr_auto] gap-3">
                <input
                  required
                  value={formData.name}
                  onChange={(event) => setFormData({ ...formData, name: event.target.value })}
                  placeholder="System name"
                  className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                />
                <input
                  value={formData.description}
                  onChange={(event) => setFormData({ ...formData, description: event.target.value })}
                  placeholder="Short description"
                  className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
                />
                <button disabled={submitting} className="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white disabled:opacity-50">
                  {submitting ? 'Creating...' : 'Create System'}
                </button>
              </form>
            </Card>
          )}

          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card title="Total Systems" variant="stat">
              <span className="text-3xl font-bold">{systems.length}</span>
            </Card>
            <Card title="Deployed" variant="stat">
              <span className="text-3xl font-bold text-sky-400">{deployedCount}</span>
            </Card>
            <Card title="Registered" variant="stat">
              <span className="text-3xl font-bold text-emerald-400">{registeredCount}</span>
            </Card>
          </div>

          {/* Table Container */}
          <Card className="!p-0 overflow-hidden border-border bg-zinc-950">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>System Identity</th>
                    <th>Deployment</th>
                    <th>Registration</th>
                    <th>Audit Date</th>
                  </tr>
                </thead>
                <tbody>
                  {systems.map((s) => (
                    <tr key={s.id} className="group">
                      <td>
                        <div className="flex flex-col">
                          <Link href={`/systems/${s.id}`} className="text-sm font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
                            {s.name}
                          </Link>
                          {s.description && (
                            <span className="text-[10px] text-zinc-500 font-medium mt-0.5 truncate max-w-[240px]">
                              {s.description}
                            </span>
                          )}
                        </div>
                      </td>
                      <td><StatusBadge value={s.deployment_status} /></td>
                      <td><StatusBadge value={s.registration_status} /></td>
                      <td className="text-[10px] text-zinc-500 font-bold uppercase tracking-tighter">
                        {new Date(s.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
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
