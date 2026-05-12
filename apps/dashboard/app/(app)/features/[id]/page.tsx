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
import { 
  History, 
  Settings2, 
  Info, 
  ShieldCheck, 
  AlertTriangle, 
  ChevronLeft,
  Mail,
  Users,
  Briefcase,
  Zap
} from 'lucide-react';

export default function FeatureDetailPage() {
  const params = useParams();
  const featureId = params.id as string;

  const [feature, setFeature] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getFeature(featureId),
      api.getFeatureVersions(featureId).catch(() => ({ versions: [] })),
    ])
      .then(([feat, verData]) => {
        setFeature(feat);
        setVersions(verData.versions || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [featureId]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!feature) return <ErrorState message="Feature not found" />;

  const breadcrumbs = [
    { label: 'Features', href: '/features' },
    { label: feature.name }
  ];

  return (
    <PageShell 
      title={feature.name} 
      subtitle={`Unique Identifier: ${feature.feature_id}`}
      breadcrumbs={breadcrumbs}
      actions={
        <Link 
          href="/features"
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-zinc-950 text-zinc-400 hover:text-white transition-all text-xs font-bold uppercase tracking-widest"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          BACK TO FEATURES
        </Link>
      }
    >
      <div className="space-y-8 animate-slide-up">
        {/* Top Status Bar */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card title="Risk Classification" variant="stat">
            <StatusBadge value={feature.risk_level_current} className="scale-110" />
          </Card>
          <Card title="Compliance Status" variant="stat">
            <StatusBadge value={feature.compliance_status} className="scale-110" />
          </Card>
          <Card title="FRIA Required" variant="stat">
            <div className="flex items-center gap-2">
              {feature.fria_likely_required ? (
                <>
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  <span className="text-xl font-bold text-amber-500">MANDATORY</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4 text-emerald-500" />
                  <span className="text-xl font-bold text-emerald-500">OPTIONAL</span>
                </>
              )}
            </div>
          </Card>
          <Card title="Policy version" variant="stat">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-indigo-500" />
              <span className="text-xl font-bold text-zinc-300">
                {feature.policy_bundle_version || 'STABLE'}
              </span>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Metadata Grid */}
          <div className="lg:col-span-4 space-y-6">
            <Card title="Management Data">
              <div className="space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                    <Info className="h-3 w-3" />
                    Feature Overview
                  </label>
                  <p className="text-sm text-zinc-400 leading-relaxed font-medium">
                    {feature.description || 'No description provided in registry.'}
                  </p>
                </div>
                
                <div className="space-y-4 pt-6 border-t border-border">
                  {[
                    { icon: Mail, label: 'Owner Contact', value: feature.owner_email },
                    { icon: Users, label: 'Accountable Team', value: feature.team },
                    { icon: Briefcase, label: 'Primary Use Case', value: feature.use_case },
                  ].map((item, idx) => (
                    <div key={idx} className="flex items-start gap-4">
                      <div className="bg-zinc-900 p-1.5 rounded border border-zinc-800">
                        <item.icon className="h-3.5 w-3.5 text-zinc-500" />
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-tight">{item.label}</p>
                        <p className="text-xs font-semibold text-zinc-400">{item.value || '—'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>

            <Card title="Provider Configuration">
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-zinc-500 font-bold uppercase tracking-tight">Approved Providers</span>
                    <div className="flex gap-1">
                      {(feature.approved_providers || []).map((p: string) => (
                        <span key={p} className="bg-zinc-900 px-2 py-0.5 rounded text-[10px] font-bold text-zinc-400 uppercase tracking-widest border border-zinc-800">{p}</span>
                      ))}
                      {(!feature.approved_providers || feature.approved_providers.length === 0) && <span className="text-zinc-600">—</span>}
                    </div>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-zinc-500 font-bold uppercase tracking-tight">Model Registry</span>
                    <div className="flex flex-wrap justify-end gap-1">
                      {(feature.approved_models || []).map((m: string) => (
                        <span key={m} className="bg-zinc-900 px-2 py-0.5 rounded text-[10px] font-bold text-zinc-400 font-mono border border-zinc-800">{m}</span>
                      ))}
                      {(!feature.approved_models || feature.approved_models.length === 0) && <span className="text-zinc-600">—</span>}
                    </div>
                  </div>
                </div>
                <div className="pt-4 border-t border-border">
                   <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-1.5">Compliance Fingerprint</p>
                   <code className="block p-2 rounded bg-black text-[10px] text-emerald-500/70 font-mono break-all border border-emerald-500/10">
                     {feature.current_fingerprint || 'PENDING_HASH_CALCULATION'}
                   </code>
                </div>
              </div>
            </Card>
          </div>

          {/* Audit History (Versions) */}
          <div className="lg:col-span-8 space-y-6">
            <Card 
              title={`Governance Audit History (${versions.length})`}
              subtitle="Immutable record of feature revisions and their compliance impact."
            >
              {versions.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 border-2 border-dashed border-zinc-900 rounded-xl">
                  <History className="h-10 w-10 text-zinc-800 mb-2" />
                  <p className="text-xs text-zinc-600 font-bold uppercase tracking-widest">No audit versions found</p>
                </div>
              ) : (
                <div className="overflow-hidden rounded-xl border border-border">
                  <table className="w-full">
                    <thead className="bg-zinc-900/40">
                      <tr>
                        <th>Version ID</th>
                        <th>Governance Status</th>
                        <th>Compute Configuration</th>
                        <th>Audit Stamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {versions.map((v: any) => (
                        <tr key={v.feature_version_id} className="hover:bg-zinc-900/20 transition-colors">
                          <td className="text-xs font-bold text-zinc-300 font-mono">v{v.version}</td>
                          <td><StatusBadge value={v.status} /></td>
                          <td>
                            <div className="flex flex-col">
                              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-tight">{v.provider}</span>
                              <span className="text-[10px] text-zinc-600 font-mono mt-0.5 italic">{v.model}</span>
                            </div>
                          </td>
                          <td className="text-[10px] text-zinc-500 font-bold uppercase tracking-tighter">
                            {new Date(v.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
