'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import PageShell from '@/components/page-shell';
import Card from '@/components/card';
import StatusBadge from '@/components/status-badge';
import Loading from '@/components/loading';
import { ShieldCheck, Plus, ArrowRight, ClipboardList, AlertCircle } from 'lucide-react';

export default function FriaPage() {
  const [frias, setFrias] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listFrias()
      .then(setFrias)
      .catch(err => {
        if (err instanceof ApiError && err.status === 403) {
          setError("You do not have entitlement for FRIA management. Please upgrade your plan.");
        } else {
          setError("Failed to load FRIA records.");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <PageShell title="Fundamental Rights Impact Assessments" subtitle="Manage and review mandated FRIAs for high-risk AI systems.">
        <Loading />
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell title="Fundamental Rights Impact Assessments" subtitle="Manage and review mandated FRIAs for high-risk AI systems.">
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="p-3 rounded-full bg-red-500/10 mb-4">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Access Restricted</h3>
            <p className="text-zinc-400 max-w-md">{error}</p>
            <Link href="/billing" className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-colors">
              View Plans
            </Link>
          </div>
        </Card>
      </PageShell>
    );
  }

  return (
    <PageShell 
      title="Fundamental Rights Impact Assessments" 
      subtitle="Manage and review mandated FRIAs for high-risk AI systems."
      actions={
        <Link href="/intake" className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-600/20">
          <Plus className="h-4 w-4" />
          New Assessment
        </Link>
      }
    >
      <div className="space-y-6">
        {frias.length === 0 ? (
          <Card>
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="p-4 rounded-full bg-zinc-900 mb-6">
                <ClipboardList className="h-8 w-8 text-zinc-600" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">No FRIAs found</h3>
              <p className="text-zinc-500 max-w-sm mx-auto leading-relaxed">
                Fundamental Rights Impact Assessments are required for high-risk AI systems under Article 27 of the EU AI Act.
              </p>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {frias.map((fria) => (
              <Link key={fria.id} href={`/fria/${fria.id}`}>
                <Card className="hover:border-zinc-700 transition-all group">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-2.5 rounded-lg bg-zinc-900 text-zinc-400 group-hover:text-indigo-400 transition-colors border border-zinc-800">
                        <ShieldCheck className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-white tracking-tight">{fria.id}</h4>
                          <StatusBadge value={fria.status} />
                        </div>
                        <p className="text-xs text-zinc-500 mt-1 font-medium">System: {fria.ai_system_id}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right hidden sm:block">
                        <p className="text-[10px] uppercase tracking-wider font-bold text-zinc-600">Last Updated</p>
                        <p className="text-xs text-zinc-400 font-medium">{new Date(fria.updated_at).toLocaleDateString()}</p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-zinc-700 group-hover:text-zinc-400 transition-colors" />
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
