'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';
import Card from '@/components/card';
import Loading from '@/components/loading';
import ErrorState from '@/components/error-state';
import Link from 'next/link';
import { Layers, Calendar, Activity, Info, ChevronLeft } from 'lucide-react';

export default function SystemDetailPage() {
  const params = useParams();
  const systemId = params.id as string;

  const [system, setSystem] = useState<any>(null);
  const [features, setFeatures] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getSystem(systemId),
      api.listFeatures(),
    ])
      .then(([sys, featData]) => {
        setSystem(sys);
        const linked = (featData.features || []).filter(
          (f: any) => f.ai_system_id === systemId,
        );
        setFeatures(linked);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [systemId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!system) return <ErrorState message="System not found" />;

  const breadcrumbs = [
    { label: 'AI Systems', href: '/systems' },
    { label: system.name }
  ];

  return (
    <PageShell
      title={system.name}
      subtitle={`Global Resource Identifier: ${system.id}`}
      breadcrumbs={breadcrumbs}
      actions={
        <Link 
          href="/systems"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-zinc-950 text-zinc-400 hover:text-white transition-all text-xs font-bold uppercase tracking-widest"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          BACK TO INVENTORY
        </Link>
      }
    >
      <div className="space-y-8 animate-slide-up">
        {/* Core Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Deployment Lifecycle" variant="stat">
            <StatusBadge value={system.deployment_status} className="scale-110" />
          </Card>
          <Card title="Registry Governance" variant="stat">
            <StatusBadge value={system.registration_status} className="scale-110" />
          </Card>
          <Card title="Last Reconciliation" variant="stat">
            <div className="flex items-center gap-2 text-zinc-300">
              <Activity className="h-4 w-4 text-indigo-500" />
              <span className="text-xl font-bold">
                {new Date(system.updated_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
              </span>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Details Sidebar */}
          <div className="lg:col-span-4 space-y-6">
            <Card title="Operational Details">
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                    <Info className="h-3 w-3" />
                    Functional Description
                  </label>
                  <p className="text-sm text-zinc-400 leading-relaxed font-medium">
                    {system.description || 'No system description provided in registry.'}
                  </p>
                </div>
                
                <div className="space-y-2 pt-4 border-t border-border">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                    <Calendar className="h-3 w-3" />
                    Audit Information
                  </label>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-tight">Provisioned</span>
                      <span className="text-[10px] text-zinc-400 font-mono font-bold">{new Date(system.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-tight">Tenant ID</span>
                      <span className="text-[10px] text-zinc-400 font-mono font-bold truncate ml-4">{system.tenant_id}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Linked Components */}
          <div className="lg:col-span-8 space-y-6">
            <Card 
              title={`Associated Features (${features.length})`}
              subtitle="Governed features architecturally linked to this AI system."
            >
              {features.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-zinc-900 rounded-xl">
                  <Layers className="h-8 w-8 text-zinc-800 mb-2" />
                  <p className="text-xs text-zinc-600 font-bold uppercase tracking-widest">No active feature linkage</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {features.map((f: any) => (
                    <Link
                      key={f.id}
                      href={`/features/${f.feature_id}`}
                      className="flex items-center justify-between p-4 rounded-xl border border-border bg-zinc-950/40 hover:bg-zinc-900/60 hover:border-zinc-700 transition-all group"
                    >
                      <div className="flex items-center gap-4">
                        <div className="bg-zinc-900 p-2 rounded-lg group-hover:bg-indigo-500/10 transition-colors">
                          <Layers className={`h-4 w-4 transition-colors ${f.risk_level_current?.toLowerCase() === 'high' ? 'text-red-500' : 'text-zinc-500 group-hover:text-indigo-400'}`} />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-zinc-200">{f.name}</p>
                          <p className="text-[10px] text-zinc-600 font-mono font-bold mt-0.5">{f.feature_id}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge value={f.compliance_status} />
                        <div className="w-px h-4 bg-border" />
                        <StatusBadge value={f.risk_level_current} />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
