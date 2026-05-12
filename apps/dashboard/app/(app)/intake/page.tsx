'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import EmptyState from '@/components/empty-state';
import ErrorState from '@/components/error-state';
import IntakeForm from '@/components/forms/intake-form';
import { Plus, ClipboardList, ArrowRight, ShieldCheck } from 'lucide-react';

export default function IntakePage() {
  const [intakes, setIntakes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const loadIntakes = async () => {
    try {
      const data = await api.listIntakes();
      setIntakes(data);
    } catch (err: any) {
      setError(err.body?.detail || 'Failed to load intake assessments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIntakes();
  }, []);

  if (showForm) {
    return (
      <PageShell 
        title="New Intake Assessment" 
        subtitle="Step-by-step classification wizard for AI systems."
        actions={
          <button 
            onClick={() => setShowForm(false)}
            className="text-[11px] font-bold uppercase tracking-widest text-zinc-500 hover:text-white transition-colors"
          >
            Cancel
          </button>
        }
      >
        <IntakeForm />
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Intake & Classification"
      subtitle="Assess and categorize AI systems under the EU AI Act."
      actions={
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all shadow-lg shadow-indigo-600/20"
        >
          <Plus className="h-3.5 w-3.5" />
          Start Assessment
        </button>
      }
    >
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorState message={error} onRetry={loadIntakes} />
      ) : intakes.length === 0 ? (
        <EmptyState 
          title="No assessments found" 
          message="Complete your first intake assessment to classify an AI system and view its obligation path."
          icon={ClipboardList}
          action={
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white text-[11px] font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all"
            >
              Start First Assessment
            </button>
          }
        />
      ) : (
        <div className="space-y-6 animate-fade-in">
          {/* Summary KPI for Intake */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card title="Total Assessments" variant="stat">
              <span className="text-3xl font-bold tabular-nums">{intakes.length}</span>
            </Card>
            <Card title="High-Risk Systems" variant="stat">
              <span className="text-3xl font-bold tabular-nums text-amber-400">
                {intakes.filter(i => i.system_classification === 'High-Risk AI System').length}
              </span>
            </Card>
            <Card title="Compliance Paths" variant="stat">
              <span className="text-3xl font-bold tabular-nums text-indigo-400">
                {Array.from(new Set(intakes.map((i: any) => i.obligation_path))).length}
              </span>
            </Card>
          </div>

          <Card title="Assessment Records">
            <div className="overflow-x-auto -mx-5 px-5">
              <table>
                <thead>
                  <tr>
                    <th>Assessment Title</th>
                    <th>Actor Role</th>
                    <th>Classification</th>
                    <th>Obligation Path</th>
                    <th>Created</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {intakes.map((intake) => (
                    <tr key={intake.id} className="group">
                      <td>
                        <div className="flex flex-col">
                          <span className="font-bold text-zinc-200">{intake.title}</span>
                          <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-tighter">{intake.id}</span>
                        </div>
                      </td>
                      <td>
                        <StatusBadge value={intake.actor_role} />
                      </td>
                      <td>
                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded border ${
                          intake.system_classification.includes('High') ? 'bg-amber-500/10 border-amber-500/30 text-amber-500' :
                          intake.system_classification.includes('Prohibited') ? 'bg-red-500/10 border-red-500/30 text-red-500' :
                          'bg-zinc-800 border-zinc-700 text-zinc-400'
                        }`}>
                          {intake.system_classification}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1.5">
                          <ShieldCheck className="h-3 w-3 text-zinc-600" />
                          <span className="text-[11px] font-mono font-bold text-zinc-400">{intake.obligation_path}</span>
                        </div>
                      </td>
                      <td className="text-zinc-500 text-[11px]">
                        {new Date(intake.created_at).toLocaleDateString()}
                      </td>
                      <td className="text-right">
                        <Link 
                          href={`/intake/${intake.id}`}
                          className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-white transition-all inline-flex"
                        >
                          <ArrowRight className="h-4 w-4" />
                        </Link>
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
