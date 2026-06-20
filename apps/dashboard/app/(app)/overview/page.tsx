import Link from 'next/link';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import { backendServiceFetch } from '@/lib/backend-service';
import {
  Cpu,
  Layers,
  ClipboardCheck,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  Activity,
  ListChecks,
} from 'lucide-react';

async function fetchOverviewData() {
  const [systemsRes, featuresRes, reviewsRes, logsRes, scorecardRes] = await Promise.allSettled([
    backendServiceFetch('/v1/ai-systems').then(r => r.ok ? r.json() as Promise<any[]> : []),
    backendServiceFetch('/v1/features').then(r => r.ok ? r.json() as Promise<{ features: any[] }> : { features: [] }),
    backendServiceFetch('/v1/review-tasks').then(r => r.ok ? r.json() as Promise<{ review_tasks: any[] }> : { review_tasks: [] }),
    backendServiceFetch('/v1/logs').then(r => r.ok ? r.json() as Promise<{ logs: any[] }> : { logs: [] }),
    backendServiceFetch('/v1/compliance/scorecard').then(r => r.ok ? r.json() : null),
  ]);

  return {
    systems: (systemsRes.status === 'fulfilled' ? systemsRes.value : null) as any[] || [],
    features: ((featuresRes.status === 'fulfilled' ? featuresRes.value : null) as any)?.features || [],
    reviews: ((reviewsRes.status === 'fulfilled' ? reviewsRes.value : null) as any)?.review_tasks || [],
    logs: ((logsRes.status === 'fulfilled' ? logsRes.value : null) as any)?.logs || [],
    scorecard: scorecardRes.status === 'fulfilled' ? scorecardRes.value : null,
  };
}

export default async function OverviewPage() {
  const data = await fetchOverviewData();

  const totalSystems = data.systems.length;
  const deployedSystems = data.systems.filter((s: any) => s.deployment_status?.toLowerCase() === 'deployed').length;
  const totalFeatures = data.features.length;
  const highRiskFeatures = data.features.filter((f: any) => f.risk_level_current?.toLowerCase() === 'high').length;
  const openReviews = data.reviews.filter((r: any) => r.status?.toLowerCase() === 'open').length;
  const totalLogs = data.logs.length;
  const blockedRequests = data.logs.filter((l: any) => l.decision?.toLowerCase() === 'block').length;
  const readinessScore = data.scorecard?.readiness_score ?? 0;

  return (
    <PageShell
      title="Governance Overview"
      subtitle="Real-time operational summary of your EU AI Act compliance posture."
    >
      <div className="space-y-8 animate-fade-in">
        {/* KPI Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
          <Card title="AI Systems" variant="stat">
            <div className="flex items-end gap-3">
              <span className="text-3xl font-bold tabular-nums">{totalSystems}</span>
              <span className="text-xs font-medium text-zinc-500 mb-1">{deployedSystems} deployed</span>
            </div>
          </Card>
          <Card title="Features" variant="stat">
            <div className="flex items-end gap-3">
              <span className="text-3xl font-bold tabular-nums">{totalFeatures}</span>
              {highRiskFeatures > 0 && (
                <span className="flex items-center gap-1 text-xs font-bold text-red-400 mb-1">
                  <AlertTriangle className="h-3 w-3" />
                  {highRiskFeatures} high risk
                </span>
              )}
            </div>
          </Card>
          <Card title="Open Reviews" variant="stat">
            <div className="flex items-end gap-3">
              <span className={`text-3xl font-bold tabular-nums ${openReviews > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {openReviews}
              </span>
              <span className="text-xs font-medium text-zinc-500 mb-1">
                {openReviews === 0 ? 'all clear' : 'pending'}
              </span>
            </div>
          </Card>
          <Card title="Evidence Events" variant="stat">
            <div className="flex items-end gap-3">
              <span className="text-3xl font-bold tabular-nums">{totalLogs}</span>
              {blockedRequests > 0 && (
                <span className="flex items-center gap-1 text-xs font-bold text-red-400 mb-1">
                  {blockedRequests} blocked
                </span>
              )}
            </div>
          </Card>
          <Card title="Readiness" variant="stat">
            <div className="flex items-end gap-3">
              <span className={`text-3xl font-bold tabular-nums ${readinessScore >= 80 ? 'text-emerald-400' : readinessScore >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                {readinessScore}%
              </span>
              <span className="flex items-center gap-1 text-xs font-medium text-zinc-500 mb-1">
                <ListChecks className="h-3 w-3" />
                controls
              </span>
            </div>
          </Card>
        </div>

        {/* Quick-Access Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Systems */}
          <Card title="AI Systems" subtitle="Most recently registered systems.">
            {data.systems.length === 0 ? (
              <p className="text-sm text-zinc-500 py-4">No systems registered yet.</p>
            ) : (
              <div className="space-y-1">
                {data.systems.slice(0, 5).map((s: any) => (
                  <Link
                    key={s.id}
                    href={`/systems/${s.id}`}
                    className="flex items-center justify-between py-2.5 px-3 -mx-3 rounded-lg hover:bg-secondary/40 transition-colors group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Cpu className="h-4 w-4 text-zinc-500 shrink-0" />
                      <span className="text-sm font-medium text-zinc-200 truncate">{s.name}</span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <StatusBadge value={s.deployment_status} />
                      <ArrowRight className="h-3 w-3 text-zinc-700 group-hover:text-zinc-400 transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
            <Link href="/systems" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
              View all systems <ArrowRight className="h-3 w-3" />
            </Link>
          </Card>

          {/* Recent Features */}
          <Card title="Feature Registry" subtitle="Recently cataloged AI features.">
            {data.features.length === 0 ? (
              <p className="text-sm text-zinc-500 py-4">No features cataloged yet.</p>
            ) : (
              <div className="space-y-1">
                {data.features.slice(0, 5).map((f: any) => (
                  <Link
                    key={f.id}
                    href={`/features/${f.feature_id}`}
                    className="flex items-center justify-between py-2.5 px-3 -mx-3 rounded-lg hover:bg-secondary/40 transition-colors group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Layers className="h-4 w-4 text-zinc-500 shrink-0" />
                      <div className="min-w-0">
                        <span className="text-sm font-medium text-zinc-200 truncate block">{f.name}</span>
                        <span className="text-[10px] font-mono text-zinc-600">{f.feature_id}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <StatusBadge value={f.risk_level_current} />
                      <ArrowRight className="h-3 w-3 text-zinc-700 group-hover:text-zinc-400 transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
            <Link href="/features" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
              View all features <ArrowRight className="h-3 w-3" />
            </Link>
          </Card>

          {/* Open Reviews */}
          <Card title="Pending Reviews" subtitle="Active governance reviews requiring attention.">
            {data.reviews.filter((r: any) => r.status?.toLowerCase() === 'open').length === 0 ? (
              <div className="flex items-center gap-3 py-6">
                <div className="p-2 rounded-full bg-emerald-500/10">
                  <ShieldCheck className="h-5 w-5 text-emerald-500" />
                </div>
                <div>
                  <p className="text-sm font-medium text-zinc-300">No pending reviews</p>
                  <p className="text-xs text-zinc-500">All governance thresholds within tolerance.</p>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {data.reviews.filter((r: any) => r.status?.toLowerCase() === 'open').slice(0, 4).map((r: any) => (
                  <div key={r.review_task_id} className="flex items-center justify-between py-2.5 px-3 -mx-3 rounded-lg hover:bg-secondary/40 transition-colors">
                    <div className="flex items-center gap-3 min-w-0">
                      <ClipboardCheck className="h-4 w-4 text-amber-500 shrink-0" />
                      <div className="min-w-0">
                        <span className="text-sm font-medium text-zinc-200 truncate block">{r.review_type}</span>
                        <span className="text-[10px] text-zinc-500">{r.trigger_reason?.slice(0, 60)}</span>
                      </div>
                    </div>
                    <StatusBadge value={r.severity} />
                  </div>
                ))}
              </div>
            )}
            <Link href="/reviews" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
              View all reviews <ArrowRight className="h-3 w-3" />
            </Link>
          </Card>

          {/* Recent Evidence */}
          <Card title="Audit Trail" subtitle="Latest governed request decisions.">
            {data.logs.length === 0 ? (
              <p className="text-sm text-zinc-500 py-4">No evidence events recorded yet.</p>
            ) : (
              <div className="space-y-1">
                {data.logs.slice(0, 4).map((l: any) => (
                  <div key={l.event_id} className="flex items-center justify-between py-2.5 px-3 -mx-3 rounded-lg hover:bg-secondary/40 transition-colors">
                    <div className="flex items-center gap-3 min-w-0">
                      <Activity className="h-4 w-4 text-zinc-500 shrink-0" />
                      <div className="min-w-0">
                        <span className="text-sm font-medium text-zinc-300 truncate block">{l.event_type}</span>
                        <span className="text-[10px] font-mono text-zinc-600">{l.feature_id || 'system'}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <StatusBadge value={l.decision} />
                      <StatusBadge value={l.risk_level} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Link href="/evidence" className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">
              View full audit trail <ArrowRight className="h-3 w-3" />
            </Link>
          </Card>
        </div>
      </div>
    </PageShell>
  );
}
