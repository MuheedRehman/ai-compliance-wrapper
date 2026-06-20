import Link from 'next/link';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import EmptyState from '@/components/empty-state';
import { backendServiceFetch } from '@/lib/backend-service';
import { Cpu } from 'lucide-react';
import CreateSystemPanel from './_create-system-panel';

interface AiSystem {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  deployment_status: string;
  registration_status: string;
  owner_email?: string | null;
  review_status?: string;
  next_review_at?: string | null;
  created_at: string;
  updated_at: string;
}

async function fetchSystems(): Promise<AiSystem[]> {
  try {
    const res = await backendServiceFetch('/v1/ai-systems');
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function SystemsPage() {
  const systems = await fetchSystems();

  const deployedCount = systems.filter(s => s.deployment_status.toLowerCase() === 'deployed').length;
  const registeredCount = systems.filter(s => s.registration_status.toLowerCase() === 'registered').length;

  return (
    <PageShell
      title="AI Systems"
      subtitle="Comprehensive inventory of AI systems within your governance scope."
      breadcrumbs={[{ label: 'AI Systems' }]}
    >
      <div className="space-y-6">
        <CreateSystemPanel />

        {systems.length === 0 ? (
          <EmptyState
            title="No AI systems identified"
            message="Begin by registering your first AI system to initiate the compliance workflow."
            icon={Cpu}
          />
        ) : (
          <>
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

            <Card className="!p-0 overflow-hidden border-border bg-zinc-950">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th>System Identity</th>
                      <th>Deployment</th>
                      <th>Registration</th>
                      <th>Owner</th>
                      <th>Review</th>
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
                        <td className="text-[10px] text-zinc-500 font-bold">
                          {s.owner_email || 'Unassigned'}
                        </td>
                        <td>
                          <div className="flex flex-col gap-1">
                            <StatusBadge value={s.review_status || 'not_started'} />
                            <span className="text-[10px] text-zinc-600">
                              {s.next_review_at
                                ? new Date(s.next_review_at).toLocaleDateString(undefined, { dateStyle: 'medium' })
                                : 'No date'}
                            </span>
                          </div>
                        </td>
                        <td className="text-[10px] text-zinc-500 font-bold uppercase tracking-tighter">
                          {new Date(s.created_at).toLocaleDateString(undefined, { dateStyle: 'medium' })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </PageShell>
  );
}
